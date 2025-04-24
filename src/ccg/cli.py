"""Command-line interface for Conventional Commits Generator."""

import argparse
import sys
import traceback
from typing import List, Optional, NoReturn

from ccg import __version__
from ccg.core import generate_commit_message, confirm_push
from ccg.git import (
    git_add, git_commit, git_push, check_and_install_pre_commit,
    check_is_git_repo, check_has_changes, check_remote_access,
    get_current_branch, branch_exists_on_remote, discard_local_changes,
    pull_from_remote, create_tag, push_tag, get_recent_commits,
    get_commit_by_hash, edit_commit_message
)
from ccg.utils import (
    print_header, print_section, print_success, print_error,
    print_warning, print_info, print_process, print_logo,
    read_input, YELLOW, RESET
)


class CustomHelpFormatter(argparse.HelpFormatter):
    """Custom formatter for argparse help text that includes ASCII logo."""

    def __init__(self, prog):
        super().__init__(prog, max_help_position=50, width=100)

    def _format_usage(self, usage, actions, groups, prefix):
        # First print the logo
        print_logo()
        # Then format usage as usual
        return super()._format_usage(usage, actions, groups, prefix)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: Command line arguments (None uses sys.argv)

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="ccg",
        description="Conventional Commits Generator - Create standardized git commits",
        formatter_class=CustomHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Just run git push without creating a new commit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate commit message without actually committing",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Discard all local changes and pull latest from remote",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Create a new Git tag and optionally push it to remote",
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help="Edit an existing commit message",
    )
    parser.add_argument(
        "--list",
        type=int,
        help="Number of recent commits to display when using --edit",
        metavar="N",
    )
    parser.add_argument(
        "--commit",
        help="Hash of the specific commit to edit",
        metavar="HASH",
    )

    return parser.parse_args(args)


def confirm_create_branch() -> bool:
    """Ask user to confirm creating a branch on the remote repository.

    Returns:
        bool: True if confirmed, False otherwise
    """
    print_section("Create Remote Branch")
    print_info("This branch doesn't exist on the remote repository yet")

    while True:
        confirm = read_input(
            f"{YELLOW}Create and push this branch to remote? (y/n){RESET}"
        ).lower()

        if not confirm:
            print_warning("Please enter 'y' or 'n'")
            continue

        if confirm in ("y", "yes"):
            return True
        elif confirm in ("n", "no"):
            print_info("Not creating branch on remote")
            return False

        print_error("Invalid choice. Please enter 'y' or 'n'.")


def confirm_reset() -> bool:
    """Ask user to confirm resetting local changes.

    Returns:
        bool: True if confirmed, False otherwise
    """
    print_warning("This will discard ALL local changes and pull the latest from remote.")
    print_warning("All uncommitted work will be lost!")

    while True:
        confirm = read_input(
            f"{YELLOW}Are you sure you want to proceed? (y/n){RESET}"
        ).lower()

        if not confirm:
            print_warning("Please enter 'y' or 'n'")
            continue

        if confirm in ("y", "yes"):
            return True
        elif confirm in ("n", "no"):
            print_info("Reset operation cancelled")
            return False

        print_error("Invalid choice. Please enter 'y' or 'n'.")


def handle_edit(commit_hash: Optional[str] = None, list_count: Optional[int] = 5) -> int:
    """Handle editing a commit message.

    Args:
        commit_hash: Hash of the specific commit to edit
        list_count: Number of recent commits to display

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    print_section("Edit Commit")

    # Check if we're in a git repository
    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    if commit_hash:
        # Edit specific commit
        return edit_specific_commit(commit_hash)
    else:
        # Show list of commits
        return show_commit_list(list_count)


def show_commit_list(count: int = 5) -> int:
    """Show a list of recent commits and let the user select one to edit.

    Args:
        count: Number of recent commits to display

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """

    # Get recent commits
    commits = get_recent_commits(count)
    if not commits:
        print_error("Failed to retrieve recent commits or no commits found.")
        return 1

    # Display the commits
    print_info(f"Showing last {len(commits)} commits:")
    print()

    for i, commit in enumerate(commits, start=1):
        # Each commit is a tuple of (full_hash, short_hash, subject, author, date)
        full_hash, short_hash, subject, author, date = commit
        print(f"{i}. [{short_hash}] {subject} - {author} ({date})")

    print()

    # Ask user to select a commit
    while True:
        selection = read_input(
            f"{YELLOW}Enter commit number or hash to edit (or 'q' to quit){RESET}"
        )

        if selection.lower() in ('q', 'quit', 'exit'):
            print_info("Edit operation cancelled")
            return 0

        # Check if selection is a number
        if selection.isdigit() and 1 <= int(selection) <= len(commits):
            idx = int(selection) - 1
            selected_hash = commits[idx][0]  # Get full hash
            return edit_specific_commit(selected_hash)

        # Check if selection is a hash (partial or full)
        matching_commits = [c for c in commits if c[0].startswith(selection)]
        if len(matching_commits) == 1:
            return edit_specific_commit(matching_commits[0][0])
        elif len(matching_commits) > 1:
            print_error("Multiple commits match this hash. Please be more specific.")
            continue

        print_error("Invalid selection. Please try again.")


def edit_specific_commit(commit_hash: str) -> int:
    """Edit a specific commit message.

    Args:
        commit_hash: Hash of the commit to edit

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Get the commit details
    commit_details = get_commit_by_hash(commit_hash)
    if not commit_details:
        print_error(f"Commit with hash '{commit_hash}' not found.")
        return 1

    hash_full, hash_short, subject, body, author, date = commit_details
    print(f"Hash: {hash_full}")
    print(f"Author: {author}")
    print(f"Date: {date}")
    print(f"Subject: {subject}")
    if body:
        print(f"Body:\n{body}")

    print()
    print_info("Enter the new commit message. Leave empty to cancel.")

    new_message = read_input(
        f"{YELLOW}New commit message{RESET}",
        history_type="message"
    )

    if not new_message:
        print_info("Edit cancelled. Commit message remains unchanged.")
        return 0

    # Confirm the edit
    print_section("Confirm Edit")
    print_info("Original: " + subject)
    print_info("New: " + new_message)

    while True:
        confirm = read_input(
            f"{YELLOW}Confirm this change? (y/n){RESET}"
        ).lower()

        if not confirm:
            print_warning("Please enter 'y' or 'n'")
            continue

        if confirm in ("y", "yes"):
            break
        elif confirm in ("n", "no"):
            print_info("Edit cancelled. Commit message remains unchanged.")
            return 0

        print_error("Invalid choice. Please enter 'y' or 'n'.")

    # Edit the commit message
    if not edit_commit_message(hash_full, new_message):
        print_error("Failed to edit commit.")
        return 1

    # Ask to push changes
    if confirm_push():

        # Get current branch name
        branch_name = get_current_branch()
        if not branch_name:
            print_error("Failed to determine current branch name")
            return 1

        # Check if branch exists on remote
        if not branch_exists_on_remote(branch_name):
            # Branch doesn't exist on remote, ask to create it
            if confirm_create_branch():
                if not git_push(set_upstream=True):
                    print_error("Failed to push and create branch on remote")
                    return 1
            else:
                print_info("Changes remain local only")
                return 0
        else:
            # Push with --force to update the commit
            print_warning("Force push is required to update the commit on the remote.")
            print_warning("This can potentially overwrite other changes. Use with caution!")

            while True:
                force_confirm = read_input(
                    f"{YELLOW}Force push changes? (y/n){RESET}"
                ).lower()

                if not force_confirm:
                    print_warning("Please enter 'y' or 'n'")
                    continue

                if force_confirm in ("y", "yes"):
                    if not git_push(force=True):
                        print_error("Failed to force push changes to remote")
                        return 1
                    break
                elif force_confirm in ("n", "no"):
                    print_info("Changes remain local only")
                    return 0

                print_error("Invalid choice. Please enter 'y' or 'n'.")

    return 0


def handle_tag() -> int:
    """Handle creating and pushing a tag.

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    print_section("Git Tag Creation")

    # Check if we're in a git repository
    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    # Check if we have access to the remote repository
    if not check_remote_access():
        print_error("Cannot access remote repository. Tag creation aborted.")
        return 1

    # Ask for tag name and message
    tag_name = read_input(f"{YELLOW}Enter the tag name (e.g., v1.0.0){RESET}")
    if not tag_name:
        print_error("Tag name cannot be empty. Aborting.")
        return 1

    # Ask if this should be an annotated tag
    while True:
        annotated = read_input(f"{YELLOW}Create an annotated tag with a message? (y/n){RESET}").lower()

        if not annotated:
            print_warning("Please enter 'y' or 'n'")
            continue

        if annotated in ("y", "yes"):
            tag_message = read_input(f"{YELLOW}Enter the tag message{RESET}")
            if not tag_message:
                print_error("Tag message cannot be empty for annotated tags. Aborting.")
                return 1
            break
        elif annotated in ("n", "no"):
            tag_message = None
            break

        print_error("Invalid choice. Please enter 'y' or 'n'.")

    # Create the tag
    if not create_tag(tag_name, tag_message):
        print_error("Failed to create tag. Aborting.")
        return 1

    # Ask if we should push the tag
    while True:
        push = read_input(f"{YELLOW}Push tag '{tag_name}' to remote? (y/n){RESET}").lower()

        if not push:
            print_warning("Please enter 'y' or 'n'")
            continue

        if push in ("y", "yes"):
            if not push_tag(tag_name):
                print_error("Failed to push tag to remote.")
                return 1
            break
        elif push in ("n", "no"):
            print_info(f"Tag '{tag_name}' created locally only")
            break

        print_error("Invalid choice. Please enter 'y' or 'n'.")

    print_success(f"Tag operation completed successfully")
    return 0


def handle_reset() -> int:
    """Handle resetting local changes and pulling from remote.

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    print_section("Reset Local Changes")

    # Check if we're in a git repository
    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    # Check if we have access to the remote repository
    if not check_remote_access():
        print_error("Cannot access remote repository. Reset aborted.")
        return 1

    # Check if there are local changes
    if not check_has_changes():
        print_info("No local changes detected.")

        # Ask if they still want to pull latest changes
        while True:
            confirm = read_input(
                f"{YELLOW}No changes to discard. Do you still want to pull latest changes? (y/n){RESET}"
            ).lower()

            if not confirm:
                print_warning("Please enter 'y' or 'n'")
                continue

            if confirm in ("y", "yes"):
                break
            elif confirm in ("n", "no"):
                print_info("Reset operation cancelled")
                return 0

            print_error("Invalid choice. Please enter 'y' or 'n'.")
    else:
        # Confirm before discarding changes
        if not confirm_reset():
            return 0

        # Discard local changes
        if not discard_local_changes():
            print_error("Failed to discard local changes")
            return 1

    # Pull latest changes
    if not pull_from_remote():
        print_error("Failed to pull latest changes from remote")
        return 1

    print_success("Reset complete! Working directory is now in sync with remote")
    return 0


def handle_push_only() -> int:
    """Handle push-only mode.

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    print_section("Push Only Mode")

    # Check if we're in a git repository
    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    # Check if we have access to the remote repository
    if not check_remote_access():
        print_error("Cannot access remote repository. Push aborted.")
        return 1

    # Get current branch name
    branch_name = get_current_branch()
    if not branch_name:
        print_error("Failed to determine current branch name")
        return 1

    # Check if branch exists on remote
    if not branch_exists_on_remote(branch_name):
        # Branch doesn't exist on remote, ask to create it
        if confirm_create_branch():
            if not git_push(set_upstream=True):
                print_error("Failed to push and create branch on remote")
                return 1
        else:
            print_info("Push operation cancelled")
            return 0
    else:
        # Normal push for existing branch - now handles upstream errors internally
        if not git_push():
            # The git_push function now handles the upstream error case internally
            # So if it returns False here, it means either:
            # 1. The user chose not to set upstream
            # 2. There was a different error that couldn't be resolved
            return 1

    return 0


def handle_git_workflow(dry_run: bool = False) -> int:
    """Handle the git workflow (add, commit, push).

    Args:
        dry_run: If True, don't actually commit changes

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Check if we're in a git repository
    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    # Check if we have access to the remote repository early in the process
    print_section("Repository Validation")
    if not check_remote_access():
        print_error("Cannot access remote repository. Commit process aborted.")
        return 1

    # Check if there are changes to commit (skip in dry-run mode)
    if not dry_run:
        print_section("Changes Validation")
        if not check_has_changes():
            print_error("No changes to commit. Make some changes before running the tool.")
            return 1

    # Stage changes
    if not dry_run:
        print_section("Git Staging")
        if not git_add():
            print_error("Failed to stage changes. Exiting workflow.")
            return 1

        # Check for pre-commit hooks
        print_section("Pre-commit Validation")
        if not check_and_install_pre_commit():
            print_error("Pre-commit checks failed. Aborting workflow.")
            return 1

    # Generate commit message
    print_section("Commit Message Generation")
    print_process("Building conventional commit message...")
    commit_message = generate_commit_message()
    if not commit_message:
        return 1

    # Dry run mode
    if dry_run:
        print_section("Dry Run Complete")
        print_info("No changes were committed (dry-run mode)")
        return 0

    # Commit changes
    print_section("Commit")
    if not git_commit(commit_message):
        print_error("Failed to commit changes. Exiting workflow.")
        return 1

    # Ask to push changes
    if confirm_push():

        # Get current branch name
        branch_name = get_current_branch()
        if not branch_name:
            print_error("Failed to determine current branch name")
            return 1

        # Check if branch exists on remote
        if not branch_exists_on_remote(branch_name):
            # Branch doesn't exist on remote, ask to create it
            if confirm_create_branch():
                if not git_push(set_upstream=True):
                    print_error("Failed to push and create branch on remote")
                    return 1
            else:
                print_info("Changes committed locally only")
                return 0
        else:
            # Normal push for existing branch - now handles upstream errors internally
            if not git_push():
                # The git_push function now handles the upstream error case internally
                # So if it returns False here, it means either:
                # 1. The user chose not to set upstream
                # 2. There was a different error that couldn't be resolved
                return 1
    return 0


def main(args: Optional[List[str]] = None) -> int:
    """Main function for the CLI application.

    Args:
        args: Command line arguments (None uses sys.argv)

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    try:
        parsed_args = parse_args(args)

        # Only print the header if we're not showing help (which already has the logo)
        if not any(help_flag in sys.argv for help_flag in ['-h', '--help']):
            print_logo()

        # Edit commit mode
        if parsed_args.edit:
            # Get list count (default 5)
            list_count = parsed_args.list or 5
            # Get commit hash (if provided)
            commit_hash = parsed_args.commit

            return handle_edit(commit_hash, list_count)

        # Just push mode
        if parsed_args.push:
            return handle_push_only()

        # Reset mode
        if parsed_args.reset:
            return handle_reset()

        # Tag mode
        if parsed_args.tag:
            return handle_tag()

        # Normal or dry-run mode
        return handle_git_workflow(dry_run=parsed_args.dry_run)

    except KeyboardInterrupt:
        print()
        print_warning("Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print_error("An unexpected error occurred")
        print(f"\033[91m{str(e)}\033[0m")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
