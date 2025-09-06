"""Commit operations like edit and diff."""

from typing import List, Optional, Tuple

from ..common.config import COLORS, ERROR_MESSAGES
from ..common.decorators import require_git_repo, section_header
from ..common.helpers import find_matching_commits
from ..git.operations import (
    edit_commit_message,
    get_commit_by_hash,
    get_recent_commits,
    show_commit_diff,
    show_diff_between_commits,
    show_diff_commit_vs_working,
    show_enhanced_diff_between_commits,
    show_working_directory_status,
)
from ..ui.display import print_error, print_info, print_section, print_success, print_warning
from ..ui.input import confirm_user_action, read_input
from ..ui.validation import validate_commit_message


class CommitSelector:
    """Helper class to handle commit selection logic."""

    def __init__(self, commits: List[Tuple], operation_type: str):
        self.commits = commits
        self.operation_type = operation_type

    def display_commits(self, count: Optional[int]) -> None:
        """Display the list of commits."""
        has_local_changes = False

        # Add local changes option for diff operations (only for target selection)
        if "use as target" in self.operation_type:
            from ..git import run_git_command

            # Check for both staged and unstaged changes
            success, local_files = run_git_command(
                ["git", "status", "--porcelain"],
                f"Failed to get local changes",
                show_output=True,
            )
            has_local_changes = success and local_files.strip()

        # Show appropriate message based on what's available
        if len(self.commits) == 0 and has_local_changes:
            print_info("No previous commits available, but local changes detected:")
        elif len(self.commits) > 0:
            print_info(f"Showing {'all' if count is None else 'last'} {len(self.commits)} commits:")
        else:
            print_info("No commits available for comparison.")

        if has_local_changes:
            print(f"0. Local Changes (uncommitted work)")

        for i, commit in enumerate(self.commits, start=1):
            full_hash, short_hash, subject, author, date = commit
            print(f"{i}. [{short_hash}] {subject} - {author} ({date})")

    def get_user_selection(self) -> Optional[str]:
        """Get commit selection from user input."""
        while True:
            selection = read_input(
                f"{COLORS['YELLOW']}Enter commit number or hash to {self.operation_type}{COLORS['RESET']}",
                max_length=7,
            )

            if selection.lower() in ("q", "quit", "exit"):
                print_info(f"{self.operation_type.capitalize()} operation cancelled")
                return None

            # Check for local changes option (0) for diff operations (only for target selection)
            if selection == "0" and "use as target" in self.operation_type:
                from ..git import run_git_command

                # Check for both staged and unstaged changes
                success, local_files = run_git_command(
                    ["git", "status", "--porcelain"],
                    f"Failed to get local changes",
                    show_output=True,
                )
                if success and local_files.strip():
                    return "LOCAL_CHANGES"
                else:
                    print_error("No local changes found.")
                    continue

            # Check if it's a valid number
            if selection.isdigit() and 1 <= int(selection) <= len(self.commits):
                idx = int(selection) - 1
                return self.commits[idx][0]

            # Check if it matches a commit hash
            matching_commits = find_matching_commits(self.commits, selection)
            if len(matching_commits) == 1:
                return matching_commits[0][0]
            elif len(matching_commits) > 1:
                print_error("Multiple commits match this hash. Please be more specific.")
                continue

            print_error("Invalid selection. Please try again.")


def get_commit_count_input() -> Optional[int]:
    """Get the number of commits to display from user."""
    while True:
        count_input = read_input(
            f"{COLORS['YELLOW']}How many recent commits to display? (Enter or 0 for all){COLORS['RESET']}",
            max_length=6,
        )
        if not count_input or count_input == "0":
            return None
        if count_input.isdigit() and int(count_input) > 0:
            return int(count_input)
        print_error("Please enter a valid positive number, 0, or press Enter for all commits.")


def display_commit_details(commit_details: Tuple[str, str, str, str, str, str]) -> None:
    """Display detailed information about a commit."""
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
    """Handle editing of commit message and body."""
    print_info("Edit the commit message below. Leave empty to cancel.")
    print_info(
        "Message must follow conventional commit format: <type>[optional scope][optional !]: <description>"
    )

    new_message = read_input(
        f"{COLORS['YELLOW']}New commit message{COLORS['RESET']}",
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
            f"{COLORS['YELLOW']}Would you like to try again? [Y/n]{COLORS['RESET']}",
            success_message=None,
            cancel_message="Edit cancelled. Commit message remains unchanged.",
        )

        if retry:
            return handle_commit_edit_input(subject, original_body)
        return None, None

    new_body = read_input(
        f"{COLORS['YELLOW']}New commit body (optional){COLORS['RESET']}",
        history_type="body",
        default_text=original_body or "",
    )

    if not new_body:
        new_body = None

    return new_message, new_body


def confirm_commit_edit(
    original_subject: str, original_body: Optional[str], new_message: str, new_body: Optional[str]
) -> bool:
    """Confirm commit edit with before/after preview."""
    from ..core import confirm_commit
    from ..ui.display import format_commit_message_box, print_section

    print_section("Original")
    format_commit_message_box(original_subject, original_body)
    return confirm_commit(new_message, new_body)


@section_header("Recent Commits")
def select_commit_for_operation(
    operation_type: str, after_commit: Optional[str] = None
) -> Optional[str]:
    """Select a commit for edit or diff operation."""
    count = get_commit_count_input()
    commits = get_recent_commits(count)
    if not commits:
        print_error("Failed to retrieve recent commits or no commits found.")
        return None

    # Filter commits if we need to show only commits before a specific commit
    if after_commit and after_commit != "LOCAL_CHANGES":
        filtered_commits = []

        for commit in commits:
            commit_hash = commit[0]
            if commit_hash == after_commit:
                break
            filtered_commits.append(commit)

        if filtered_commits:
            commits = filtered_commits
        else:
            # If no commits before base but this is target selection, show empty list
            # The CommitSelector will show local changes if available
            if "target" in operation_type:
                commits = []
            else:
                print_warning("No commits found before the selected base commit.")
                return None

    selector = CommitSelector(commits, operation_type)
    selector.display_commits(count if not after_commit else None)

    print_section("Commit Selection")
    return selector.get_user_selection()


@require_git_repo
def handle_commit_operation(operation_type: str) -> int:
    """Handle edit or diff commit operations."""
    if operation_type == "diff":
        return diff_two_commits()

    selected_hash = select_commit_for_operation(operation_type)
    if not selected_hash:
        return 0

    if operation_type == "edit":
        return edit_specific_commit(selected_hash)


def edit_specific_commit(commit_hash: str) -> int:
    """Edit a specific commit by hash."""
    from ..core import confirm_push
    from ..git import get_current_branch

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
        from .workflows import handle_push_after_edit

        branch_name = get_current_branch()
        if not branch_name:
            print_error("Failed to determine current branch name")
            return 1
        return handle_push_after_edit(branch_name)

    return 0


def diff_two_commits() -> int:
    """Compare two commits interactively."""
    base_commit = select_commit_for_operation("use as base")
    if not base_commit:
        return 0

    # Check if there are local changes available for comparison
    from ..git import run_git_command

    success, local_files = run_git_command(
        ["git", "status", "--porcelain"],
        f"Failed to get local changes",
        show_output=True,
    )
    has_local_changes = success and local_files.strip()

    target_commit = select_commit_for_operation("use as target", after_commit=base_commit)
    if not target_commit:
        # If no target commit selected and no local changes, show error
        if not has_local_changes:
            print_error("No commits available for comparison and no local changes found.")
            print_info("Make some changes to your files or select a different base commit.")
        return 0

    # Show what changed between base -> target
    from ..git import get_commit_by_hash

    base_details = None if base_commit == "LOCAL_CHANGES" else get_commit_by_hash(base_commit)
    target_details = None if target_commit == "LOCAL_CHANGES" else get_commit_by_hash(target_commit)

    print_section("Comparison Summary")
    if base_commit == "LOCAL_CHANGES":
        print_info(f"FROM: Local Changes (uncommitted work)")
        if target_details:
            print_info(f"TO:   [{target_details[1]}] {target_details[2]}")
    elif target_commit == "LOCAL_CHANGES":
        if base_details:
            print_info(f"FROM: [{base_details[1]}] {base_details[2]}")
        print_info(f"TO:   Local Changes (uncommitted work)")
    else:
        if base_details and target_details:
            print_info(f"FROM: [{base_details[1]}] {base_details[2]}")
            print_info(f"TO:   [{target_details[1]}] {target_details[2]}")

    print_section("Changes Analysis")

    # Handle local changes comparisons
    if base_commit == "LOCAL_CHANGES" or target_commit == "LOCAL_CHANGES":
        if base_commit == "LOCAL_CHANGES" and target_commit == "LOCAL_CHANGES":
            print_error("Cannot compare local changes with itself")
            return 1

        from ..git import show_local_changes_interactive

        if not show_local_changes_interactive():
            print_error("Failed to show local changes")
            return 1
    else:
        if not show_enhanced_diff_between_commits(base_commit, target_commit):
            print_error("Failed to show diff between commits")
            return 1

    return 0
