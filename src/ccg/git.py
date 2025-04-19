"""Git operations for the Conventional Commits Generator."""

import subprocess
from typing import List, Optional, Tuple

from ccg.utils import print_error, print_process, print_success, print_info


def git_add() -> bool:
    """Run 'git add' to stage changes.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print_process("Staging changes with git...")
        subprocess.run(["git", "add", "."], capture_output=True, check=True)
        print_success("Changes staged successfully")
        return True
    except subprocess.CalledProcessError as error:
        print_error("Error during 'git add':")
        print(f"\033[91m{error.stderr.decode()}\033[0m")
        return False
    except FileNotFoundError:
        print_error("Git is not installed. Please install Git and try again.")
        return False


def git_commit(commit_message: str) -> bool:
    """Run 'git commit' with the provided message.

    Args:
        commit_message: The commit message to use

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print_process("Committing changes...")
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print_success("New commit successfully created!")
        return True
    except subprocess.CalledProcessError as error:
        print_error("Error during 'git commit'")
        if error.stderr:
            print(f"\033[91m{error.stderr.decode()}\033[0m")
        return False


def git_push() -> bool:
    """Run 'git push' to push changes.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print_process("Pushing changes to remote repository...")
        subprocess.run(["git", "push"], check=True)
        print_success("Changes pushed successfully!")
        return True
    except subprocess.CalledProcessError as error:
        print_error("Error during 'git push'")
        if error.stderr:
            print(f"\033[91m{error.stderr.decode()}\033[0m")
        return False


def get_staged_files() -> List[str]:
    """Get the list of staged files.

    Returns:
        List[str]: The list of staged files
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            check=True,
            capture_output=True,
            text=True
        )
        return [file for file in result.stdout.strip().split("\n") if file]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def check_is_git_repo() -> bool:
    """Check if the current directory is a git repository.

    Returns:
        bool: True if it's a git repository, False otherwise
    """
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


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
            return True

        # Check if pre-commit is installed
        try:
            subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print_info("pre-commit is configured but not installed.")
            print_info("Run 'pip install pre-commit' to install it.")
            print_info("After installing, run 'pre-commit install' to set up the hooks.")
            return False

        # Install pre-commit hooks
        print_process("Setting up pre-commit hooks...")
        subprocess.run(["pre-commit", "install"], check=True, capture_output=True)
        print_success("Pre-commit hooks installed successfully")

        # Run pre-commit against staged files
        print_process("Running pre-commit checks on staged files...")
        staged_files = get_staged_files()

        # Only run pre-commit if there are staged files
        if staged_files:
            result = subprocess.run(
                ["pre-commit", "run", "--files"] + staged_files,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print_error("Some pre-commit checks failed. Exiting the script.")
                # Display the output
                print(result.stdout)
                print(result.stderr)
                # Return False when pre-commit fails
                return False

        print_success("All pre-commit checks passed successfully")
        return True

    except Exception as e:
        print_error(f"Unexpected error during pre-commit checks: {str(e)}")
        return False
