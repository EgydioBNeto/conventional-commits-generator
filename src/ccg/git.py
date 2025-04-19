"""Git operations for the Conventional Commits Generator."""

import subprocess
from typing import List, Optional, Tuple, Any

from ccg.utils import print_error, print_process, print_success, print_info, print_warning


def run_git_command(command: List[str], error_message: str, success_message: Optional[str] = None,
                   show_output: bool = False) -> Tuple[bool, Any]:
    """Run a git command and handle errors consistently.

    Args:
        command: The git command to run as a list of strings
        error_message: Message to display on error
        success_message: Message to display on success (optional)
        show_output: Whether to return the command output

    Returns:
        Tuple[bool, Any]: Success status and command output if show_output is True
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True
        )

        if success_message:
            print_success(success_message)

        if show_output:
            return True, result.stdout.strip()
        return True, None

    except subprocess.CalledProcessError as error:
        print_error(error_message)
        # When text=True is used, stderr is already a string, no need to decode
        if show_output:
            return False, error.stderr if error.stderr else error.stdout
        else:
            if error.stderr:
                print(f"\033[91m{error.stderr}\033[0m")
            return False, None

    except FileNotFoundError:
        print_error("Git is not installed. Please install Git and try again.")
        return False, None


def git_add() -> bool:
    """Run 'git add' to stage changes.

    Returns:
        bool: True if successful, False otherwise
    """
    print_process("Staging changes with git...")
    success, _ = run_git_command(
        ["git", "add", "."],
        "Error during 'git add'",
        "Changes staged successfully"
    )
    return success


def git_commit(commit_message: str) -> bool:
    """Run 'git commit' with the provided message.

    Args:
        commit_message: The commit message to use

    Returns:
        bool: True if successful, False otherwise
    """
    print_process("Committing changes...")
    success, _ = run_git_command(
        ["git", "commit", "-m", commit_message],
        "Error during 'git commit'",
        "New commit successfully created!"
    )
    return success


def git_push() -> bool:
    """Run 'git push' to push changes.

    Returns:
        bool: True if successful, False otherwise
    """
    print_process("Pushing changes to remote repository...")
    success, _ = run_git_command(
        ["git", "push"],
        "Error during 'git push'",
        "Changes pushed successfully!"
    )
    return success


def get_staged_files() -> List[str]:
    """Get the list of staged files.

    Returns:
        List[str]: The list of staged files
    """
    success, output = run_git_command(
        ["git", "diff", "--name-only", "--cached"],
        "Failed to get staged files",
        show_output=True
    )

    if success and output:
        return [file for file in output.split("\n") if file]
    return []


def check_is_git_repo() -> bool:
    """Check if the current directory is a git repository.

    Returns:
        bool: True if it's a git repository, False otherwise
    """
    success, _ = run_git_command(
        ["git", "rev-parse", "--is-inside-work-tree"],
        "Not a git repository",
        show_output=True
    )
    return success


def check_and_install_pre_commit() -> bool:
    """Check for pre-commit config and install hooks if needed.

    Returns:
        bool: True if pre-commit checks pass or are not needed, False otherwise
    """
    try:
        # First check if .pre-commit-config.yaml exists
        try:
            with open(".pre-commit-config.yaml", "r"):
                pass
        except FileNotFoundError:
            # No pre-commit config found, that's okay
            print_info("No pre-commit configuration found. Skipping pre-commit checks.")
            return True

        # Check if pre-commit is installed
        pre_commit_installed, _ = run_git_command(
            ["pre-commit", "--version"],
            "pre-commit command not found",
            show_output=True
        )

        if not pre_commit_installed:
            print_warning("pre-commit is configured but not installed.")
            print_info("Run 'pip install pre-commit' to install it.")
            print_info("After installing, run 'pre-commit install' to set up the hooks.")
            return False

        # Install pre-commit hooks
        print_process("Setting up pre-commit hooks...")
        hooks_installed, _ = run_git_command(
            ["pre-commit", "install"],
            "Failed to install pre-commit hooks",
            "Pre-commit hooks installed successfully"
        )

        if not hooks_installed:
            return False

        # Run pre-commit against staged files
        print_process("Running pre-commit checks on staged files...")
        staged_files = get_staged_files()

        # Only run pre-commit if there are staged files
        if staged_files:
            # For pre-commit, we'll run it directly to capture the full output
            try:
                result = subprocess.run(
                    ["pre-commit", "run", "--files"] + staged_files,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print_error("Some pre-commit checks failed:")
                    # Print the complete output to help with debugging
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(f"\033[91m{result.stderr}\033[0m")
                    return False

                print_success("All pre-commit checks passed successfully")
            except subprocess.CalledProcessError as e:
                print_error("Error running pre-commit:")
                if e.stdout:
                    print(e.stdout)
                if e.stderr:
                    print(f"\033[91m{e.stderr}\033[0m")
                return False
            except Exception as e:
                print_error(f"Unexpected error running pre-commit: {str(e)}")
                return False

        return True

    except Exception as e:
        print_error(f"Unexpected error during pre-commit checks: {str(e)}")
        return False
