"""Core functionality for the Conventional Commits Generator."""

import subprocess
import sys
from typing import Dict, List, Optional

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Commit types with explanations
COMMIT_TYPES: List[Dict[str, str]] = [
    {
        "type": "feat",
        "description": "A new feature for the user or a particular enhancement",
    },
    {"type": "fix", "description": "A bug fix for the user or a particular issue"},
    {"type": "chore", "description": "Routine tasks, maintenance, or minor updates"},
    {
        "type": "refactor",
        "description": "Code refactoring without changing its behavior",
    },
    {
        "type": "style",
        "description": "Code style changes, formatting, or cosmetic improvements",
    },
    {"type": "docs", "description": "Documentation-related changes"},
    {"type": "test", "description": "Adding or modifying tests"},
    {
        "type": "build",
        "description": "Changes that affect the build system or external dependencies",
    },
    {"type": "revert", "description": "Reverts a previous commit"},
    {"type": "ci", "description": "Changes to CI configuration files and scripts"},
    {"type": "perf", "description": "A code change that improves performance"},
]


def read_input(prompt: str) -> str:
    """Read user input with a given prompt."""
    return input(f"{prompt}: ").strip()


def display_commit_types() -> None:
    """Display available commit types with explanations."""
    for i, commit_data in enumerate(COMMIT_TYPES, start=1):
        print(f"{i}. {commit_data['type']:<10} - {commit_data['description']}")


def choose_commit_type() -> str:
    """Prompt the user to choose a commit type."""
    display_commit_types()

    while True:
        try:
            user_input = read_input(f"{YELLOW}Choose the commit type{RESET}")

            if user_input.isdigit() and 1 <= int(user_input) <= len(COMMIT_TYPES):
                commit_type = COMMIT_TYPES[int(user_input) - 1]["type"]
                return commit_type

            # Check if the input matches a commit type directly
            for commit_data in COMMIT_TYPES:
                if user_input.lower() == commit_data["type"].lower():
                    return commit_data["type"]

            print(f"{RED}Invalid choice. Please select a valid option.{RESET}")
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            sys.exit(0)


def get_scope() -> Optional[str]:
    """Get the commit scope from user input."""
    scope = read_input(f"{YELLOW}Enter the scope (optional){RESET}")
    return scope if scope else None


def is_breaking_change() -> bool:
    """Check if the commit is a breaking change."""
    while True:
        breaking = read_input(
            f"{YELLOW}Is this a BREAKING CHANGE? (y/n){RESET}"
        ).lower()
        if breaking in ("y", "n"):
            return breaking == "y"
        print(f"{RED}Invalid choice. Please enter 'y' or 'n'.{RESET}")


def get_commit_message() -> str:
    """Get the commit message from user input."""
    while True:
        message = read_input(f"{YELLOW}Enter the commit message{RESET}")
        if message.strip():
            return message
        print(f"{RED}Commit message cannot be empty.{RESET}")


def generate_commit_message() -> Optional[str]:
    """Generate a conventional commit message based on user input."""
    try:
        # Get commit components
        commit_type = choose_commit_type()
        scope = get_scope()
        breaking_change = is_breaking_change()
        message = get_commit_message()

        # Construct the commit message
        breaking_indicator = "!" if breaking_change else ""
        scope_part = f"({scope})" if scope else ""
        header = f"{commit_type}{breaking_indicator}{scope_part}: "
        commit_message = f"{header}{message}"

        # Display and confirm
        print(f"{YELLOW}Commit message:{RESET}")
        print(f"{GREEN}{commit_message}{RESET}")

        while True:
            confirm = read_input(f"{YELLOW}Confirm this commit? (y/n){RESET}").lower()
            if confirm in ("y", "n"):
                if confirm == "y":
                    return commit_message
                print("\nExiting. Goodbye!")
                sys.exit(0)
            print(f"{RED}Invalid choice. Please enter 'y' or 'n'.{RESET}")

    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)

    return None


def git_add() -> bool:
    """Run 'git add' to stage changes."""
    try:
        subprocess.run(["git", "add", "."], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError as error:
        print(f"{RED}Error during 'git add':{RESET}")
        print(f"{RED}{error.stderr.decode()}{RESET}")
        return False
    except FileNotFoundError:
        print(f"{RED}Git is not installed. Please install Git and try again.{RESET}")
        return False


def git_commit(commit_message: str) -> bool:
    """Run 'git commit' with the provided message."""
    try:
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(f"{GREEN}New commit successfully made.{RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"{RED}Error during 'git commit'.{RESET}")
        return False


def confirm_push() -> bool:
    """Ask user to confirm push."""
    confirm = read_input(
        f"{YELLOW}Do you want to push these changes? (y/n){RESET}"
    ).lower()
    return confirm == "y"


def git_push() -> bool:
    """Run 'git push' to push changes."""
    try:
        subprocess.run(["git", "push"], check=True)
        print(f"{GREEN}Changes pushed.{RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"{RED}Error during 'git push'.{RESET}")
        return False


def check_and_install_pre_commit() -> bool:
    """Check for pre-commit config and install hooks if needed."""
    try:
        # Check if .pre-commit-config.yaml exists
        with open(".pre-commit-config.yaml", "r"):
            pass

        # Check if pre-commit is installed
        try:
            subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)

            # Install pre-commit hooks
            print(f"{YELLOW}Setting up pre-commit hooks...{RESET}")
            subprocess.run(["pre-commit", "install"], check=True, capture_output=True)
            print(f"{GREEN}Pre-commit hooks installed successfully.{RESET}")

            # Run pre-commit against staged files
            print(f"{YELLOW}Running pre-commit checks on staged files...{RESET}")

            # Get the list of staged files using a separate subprocess call
            staged_files_process = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                check=False,
                capture_output=True,
                text=True,
            )

            if staged_files_process.returncode == 0:
                # Split the output into a list of files
                staged_files = staged_files_process.stdout.strip().split("\n")

                # Only run pre-commit if there are staged files
                if staged_files and staged_files[0]:
                    result = subprocess.run(
                        ["pre-commit", "run", "--files"] + staged_files,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode != 0:
                        print(
                            f"{RED}Some pre-commit checks failed. "
                            f"Exiting the script.{RESET}"
                        )
                        # Display the output
                        print(result.stdout)
                        print(result.stderr)
                        # Return False when pre-commit fails
                        # This will signal to exit the main workflow
                        return False

            print(f"{GREEN}Pre-commit checks passed.{RESET}")
            return True

        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"{YELLOW}pre-commit is configured but not installed.{RESET}")
            print(f"{YELLOW}Run 'pip install pre-commit' to install it.{RESET}")
            print(
                f"{YELLOW}After installing, run 'pre-commit install' to set up the hooks.{RESET}"
            )
            return False

    except FileNotFoundError:
        # No pre-commit config found, that's okay
        return True
