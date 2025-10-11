"""Command-line interface for Conventional Commits Generator."""

import argparse
import os
import sys
import traceback
from functools import wraps
from typing import Any, Callable, List, Optional, Tuple, TypeVar, cast

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
    get_remote_name,
    get_repository_name,
    get_repository_root,
    git_add,
    git_commit,
    git_push,
    is_path_in_repository,
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


def show_repository_info() -> None:
    """Display current repository and branch information.

    Retrieves and prints the repository name and current branch in a formatted
    style with colors. This is shown at the start of most CLI operations to
    provide context about the working repository.

    Note:
        Silently returns if repository name or branch cannot be determined
    """
    from ccg.utils import BOLD, CYAN, RESET

    repo_name = get_repository_name()
    branch_name = get_current_branch()

    if repo_name and branch_name:
        print(
            f"{CYAN}Repository:{RESET} {BOLD}{repo_name}{RESET}  {CYAN}Branch:{RESET} {BOLD}{branch_name}{RESET}"
        )


F = TypeVar("F", bound=Callable[..., int])


def require_git_repo(func: F) -> F:
    """Decorator to ensure function runs in a git repository.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function that checks for git repository first
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        if not check_is_git_repo():
            print_error("Not a git repository. Please initialize one with 'git init'.")
            return 1
        show_repository_info()
        return func(*args, **kwargs)

    return cast(F, wrapper)


class CustomHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter that displays ASCII logo before help text.

    Extends ArgumentParser's default formatter to print the CCG logo
    when --help is invoked, providing better visual branding.
    """

    def __init__(self, prog: str) -> None:
        super().__init__(prog, max_help_position=50, width=100)

    def _format_usage(self, usage: Any, actions: Any, groups: Any, prefix: Optional[str]) -> str:
        """Format usage text with logo prepended."""
        print_logo()
        return super()._format_usage(usage, actions, groups, prefix)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse and validate command-line arguments for CCG.

    Parses all CLI flags and options, validates unknown arguments, and returns
    a namespace with the parsed values. Shows the ASCII logo and helpful error
    messages for invalid arguments.

    Args:
        args: Optional list of arguments to parse (defaults to sys.argv if None)

    Returns:
        Namespace object containing all parsed command-line arguments with
        boolean flags (push, commit, reset, tag, edit, delete) and optional
        path list

    Raises:
        SystemExit: If unknown/invalid arguments are provided, exits with code 1
    """
    parser = argparse.ArgumentParser(
        prog="ccg",
        description="Conventional Commits Generator - Create standardized git commits",
        formatter_class=CustomHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--push",
        action="store_true",
        help="Just run git push without creating a new commit",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Generate commit message without actually committing",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Discard all local changes and pull latest from remote",
    )
    parser.add_argument(
        "--tag", action="store_true", help="Create a new Git tag and push it to remote"
    )
    parser.add_argument("--edit", action="store_true", help="Edit an existing commit message")
    parser.add_argument("--delete", action="store_true", help="Delete an existing commit")
    parser.add_argument(
        "--path",
        nargs="+",
        help="Specify path(s) to stage or directory to work in",
    )

    # Parse args and catch unknown arguments
    parsed_args, unknown = parser.parse_known_args(args)

    # If there are unknown arguments, show error
    if unknown:
        print_logo()
        print_error(f"Unrecognized arguments: {' '.join(unknown)}")
        print_info("Run 'ccg --help' to see available options")
        sys.exit(1)

    return parsed_args


def confirm_create_branch() -> bool:
    """Prompt user to confirm creating a new branch on the remote repository.

    Displays an informational section explaining that the current branch doesn't
    exist remotely and asks the user if they want to create it. Used when pushing
    commits to a branch that has no upstream tracking.

    Returns:
        True if user confirms branch creation, False otherwise
    """
    print_section("Create Remote Branch")
    print_info("This branch doesn't exist on the remote repository yet")
    return confirm_user_action(
        f"{YELLOW}Create and push this branch to remote? (y/n){RESET}",
        success_message="Branch will be created on remote",
        cancel_message="Not creating branch on remote",
    )


def confirm_reset() -> bool:
    """Prompt user to confirm a destructive reset operation.

    Displays warning messages about the dangers of resetting (losing all local
    uncommitted changes) and requires explicit user confirmation before proceeding.
    Used by the --reset flag workflow.

    Returns:
        True if user confirms the reset, False to cancel

    Note:
        This is a destructive operation - all uncommitted work will be lost
    """
    print_warning("This will discard ALL local changes and pull the latest from remote.")
    print_warning("All uncommitted work will be lost!")
    return confirm_user_action(
        f"{YELLOW}Are you sure you want to proceed? (y/n){RESET}",
        success_message=None,
        cancel_message="Reset operation cancelled",
    )


def get_commit_count_input() -> Optional[int]:
    """Prompt user for the number of recent commits to display.

    Asks the user how many recent commits they want to see in the commit
    selection list. Validates input to ensure it's a positive integer, allows
    0 or empty input to show all commits.

    Returns:
        Positive integer for specific count, or None to show all commits

    Note:
        Loops until valid input is provided (positive number, 0, or Enter)
    """
    while True:
        count_input = read_input(
            f"{YELLOW}How many recent commits to display? (Enter or 0 for all){RESET}",
            max_length=6,
        )
        if not count_input or count_input == "0":
            return None
        if count_input.isdigit() and int(count_input) > 0:
            return int(count_input)
        print_error("Please enter a valid positive number, 0, or press Enter for all commits.")


@require_git_repo
def handle_commit_operation(operation_type: str) -> int:
    """Generic handler for commit edit and delete operations.

    Displays recent commits, prompts user to select one by number or hash,
    then delegates to the appropriate specific handler (edit or delete).
    Supports partial hash matching and validates selections.

    Args:
        operation_type: Type of operation ("edit" or "delete")

    Returns:
        0 on success, 1 on error or if no commits found

    Note:
        Requires git repository (enforced by @require_git_repo decorator)
    """
    print_section(f"{operation_type.capitalize()} Commit")

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
        full_hash, short_hash, subject, author, date = commit
        print(f"{i}. [{short_hash}] {subject} - {author} ({date})")
    print()

    print_section("Commit Selection")
    while True:
        selection = read_input(
            f"{YELLOW}Enter commit number or hash to {operation_type}{RESET}",
            max_length=7,
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
    """Handle the --edit flag workflow for editing commit messages.

    Entry point for commit editing. Delegates to handle_commit_operation
    to display commits and get user selection, then edits the chosen commit.

    Returns:
        0 on success, 1 on error

    Note:
        Supports editing both latest commit (amend) and older commits (filter-branch)
    """
    return handle_commit_operation("edit")


def handle_delete() -> int:
    """Handle the --delete flag workflow for deleting commits.

    Entry point for commit deletion. Delegates to handle_commit_operation
    to display commits and get user selection, then deletes the chosen commit.

    Returns:
        0 on success, 1 on error

    Note:
        Supports deleting latest commit (reset) and older commits (rebase)
    """
    return handle_commit_operation("delete")


def display_commit_details(commit_details: Tuple[str, str, str, str, str, str]) -> None:
    """Display detailed information about a specific commit.

    Prints formatted commit details including full hash, short hash, author,
    date, subject, and body (if present). Used before editing or deleting
    commits to show the user what they're modifying.

    Args:
        commit_details: Tuple containing (full_hash, short_hash, subject,
                        body, author, date) from get_commit_by_hash()
    """
    hash_full, hash_short, subject, body, author, date = commit_details
    print(f"Hash: {hash_full}")
    print(f"Author: {author}")
    print(f"Date: {date}")
    print(f"Subject: {subject}")
    if body:
        print(f"Body:\n{body}")


def handle_commit_edit_input(
    subject: str, original_body: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Prompt user to edit commit message and body with validation.

    Displays the current message as default text and allows the user to edit it.
    Validates the new message against conventional commit format. If invalid,
    shows examples and offers a retry. Also prompts for optional commit body.

    Args:
        subject: Current commit subject/message line
        original_body: Current commit body (if any)

    Returns:
        Tuple of (new_message, new_body) or (None, None) if cancelled

    Note:
        Recursively retries if validation fails and user chooses to try again
    """
    print_info("Edit the commit message below. Leave empty to cancel.")
    print_info(
        "Message must follow conventional commit format: <type>[optional scope][optional !]: <description>"
    )

    new_message = read_input(
        f"{YELLOW}New commit message{RESET}",
        history_type="edit_message",
        default_text=subject,
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

    new_body_input = read_input(
        f"{YELLOW}New commit body (optional){RESET}",
        history_type="body",
        default_text=original_body or "",
    )

    new_body: Optional[str] = new_body_input if new_body_input else None

    return new_message, new_body


def confirm_commit_edit(
    original_subject: str,
    original_body: Optional[str],
    new_message: str,
    new_body: Optional[str],
) -> bool:
    """Display original and new commit messages and confirm the edit.

    Shows a side-by-side comparison of the original commit (with emoji rendering)
    and the new commit message. Delegates to confirm_commit() for the final
    user confirmation.

    Args:
        original_subject: Original commit subject line
        original_body: Original commit body (if any)
        new_message: New commit subject line to apply
        new_body: New commit body to apply (if any)

    Returns:
        True if user confirms the edit, False otherwise
    """
    print_section("Original")

    from ccg.core import convert_emoji_codes_to_real
    from ccg.utils import BOLD, CYAN, RESET

    # Display original commit message
    display_header = convert_emoji_codes_to_real(original_subject)
    print(f"{CYAN}Commit:{RESET} {BOLD}{display_header}{RESET}")

    if original_body:
        print()
        print(f"{CYAN}Body:{RESET}")
        for line in original_body.split("\n"):
            print(line)

    print()
    return confirm_commit(new_message, new_body)


def handle_push_after_edit(branch_name: str) -> int:
    """Handle pushing changes after editing or deleting a commit.

    Determines the appropriate push strategy based on whether the branch exists
    remotely. For new branches, offers to create upstream. For existing branches,
    warns about force push requirements and asks for confirmation.

    Args:
        branch_name: Name of the current branch to push

    Returns:
        0 on success, 1 on error

    Note:
        Force push is required when editing/deleting commits that exist remotely
    """
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
    """Edit a specific commit identified by its hash.

    Retrieves and displays commit details, prompts user for new message/body,
    validates the changes, confirms with user, then applies the edit. Offers
    to push changes after successful edit.

    Args:
        commit_hash: Full or partial hash of commit to edit

    Returns:
        0 on success or user cancellation, 1 on error

    Note:
        Latest commits use amend, older commits use filter-branch
    """
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
    """Delete a specific commit identified by its hash.

    Retrieves and displays commit details, shows destructive warning, requires
    explicit confirmation, then permanently deletes the commit from history.
    Offers to push changes after successful deletion.

    Args:
        commit_hash: Full or partial hash of commit to delete

    Returns:
        0 on success or user cancellation, 1 on error

    Note:
        This is destructive and irreversible. Latest commits use reset,
        older commits use interactive rebase
    """
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


@require_git_repo
def handle_tag() -> int:
    """Handle the --tag flag workflow for creating and pushing git tags.

    Prompts user for tag name, asks if they want an annotated tag (with message),
    creates the tag, and pushes it to the remote repository. Validates remote
    access before proceeding.

    Returns:
        0 on success, 1 on error or if inputs are invalid

    Note:
        Requires git repository (enforced by @require_git_repo decorator)
    """
    print_section("Git Tag Creation")

    if not check_remote_access():
        return 1

    tag_name = read_input(
        f"{YELLOW}Enter the tag name (e.g., v1.0.0){RESET}",
        max_length=INPUT_LIMITS["tag"],
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

    push = confirm_user_action(
        f"{YELLOW}Push tag '{tag_name}' to remote? (y/n){RESET}",
        success_message=None,
        cancel_message=None,
    )

    if push:
        if not push_tag(tag_name):
            print_error("Failed to push tag to remote.")
            return 1
    else:
        print_info(f"Tag '{tag_name}' created locally only")
    return 0


@require_git_repo
def handle_reset() -> int:
    """Handle the --reset flag workflow for discarding changes and pulling latest.

    Checks for local changes, warns about data loss, requires confirmation,
    discards all uncommitted changes, and pulls latest from remote. If no
    changes exist, offers to pull anyway.

    Returns:
        0 on success or user cancellation, 1 on error

    Note:
        This is destructive - all uncommitted work will be lost
    """
    print_section("Reset Local Changes")

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
    """Handle the --push flag workflow for pushing without creating a commit.

    Validates repository and remote access, determines current branch, checks
    if branch exists remotely. For new branches, offers to create upstream.
    For existing branches, performs a normal push.

    Returns:
        0 on success or user cancellation, 1 on error

    Note:
        Does not require @require_git_repo decorator as it does its own validation
    """
    print_section("Push Only Mode")

    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return 1

    show_repository_info()

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
    """Validate that the repository is ready for git operations.

    Checks if current directory is a git repository, displays repository info,
    validates remote access, and optionally checks for changes in specified paths.

    Args:
        commit_only: If True, skip change validation (used for --commit flag)
        paths: Optional list of specific paths to check for changes

    Returns:
        True if repository state is valid and ready, False otherwise

    Note:
        Exits with code 1 if remote access fails (considered critical)
    """
    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return False

    show_repository_info()

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
    """Execute the main CCG workflow for creating and pushing commits.

    Orchestrates the complete commit workflow: validate repository state, stage
    changes, run pre-commit hooks, generate commit message, create commit, and
    optionally push. Handles branch creation for new remote branches.

    Args:
        commit_only: If True, generate message without committing (--commit flag)
        paths: Optional list of specific files/directories to stage

    Returns:
        0 on success or user cancellation, 1 on error

    Note:
        This is the core workflow executed when running ccg without flags
    """
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


def validate_paths_exist(paths: List[str]) -> None:
    """Validate that all provided paths exist.

    Args:
        paths: List of paths to validate

    Raises:
        SystemExit: If any path does not exist
    """
    invalid_paths = []
    for path in paths:
        if not os.path.exists(path):
            invalid_paths.append(path)

    if invalid_paths:
        print_error(f"Invalid path(s): {', '.join(invalid_paths)}")
        print_info("All paths must be valid files or directories")
        print_info("Usage:")
        print_info("  • ccg --path <directory>")
        print_info("  • ccg --path <directory> --flag")
        print_info("  • ccg --path <file1> <file2> ... (for staging specific files)")
        sys.exit(1)


def validate_paths_in_repository(paths: List[str]) -> None:
    """Validate that all paths are within the current git repository.

    Args:
        paths: List of paths to validate

    Raises:
        SystemExit: If any path is outside the repository
    """
    # Get current repository root
    repo_root = get_repository_root()
    if not repo_root:
        print_error("Failed to determine git repository root")
        sys.exit(1)

    # Check each path
    paths_outside_repo = []
    for path in paths:
        if not is_path_in_repository(path, repo_root):
            paths_outside_repo.append(path)

    if paths_outside_repo:
        print_error(f"Path(s) outside repository: {', '.join(paths_outside_repo)}")
        print_info(f"Repository root: {repo_root}")
        print_info("All paths must be within the same git repository")
        sys.exit(1)


def change_to_working_directory(paths: Optional[List[str]]) -> Optional[List[str]]:
    """Change to working directory if specified in paths.

    If paths contains a single directory, change to it and return None.
    Otherwise, return paths as-is for staging.

    Args:
        paths: List of paths from command line

    Returns:
        Paths to stage, or None if directory change was performed
    """
    if not paths:
        return None

    # Validate all paths exist first
    validate_paths_exist(paths)

    # If there's only one path and it's a directory, change to it
    if len(paths) == 1 and os.path.isdir(paths[0]):
        target_dir = os.path.abspath(paths[0])
        try:
            os.chdir(target_dir)
            return None
        except Exception as e:
            print_error(f"Failed to change to directory '{paths[0]}': {e}")
            sys.exit(1)

    # For multiple paths or files, validate they're all in the same repository
    # This must be done AFTER we've changed directory if needed
    validate_paths_in_repository(paths)

    # Otherwise, treat as paths to stage
    return paths


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CCG CLI application.

    Parses command-line arguments, handles directory changes from --path flag,
    routes to appropriate workflow handlers based on flags (--edit, --delete,
    --push, --reset, --tag, --commit), and manages error handling for the
    entire application.

    Args:
        args: Optional list of arguments (defaults to sys.argv if None)

    Returns:
        Exit code: 0 for success, 1 for errors, 130 for user cancellation

    Examples:
        >>> main()  # Interactive commit workflow
        0
        >>> main(['--push'])  # Push only mode
        0
        >>> main(['--tag'])  # Tag creation mode
        0

    Note:
        Catches EOFError and KeyboardInterrupt for graceful cancellation
    """
    try:
        parsed_args = parse_args(args)

        if not any(help_flag in sys.argv for help_flag in ["-h", "--help"]):
            print_logo()

        # Handle directory change if --path points to a single directory
        # This works for all operations
        stage_paths = parsed_args.path
        working_dir_changed = False

        if parsed_args.path and any(
            [
                parsed_args.push,
                parsed_args.edit,
                parsed_args.delete,
                parsed_args.reset,
                parsed_args.tag,
            ]
        ):
            # For these operations, --path should change directory
            stage_paths = change_to_working_directory(parsed_args.path)
            working_dir_changed = True

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
            # For normal workflow, --path can either change directory OR specify files to stage
            if not working_dir_changed and parsed_args.path:
                stage_paths = change_to_working_directory(parsed_args.path)
            return handle_git_workflow(commit_only=parsed_args.commit, paths=stage_paths)

    except (EOFError, KeyboardInterrupt):
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
