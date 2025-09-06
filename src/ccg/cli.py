"""Command-line interface for Conventional Commits Generator."""

import argparse
import sys
from typing import List, Optional

from ._version import __version__
from .common.decorators import handle_keyboard_interrupt, with_error_handling
from .core.operations import handle_commit_operation
from .core.workflows import (
    handle_git_workflow,
    handle_pull,
    handle_push_only,
    handle_reset,
    handle_tag,
)
from .git.operations import get_current_branch, get_repository_name
from .ui.display import print_error, print_info, print_logo, print_warning


class CustomHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter that shows the logo."""

    def __init__(self, prog):
        super().__init__(prog, max_help_position=50, width=100)

    def _format_usage(self, usage, actions, groups, prefix):
        print_logo()
        return super()._format_usage(usage, actions, groups, prefix)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="ccg",
        description="Conventional Commits Generator - Create standardized git commits",
        formatter_class=CustomHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push committed changes to remote repository without creating a new commit",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Fetch and pull latest changes from remote repository to current branch",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Generate and preview commit message without actually committing changes",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Discard all local changes, reset to HEAD, and pull latest from remote",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Create a new annotated or lightweight Git tag and push it to remote",
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help="Edit an existing commit message (recent or by hash selection)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Compare two commits and show detailed differences between them",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show detailed working directory status with staged/unstaged changes",
    )
    parser.add_argument(
        "--dir", metavar="PATH", help="Specify target directory where CCG will execute git commands"
    )
    parser.add_argument(
        "--add",
        metavar="FILE/DIR",
        help="Add specific file or directory to staging area before committing",
    )
    return parser.parse_args(args)


def handle_edit() -> int:
    """Handle edit commit operation."""
    return handle_commit_operation("edit")


def handle_diff() -> int:
    """Handle diff commit operation."""
    return handle_commit_operation("diff")


def handle_status() -> int:
    """Handle status operation."""
    from .common.decorators import require_git_repo
    from .git.operations import show_working_directory_status
    from .ui.display import print_section

    @require_git_repo
    def _handle_status():
        print_section("Working Directory Status")
        return 0 if show_working_directory_status() else 1

    return _handle_status()


def change_working_directory(path: str) -> bool:
    """Change working directory to specified path and validate it's a git repository."""
    import os

    from .git.operations import is_git_repository
    from .ui.display import print_error, print_info

    # Convert to absolute path and validate
    try:
        abs_path = os.path.abspath(os.path.expanduser(path))
        if not os.path.exists(abs_path):
            print_error(f"Path '{path}' does not exist")
            return False

        if not os.path.isdir(abs_path):
            print_error(f"Path '{path}' is not a directory")
            return False

        # Change to the directory
        os.chdir(abs_path)
        print_info(f"Changed working directory to: {abs_path}")

        # Validate it's a git repository
        if not is_git_repository():
            print_error(f"Directory '{abs_path}' is not a git repository")
            return False

        return True

    except Exception as e:
        print_error(f"Failed to change directory to '{path}': {str(e)}")
        return False


def validate_and_resolve_path(path: str, working_dir: Optional[str] = None) -> Optional[str]:
    """Validate that the specified path exists and is within the working directory hierarchy."""
    import os

    from .ui.display import print_error, print_info

    # Get the current working directory (or the specified one)
    if working_dir:
        base_dir = os.path.abspath(os.path.expanduser(working_dir))
    else:
        base_dir = os.getcwd()

    try:
        # Convert to absolute path
        abs_path = os.path.abspath(os.path.expanduser(path))

        # Check if path exists
        if not os.path.exists(abs_path):
            print_error(f"Path '{path}' does not exist")
            return None

        # Check if path is within the working directory hierarchy
        try:
            rel_path = os.path.relpath(abs_path, base_dir)
            if rel_path.startswith(".."):
                print_error(f"Path '{path}' is outside the working directory '{base_dir}'")
                print_info("Only paths within the current working directory can be committed")
                return None
        except ValueError:
            # Different drives on Windows
            print_error(f"Path '{path}' is outside the working directory '{base_dir}'")
            return None

        # Determine if it's a file or folder for display message
        if os.path.isfile(abs_path):
            print_info(f"Validated file '{rel_path}' for staging")
        elif os.path.isdir(abs_path):
            print_info(f"Validated folder '{rel_path}' for staging")
        else:
            print_error(f"Path '{path}' is neither a file nor a directory")
            return None

        return rel_path

    except Exception as e:
        print_error(f"Error validating path '{path}': {str(e)}")
        return None


def validate_argument_order() -> None:
    """Validate that --dir comes first before all other flags."""
    argv = sys.argv[1:]  # Skip script name

    if "--dir" not in argv:
        return  # No --dir flag, nothing to validate

    # Find position of --dir
    dir_index = argv.index("--dir")

    # All flags that should come after --dir
    all_other_flags = [
        "--status",
        "--diff",
        "--edit",
        "--push",
        "--pull",
        "--reset",
        "--tag",
        "--commit",
        "--add",
    ]

    for flag in all_other_flags:
        if flag in argv:
            flag_index = argv.index(flag)
            if flag_index < dir_index:
                print_error(f"Invalid argument order. --dir must come before {flag}")
                print_info(f"Correct usage: ccg --dir <path> {flag} ...")
                sys.exit(1)


@handle_keyboard_interrupt("Operation cancelled by user")
@with_error_handling(default_return=1)
def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    # Validate argument order before parsing
    if not args:  # Only validate when called from command line, not in tests
        validate_argument_order()

    parsed_args = parse_args(args)

    # Validate and resolve file path if --add is specified
    validated_path = None
    if parsed_args.add:
        validated_path = validate_and_resolve_path(parsed_args.add, parsed_args.dir)
        if validated_path is None:
            return 1

    # Change working directory if --dir is specified
    if parsed_args.dir:
        if not change_working_directory(parsed_args.dir):
            return 1

    if not any(help_flag in sys.argv for help_flag in ["-h", "--help"]):
        print_logo()

        # Show current branch and repository
        current_branch = get_current_branch()
        repo_name = get_repository_name()
        if current_branch and repo_name:
            print_info(f"Currently on branch: {current_branch} | Repository: {repo_name}")
        elif current_branch:
            print_info(f"Currently on branch: {current_branch}")

    if parsed_args.edit:
        return handle_edit()
    elif parsed_args.diff:
        return handle_diff()
    elif parsed_args.status:
        return handle_status()
    elif parsed_args.push:
        return handle_push_only()
    elif parsed_args.pull:
        return handle_pull()
    elif parsed_args.reset:
        return handle_reset()
    elif parsed_args.tag:
        return handle_tag()
    else:
        # Convert single path to list for compatibility with existing workflow
        paths = [validated_path] if validated_path else None
        return handle_git_workflow(commit_only=parsed_args.commit, paths=paths)


if __name__ == "__main__":
    sys.exit(main())
