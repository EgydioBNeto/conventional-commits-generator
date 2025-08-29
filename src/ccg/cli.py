"""Command-line interface for Conventional Commits Generator."""

import argparse
import sys
import traceback
from typing import List, Optional, Tuple

from ccg import __version__
from ccg.core import confirm_commit, confirm_push, generate_commit_message, validate_commit_message
from ccg.git import (
    branch_exists_on_remote,
    check_and_install_pre_commit,
    check_has_changes,
    check_is_git_repo,
    check_remote_access,
    create_tag,
    delete_commit,
    discard_local_changes,
    edit_commit_message,
    get_commit_by_hash,
    get_current_branch,
    get_recent_commits,
    git_add,
    git_commit,
    git_push,
    pull_from_remote,
    push_tag,
)
from ccg.utils import (
    INPUT_LIMITS,
    RESET,
    YELLOW,
    confirm_user_action,
    print_error,
    print_info,
    print_logo,
    print_process,
    print_section,
    print_success,
    print_warning,
    read_input,
)


class CustomHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=50, width=100)

    def _format_usage(self, usage, actions, groups, prefix):
        print_logo()
        return super()._format_usage(usage, actions, groups, prefix)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ccg",
        description="Conventional Commits Generator - Create standardized git commits",
        formatter_class=CustomHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--push", action="store_true", help="Just run git push without creating a new commit"
    )
    parser.add_argument(
        "--commit", action="store_true", help="Generate commit message without actually committing"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Discard all local changes and pull latest from remote"
    )
    parser.add_argument(
        "--tag", action="store_true", help="Create a new Git tag and push it to remote"
    )
    parser.add_argument("--edit", action="store_true", help="Edit an existing commit message")
    parser.add_argument("--delete", action="store_true", help="Delete an existing commit")
    parser.add_argument("--path", nargs="+", help="Specify path(s) to stage instead of all changes")
    return parser.parse_args(args)


def confirm_create_branch() -> bool:
    print_section("Create Remote Branch")
    print_info("This branch doesn't exist on the remote repository yet")
    return confirm_user_action(
        f"{YELLOW}Create and push this branch to remote? (y/n){RESET}",
        success_message="Branch will be created on remote",
        cancel_message="Not creating branch on remote",
    )


def confirm_reset() -> bool:
    print_warning("This will discard ALL local changes and pull the latest from remote.")
    print_warning("All uncommitted work will be lost!")
    return confirm_user_action(
        f"{YELLOW}Are you sure you want to proceed? (y/n){RESET}",
        success_message=None,
        cancel_message="Reset operation cancelled",
    )


def get_commit_count_input() -> Optional[int]:
    while True:
        count_input = read_input(
            f"{YELLOW}How many recent commits to display? (Enter or 0 for all){RESET}", max_length=6
        )
        if not count_input or count_input == "0":
            return None
        if count_input.isdigit() and int(count_input) > 0:
            return int(count_input)
        print_error("Please enter a valid positive number, 0, or press Enter for all commits.")


def handle_commit_operation(operation_type: str) -> int:
    print_section(f"{operation_type.capitalize()} Commit")

    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    count = get_commit_count_input()
    commits = get_recent_commits(count)
    if not commits:
        print_error("Failed to retrieve recent commits or no commits found.")
        return 1

    print_section("Recent Commits")
    if count is None:
        print_info(f"Showing all {len(commits)} commits:")
    else:
        print_info(f"Showing last {len(commits)} commits:")
    print()

    for i, commit in enumerate(commits, start=1):
        short_hash, subject, author, date = commit
        print(f"{i}. [{short_hash}] {subject} - {author} ({date})")
    print()

    print_section("Commit Selection")
    while True:
        selection = read_input(
            f"{YELLOW}Enter commit number or hash to {operation_type} (or 'q' to quit){RESET}",
            max_length=40,
        )

        if selection.lower() in ("q", "quit", "exit"):
            print_info(f"{operation_type.capitalize()} operation cancelled")
            return 0

        if selection.isdigit() and 1 <= int(selection) <= len(commits):
            idx = int(selection) - 1
            selected_hash = commits[idx][0]
            break

        matching_commits = [c for c in commits if c[0].startswith(selection)]
        if len(matching_commits) == 1:
            selected_hash = matching_commits[0][0]
            break
        elif len(matching_commits) > 1:
            print_error("Multiple commits match this hash. Please be more specific.")
            continue

        print_error("Invalid selection. Please try again.")

    if operation_type == "edit":
        return edit_specific_commit(selected_hash)
    else:
        return delete_specific_commit(selected_hash)


def handle_edit() -> int:
    return handle_commit_operation("edit")


def handle_delete() -> int:
    return handle_commit_operation("delete")


def display_commit_details(commit_details: Tuple[str, str, str, str, str, str]) -> None:
    hash_full, hash_short, subject, body, author, date = commit_details
    print(f"Hash: {hash_full}")
    print(f"Author: {author}")
    print(f"Date: {date}")
    print(f"Subject: {subject}")
    if body:
        print(f"Body:\n{body}")
    print()


def handle_commit_edit_input(
    subject: str, original_body: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    print_info("Edit the commit message below. Leave empty to cancel.")
    print_info(
        "Message must follow conventional commit format: <type>[optional scope][optional !]: <description>"
    )

    new_message = read_input(
        f"{YELLOW}New commit message{RESET}", history_type="message", default_text=subject
    )

    if not new_message:
        print_info("Edit cancelled. Commit message remains unchanged.")
        return None, None

    is_valid, error_message = validate_commit_message(new_message)
    if not is_valid:
        print_error(f"Invalid commit message format: {error_message}")
        print_info("Examples of valid formats:")
        print_info("  feat: add new feature")
        print_info("  fix(auth): resolve login issue")

        retry = confirm_user_action(
            f"{YELLOW}Would you like to try again? (y/n){RESET}",
            success_message=None,
            cancel_message="Edit cancelled. Commit message remains unchanged.",
        )

        if retry:
            return handle_commit_edit_input(subject, original_body)
        return None, None

    print_info("Edit the commit body below. Leave empty to remove body, or keep unchanged.")
    new_body = read_input(
        f"{YELLOW}New commit body (optional){RESET}",
        history_type="body",
        default_text=original_body or "",
    )

    if not new_body:
        new_body = None

    return new_message, new_body


def confirm_commit_edit(
    original_subject: str, original_body: Optional[str], new_message: str, new_body: Optional[str]
) -> bool:
    print_section("Original")

    original_full = original_subject
    if original_body:
        original_full += f"\n\n{original_body}"

    from ccg.core import convert_emoji_codes_to_real, get_visual_width
    from ccg.utils import BOLD, RESET, TERM_WIDTH, WHITE

    display_header = convert_emoji_codes_to_real(original_subject)
    lines = [display_header]
    if original_body:
        lines.append("")
        lines.extend(original_body.split("\n"))

    max_visual_width = max(get_visual_width(line) for line in lines)
    left_padding = 4
    right_padding = 4
    content_width = max_visual_width
    inner_width = content_width + left_padding + right_padding
    box_width = inner_width + 2
    min_width = 50
    max_width = min(TERM_WIDTH - 4, 100)
    box_width = max(min_width, min(box_width, max_width))
    final_inner_width = box_width - 2
    final_content_width = final_inner_width - left_padding - right_padding

    print(f"{WHITE}┌{'─' * (box_width - 2)}┐{RESET}")
    print(f"{WHITE}│{' ' * (box_width - 2)}│{RESET}")

    for line in lines:
        if not line:
            print(f"{WHITE}│{' ' * (box_width - 2)}│{RESET}")
            continue

        line_visual_width = get_visual_width(line)
        if line_visual_width > final_content_width:
            truncated = ""
            for char in line:
                test_line = truncated + char + "..."
                if get_visual_width(test_line) <= final_content_width:
                    truncated += char
                else:
                    break
            display_line = truncated + "..."
            display_visual_width = get_visual_width(display_line)
        else:
            display_line = line
            display_visual_width = line_visual_width

        remaining_space = final_content_width - display_visual_width
        formatted_line = (
            f"{WHITE}│"
            f"{' ' * left_padding}"
            f"{BOLD}{display_line}{RESET}"
            f"{WHITE}{' ' * remaining_space}"
            f"{' ' * right_padding}"
            f"│{RESET}"
        )
        print(formatted_line)

    print(f"{WHITE}│{' ' * (box_width - 2)}│{RESET}")
    print(f"{WHITE}└{'─' * (box_width - 2)}┘{RESET}")

    return confirm_commit(new_message, new_body)


def handle_push_after_edit(branch_name: str) -> int:
    if not branch_exists_on_remote(branch_name):
        if confirm_create_branch():
            if not git_push(set_upstream=True):
                print_error("Failed to push and create branch on remote")
                return 1
        else:
            print_info("Changes remain local only")
            return 0
    else:
        print_warning("Force push is required to update the commit on the remote.")
        print_warning("This can potentially overwrite other changes. Use with caution!")

        force_push = confirm_user_action(
            f"{YELLOW}Force push changes? (y/n){RESET}",
            success_message=None,
            cancel_message="Changes remain local only",
        )

        if force_push:
            if not git_push(force=True):
                print_error("Failed to force push changes to remote")
                return 1

    return 0


def edit_specific_commit(commit_hash: str) -> int:
    print_section("Commit Details")
    commit_details = get_commit_by_hash(commit_hash)
    if not commit_details:
        print_error(f"Commit with hash '{commit_hash}' not found.")
        return 1

    display_commit_details(commit_details)
    print_section("Edit Message")

    hash_full, hash_short, subject, body, author, date = commit_details
    new_message, new_body = handle_commit_edit_input(subject, body)

    if new_message is None:
        return 0

    if not confirm_commit_edit(subject, body, new_message, new_body):
        return 0

    print_section("Updating Commit")
    if not edit_commit_message(hash_full, new_message, new_body):
        print_error("Failed to edit commit.")
        return 1

    if confirm_push():
        branch_name = get_current_branch()
        if not branch_name:
            print_error("Failed to determine current branch name")
            return 1
        return handle_push_after_edit(branch_name)

    return 0


def delete_specific_commit(commit_hash: str) -> int:
    print_section("Commit Details")
    commit_details = get_commit_by_hash(commit_hash)
    if not commit_details:
        print_error(f"Commit with hash '{commit_hash}' not found.")
        return 1

    display_commit_details(commit_details)
    print_section("Delete Confirmation")
    hash_full, hash_short, subject, body, author, date = commit_details

    print_warning("This will permanently delete the commit from history!")
    print_warning("This action cannot be undone and may affect other commits.")

    confirm_delete = confirm_user_action(
        f"{YELLOW}Are you sure you want to delete this commit? (y/n){RESET}",
        success_message=None,
        cancel_message="Delete cancelled. Commit remains unchanged.",
    )

    if not confirm_delete:
        return 0

    print_section("Deleting Commit")
    if not delete_commit(hash_full):
        print_error("Failed to delete commit.")
        return 1

    if confirm_push():
        branch_name = get_current_branch()
        if not branch_name:
            print_error("Failed to determine current branch name")
            return 1
        return handle_push_after_edit(branch_name)

    return 0


def handle_tag() -> int:
    print_section("Git Tag Creation")

    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    if not check_remote_access():
        return 1

    tag_name = read_input(
        f"{YELLOW}Enter the tag name (e.g., v1.0.0){RESET}", max_length=INPUT_LIMITS["tag"]
    )

    if not tag_name:
        print_error("Tag name cannot be empty. Aborting.")
        return 1

    annotated = confirm_user_action(
        f"{YELLOW}Create an annotated tag with a message? (y/n){RESET}",
        success_message=None,
        cancel_message=None,
    )

    tag_message = None
    if annotated:
        tag_message = read_input(
            f"{YELLOW}Enter the tag message{RESET}",
            history_type="tag_message",
            max_length=INPUT_LIMITS["tag_message"],
        )
        if not tag_message:
            print_error("Tag message cannot be empty for annotated tags. Aborting.")
            return 1

    if not create_tag(tag_name, tag_message):
        print_error("Failed to create tag. Aborting.")
        return 1

    if not push_tag(tag_name):
        print_error("Failed to push tag to remote.")
        return 1
    return 0


def handle_reset() -> int:
    print_section("Reset Local Changes")

    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    if not check_remote_access():
        return 1

    if not check_has_changes():
        pull_anyway = confirm_user_action(
            f"{YELLOW}No changes to discard. Do you still want to pull latest changes? (y/n){RESET}",
            success_message=None,
            cancel_message="Reset operation cancelled",
        )
        if not pull_anyway:
            return 0
    else:
        if not confirm_reset():
            return 0
        if not discard_local_changes():
            print_error("Failed to discard local changes")
            return 1

    if not pull_from_remote():
        print_error("Failed to pull latest changes from remote")
        return 1

    print_success("Reset complete! Working directory is now in sync with remote")
    return 0


def handle_push_only() -> int:
    print_section("Push Only Mode")

    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    if not check_remote_access():
        return 1

    branch_name = get_current_branch()
    if not branch_name:
        print_error("Failed to determine current branch name")
        return 1

    if not branch_exists_on_remote(branch_name):
        if confirm_create_branch():
            if not git_push(set_upstream=True):
                print_error("Failed to push and create branch on remote")
                return 1
        else:
            print_info("Push operation cancelled")
            return 0
    else:
        if not git_push():
            return 1

    return 0


def validate_repository_state(commit_only: bool = False, paths: Optional[List[str]] = None) -> bool:
    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return False

    print_section("Repository Validation")
    if not check_remote_access():
        sys.exit(1)

    if not commit_only:
        print_section("Changes Validation")
        if not check_has_changes(paths):
            print_error(
                "No changes to commit in the specified path(s). Make some changes before running the tool."
            )
            return False

    return True


def handle_git_workflow(commit_only: bool = False, paths: Optional[List[str]] = None) -> int:
    if not validate_repository_state(commit_only, paths):
        return 1

    if not commit_only:
        print_section("Git Staging")
        if not git_add(paths):
            print_error("Failed to stage changes. Exiting workflow.")
            return 1

        print_section("Pre-commit Validation")
        if not check_and_install_pre_commit():
            print_error("Pre-commit checks failed. Aborting workflow.")
            return 1

    print_section("Commit Message Generation")
    print_process("Building conventional commit message...")
    commit_message = generate_commit_message()
    if not commit_message:
        return 1

    if commit_only:
        print_section("Commit Complete")
        print_info("No changes were committed")
        return 0

    print_section("Commit")
    if not git_commit(commit_message):
        print_error("Failed to commit changes. Exiting workflow.")
        return 1

    if confirm_push():
        branch_name = get_current_branch()
        if not branch_name:
            print_error("Failed to determine current branch name")
            return 1

        if not branch_exists_on_remote(branch_name):
            if confirm_create_branch():
                if not git_push(set_upstream=True):
                    print_error("Failed to push and create branch on remote")
                    return 1
            else:
                print_info("Changes committed locally only")
                return 0
        else:
            if not git_push():
                return 1
    return 0


def main(args: Optional[List[str]] = None) -> int:
    try:
        parsed_args = parse_args(args)

        if not any(help_flag in sys.argv for help_flag in ["-h", "--help"]):
            print_logo()

        if parsed_args.edit:
            return handle_edit()
        elif parsed_args.delete:
            return handle_delete()
        elif parsed_args.push:
            return handle_push_only()
        elif parsed_args.reset:
            return handle_reset()
        elif parsed_args.tag:
            return handle_tag()
        else:
            return handle_git_workflow(commit_only=parsed_args.commit, paths=parsed_args.path)

    except KeyboardInterrupt:
        print()
        print_warning("Operation cancelled by user")
        return 130
    except Exception as e:
        print_error("An unexpected error occurred")
        print(f"\033[91m{str(e)}\033[0m")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
