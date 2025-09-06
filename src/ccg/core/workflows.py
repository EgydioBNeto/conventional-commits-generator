"""CLI helper functions and operations."""

from typing import List, Optional

from ..common.config import COLORS, INPUT_LIMITS
from ..common.decorators import require_git_repo, require_remote_access, section_header
from ..core.interactive import confirm_push, generate_commit_message
from ..git.operations import (
    branch_exists_on_remote,
    check_and_install_pre_commit,
    check_has_changes,
    check_remote_access,
    create_tag,
    discard_local_changes,
    fetch_and_pull_all,
    get_current_branch,
    git_add,
    git_commit,
    git_push,
    pull_from_remote,
    push_tag,
)
from ..ui.display import (
    print_error,
    print_info,
    print_process,
    print_section,
    print_success,
    print_warning,
)
from ..ui.input import confirm_user_action, read_input


def confirm_create_branch() -> bool:
    """Confirm creation of remote branch."""
    print_section("Create Remote Branch")
    print_info("This branch doesn't exist on the remote repository yet")
    return confirm_user_action(
        f"{COLORS['YELLOW']}Create and push this branch to remote? [Y/n]{COLORS['RESET']}",
        success_message="Branch will be created on remote",
        cancel_message="Not creating branch on remote",
    )


def confirm_reset() -> bool:
    """Confirm reset operation."""
    print_warning("This will discard ALL local changes and pull the latest from remote.")
    print_warning("All uncommitted work will be lost!")
    return confirm_user_action(
        f"{COLORS['YELLOW']}Are you sure you want to proceed? [Y/n]{COLORS['RESET']}",
        success_message=None,
        cancel_message="Reset operation cancelled",
    )


def handle_push_after_edit(branch_name: str) -> int:
    """Handle push operations after commit edit."""
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
            f"{COLORS['YELLOW']}Force push changes? [Y/n]{COLORS['RESET']}",
            success_message=None,
            cancel_message="Changes remain local only",
        )

        if force_push:
            if not git_push(force=True):
                print_error("Failed to force push changes to remote")
                return 1

    return 0


@require_git_repo
@require_remote_access
def handle_tag() -> int:
    """Handle git tag creation."""
    print_section("Git Tag Creation")

    tag_name = read_input(
        f"{COLORS['YELLOW']}Enter the tag name (e.g., v1.0.0){COLORS['RESET']}",
        max_length=INPUT_LIMITS["tag"],
    )

    if not tag_name:
        print_error("Tag name cannot be empty. Aborting.")
        return 1

    annotated = confirm_user_action(
        f"{COLORS['YELLOW']}Create an annotated tag with a message? [Y/n]{COLORS['RESET']}",
        success_message=None,
        cancel_message=None,
    )

    tag_message = None
    if annotated:
        tag_message = read_input(
            f"{COLORS['YELLOW']}Enter the tag message{COLORS['RESET']}",
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


@require_git_repo
@require_remote_access
def handle_reset() -> int:
    """Handle reset local changes operation."""
    print_section("Reset Local Changes")

    if not check_has_changes():
        pull_anyway = confirm_user_action(
            f"{COLORS['YELLOW']}No changes to discard. Do you still want to pull latest changes? [Y/n]{COLORS['RESET']}",
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


@require_git_repo
@require_remote_access
def handle_push_only() -> int:
    """Handle push-only operation."""
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


@require_git_repo
@require_remote_access
def handle_pull() -> int:
    """Handle pull operation to fetch and pull all changes."""
    return 0 if fetch_and_pull_all() else 1


def validate_repository_state(commit_only: bool = False, paths: Optional[List[str]] = None) -> bool:
    """Validate repository state before operations."""
    from ..git.operations import check_is_git_repo

    if not check_is_git_repo():
        print_error("Not a git repository. Please initialize one with 'git init'.")
        return False

    print_section("Repository Validation")
    if not check_remote_access():
        return False

    if not commit_only:
        print_section("Changes Validation")
        if not check_has_changes(paths):
            print_error(
                "No changes to commit in the specified path(s). Make some changes before running the tool."
            )
            return False

    return True


def handle_git_workflow(commit_only: bool = False, paths: Optional[List[str]] = None) -> int:
    """Handle the main git workflow (stage, commit, push)."""
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
