"""Command-line interface for Conventional Commits Generator."""

import argparse
import sys
import traceback
from typing import List, Optional

from ccg import __version__
from ccg.core import (
    GREEN,
    RED,
    RESET,
    YELLOW,
    check_and_install_pre_commit,
    confirm_push,
    generate_commit_message,
    git_add,
    git_commit,
    git_push,
)


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

        print(f"{GREEN}Conventional Commits Generator{RESET}")

        # Just push mode
        if parsed_args.push:
            print(f"{YELLOW}Push mode: pushing existing commits...{RESET}")
            if git_push():
                print(f"{GREEN}Push successful.{RESET}")
                return 0
            print(f"{RED}Push failed.{RESET}")
            return 1

        # Stage changes
        if not parsed_args.dry_run:
            print(f"{YELLOW}Staging changes...{RESET}")
            if not git_add():
                print(f"{RED}Failed to stage changes. Exiting.{RESET}")
                return 1
            print(f"{GREEN}Changes staged successfully.{RESET}")

        # Check for pre-commit hooks (only if not in dry-run mode)
        if not parsed_args.dry_run:
            print(f"{YELLOW}Running pre-commit checks...{RESET}")
            pre_commit_result = check_and_install_pre_commit()
            if not pre_commit_result:
                print(f"{RED}Aborting commit due to pre-commit check failures.{RESET}")
                sys.exit(1)  # Force immediate exit
            print(f"{GREEN}Pre-commit checks passed.{RESET}")

        # Generate commit message
        print(f"{YELLOW}Generating commit message...{RESET}")
        commit_message = generate_commit_message()
        if not commit_message:
            print(f"{RED}Failed to generate commit message. Exiting.{RESET}")
            return 1

        # Dry run mode - just show the message and exit
        if parsed_args.dry_run:
            print(f"{GREEN}Dry run complete. No commit was made.{RESET}")
            return 0

        # Commit changes
        print(f"{YELLOW}Committing changes...{RESET}")
        if not git_commit(commit_message):
            print(f"{RED}Failed to commit changes. Exiting.{RESET}")
            return 1
        print(f"{GREEN}Changes committed successfully.{RESET}")

        # Ask to push changes
        if confirm_push():
            print(f"{YELLOW}Pushing changes...{RESET}")
            if not git_push():
                print(f"{RED}Failed to push changes.{RESET}")
                return 1
            print(f"{GREEN}Changes pushed successfully.{RESET}")

        print(f"{GREEN}All done!{RESET}")
        return 0

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Operation cancelled by user.{RESET}")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"{RED}An unexpected error occurred:{RESET}")
        print(f"{RED}{str(e)}{RESET}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
