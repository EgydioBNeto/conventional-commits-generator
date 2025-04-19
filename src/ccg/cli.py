"""Command-line interface for Conventional Commits Generator."""

import argparse
import sys
import traceback
from typing import List, Optional, NoReturn

from ccg import __version__
from ccg.core import generate_commit_message, confirm_push
from ccg.git import git_add, git_commit, git_push, check_and_install_pre_commit, check_is_git_repo
from ccg.utils import (
    print_header, print_section, print_success, print_error,
    print_warning, print_info, print_process, print_complete, print_logo
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

    return parser.parse_args(args)


def handle_push_only() -> int:
    """Handle push-only mode.

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    print_section("Push Only Mode")
    print_process("Pushing existing commits to remote repository...")
    if git_push():
        print_success("Changes pushed successfully to remote!")
        return 0

    print_error("Failed to push changes to remote")
    return 1


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

    # Stage changes
    if not dry_run:
        print_section("Git Staging")
        print_process("Staging changes for commit...")
        if not git_add():
            print_error("Failed to stage changes. Exiting workflow.")
            return 1
        print_success("Changes staged successfully")

        # Check for pre-commit hooks
        print_section("Pre-commit Validation")
        print_process("Running pre-commit checks on staged files...")
        if not check_and_install_pre_commit():
            print_error("Pre-commit checks failed. Aborting workflow.")
            return 1
        print_success("All pre-commit checks passed successfully")

    # Generate commit message
    print_section("Commit Message Generation")
    print_process("Building conventional commit message...")
    commit_message = generate_commit_message()
    if not commit_message:
        print_error("Failed to generate commit message. Exiting workflow.")
        return 1

    # Dry run mode
    if dry_run:
        print_section("Dry Run Complete")
        print_info("No changes were committed (dry-run mode)")
        return 0

    # Commit changes
    print_section("Commit")
    print_process("Committing changes to local repository...")
    if not git_commit(commit_message):
        print_error("Failed to commit changes. Exiting workflow.")
        return 1
    print_success("Changes committed successfully to local repository")

    # Ask to push changes
    if confirm_push():
        print_section("Remote Push")
        print_process("Pushing commits to remote repository...")
        if not git_push():
            print_error("Failed to push changes to remote")
            return 1
        print_success("Changes pushed successfully to remote repository")

    print_complete()
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

        # Just push mode
        if parsed_args.push:
            return handle_push_only()

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
