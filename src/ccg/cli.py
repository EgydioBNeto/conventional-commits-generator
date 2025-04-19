"""Command-line interface for Conventional Commits Generator."""

import argparse
import os
import sys
import traceback
from typing import List, Optional

from ccg import __version__
from ccg.core import (check_and_install_pre_commit, confirm_push,
                      generate_commit_message, git_add, git_commit, git_push)

# Enhanced terminal colors and styles
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

# Symbols for different message types
CHECK = "✓"
ARROW = "→"
CROSS = "✗"
INFO = "ℹ"
STAR = "★"
WARNING = "⚠"

# Get terminal width for centered text
try:
    TERM_WIDTH = os.get_terminal_size().columns
except (AttributeError, OSError):
    TERM_WIDTH = 80


def print_header(text: str) -> None:
    """Print a stylized header."""
    print()
    print(f"{CYAN}{BOLD}{'═' * TERM_WIDTH}{RESET}")
    print(f"{CYAN}{BOLD}{text.center(TERM_WIDTH)}{RESET}")
    print(f"{CYAN}{BOLD}{'═' * TERM_WIDTH}{RESET}")
    print()


def print_section(text: str) -> None:
    """Print a section divider."""
    print()
    print(f"{BLUE}{BOLD}┌{'─' * (len(text) + 2)}┐{RESET}")
    print(f"{BLUE}{BOLD}│ {text} │{RESET}")
    print(f"{BLUE}{BOLD}└{'─' * (len(text) + 2)}┘{RESET}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{GREEN}{BOLD}{CHECK} {message}{RESET}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{BLUE}{INFO} {message}{RESET}")


def print_process(message: str) -> None:
    """Print a process message."""
    print(f"{YELLOW}{ARROW} {message}{RESET}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{RED}{BOLD}{CROSS} {message}{RESET}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{MAGENTA}{WARNING} {message}{RESET}")


def print_complete() -> None:
    """Print a completion message."""
    print()
    print(f"{GREEN}{BOLD}{STAR} All done! {STAR}{RESET}")
    print()


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="ccg",
        description="Conventional Commits Generator - Create standardized git commits",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
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


def main(args: Optional[List[str]] = None) -> int:
    """Main function for the CLI application."""
    try:
        parsed_args = parse_args(args)

        print_header("Conventional Commits Generator")

        # Just push mode
        if parsed_args.push:
            print_section("Push Only Mode")
            print_process("Pushing existing commits to remote repository...")
            if git_push():
                print_success("Changes pushed successfully to remote!")
                return 0
            print_error("Failed to push changes to remote")
            return 1

        # Stage changes
        if not parsed_args.dry_run:
            print_section("Git Staging")
            print_process("Staging changes for commit...")
            if not git_add():
                print_error("Failed to stage changes. Exiting workflow.")
                return 1
            print_success("Changes staged successfully")

        # Check for pre-commit hooks
        if not parsed_args.dry_run:
            print_section("Pre-commit Validation")
            print_process("Running pre-commit checks on staged files...")
            pre_commit_result = check_and_install_pre_commit()
            if not pre_commit_result:
                print_error("Pre-commit checks failed. Aborting workflow.")
                sys.exit(1)  # Force immediate exit
            print_success("All pre-commit checks passed successfully")

        # Generate commit message
        print_section("Commit Message Generation")
        print_process("Building conventional commit message...")
        commit_message = generate_commit_message()
        if not commit_message:
            print_error("Failed to generate commit message. Exiting workflow.")
            return 1

        # Dry run mode
        if parsed_args.dry_run:
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

    except KeyboardInterrupt:
        print()
        print_warning("Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print_error("An unexpected error occurred")
        print(f"{RED}{str(e)}{RESET}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
