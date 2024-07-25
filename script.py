#!/usr/bin/env python3
"""CCG - Conventional Commits Generator"""

import subprocess
import sys

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def read_input(prompt):
    """Read user input with a given prompt."""
    return input(f"{prompt}: ").strip()

def choose_commit_type():
    """Prompt the user to choose a commit type."""
    commit_types_explanation = [
        "feat - A new feature for the user or a particular enhancement",
        "fix - A bug fix for the user or a particular issue",
        "chore - Routine tasks, maintenance, or minor updates",
        "refactor - Code refactoring without changing its behavior",
        "style - Code style changes, formatting, or cosmetic improvements",
        "docs - Documentation-related changes",
        "test - Adding or modifying tests",
        "build - Changes that affect the build system or external dependencies",
    ]

    print(YELLOW + "Choose the commit type:" + RESET)
    for i, explanation in enumerate(commit_types_explanation, start=1):
        print(f"{i}. {explanation}")

    while True:
        try:
            user_input = read_input(
                YELLOW + "Choose the commit type or enter directly " +
                "(e.g., feat, fix, chore):" + RESET
            )

            # Validate user input
            if user_input.isdigit() and 1 <= int(user_input) <= len(commit_types_explanation):
                commit_type = commit_types_explanation[int(user_input) - 1].split()[0]
            elif user_input.lower() in [ct.split()[0].lower() for ct in commit_types_explanation]:
                commit_type = user_input.lower()
            else:
                print(RED + "Invalid choice. Please select a valid option." + RESET)
                continue

            return commit_type
        except KeyboardInterrupt:
            print("\nExiting the script. Goodbye!")
            sys.exit()

def generate_commit_message():
    """Generate the commit message based on user input."""
    commit_type = choose_commit_type()
    scope = read_input(YELLOW + "Enter the scope (optional, press Enter to skip)" + RESET)

    while True:
        message = read_input(YELLOW + "Enter the commit message" + RESET)
        if message.strip():
            break

    commit_message = f"{commit_type}({scope}): {message}" if scope else f"{commit_type}: {message}"

    print(YELLOW + "Commit message:" + RESET)
    print(GREEN + commit_message + RESET)

    confirm = read_input(YELLOW + "Do you want to confirm this commit? (y/n)" + RESET).lower()
    if confirm != "y":
        print(RED + "Commit canceled." + RESET)
        return None

    return commit_message

def git_add():
    """Run 'git add' to stage changes."""
    try:
        subprocess.run(["git", "add", "."], capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        print(RED + "Error during 'git add':" + RESET)
        print(RED + error.stderr.decode() + RESET)
        sys.exit(1)
    except FileNotFoundError:
        print(RED + "Git is not installed. Please install Git and try again." + RESET)
        sys.exit(1)

def git_commit(commit_message):
    """Run 'git commit' with the provided message."""
    try:
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        print(GREEN + "New commit successfully made." + RESET)
    except subprocess.CalledProcessError:
        print(RED + "Error during 'git commit'" + RESET)
        sys.exit(1)

def git_push():
    """Run 'git push' to push changes."""
    try:
        subprocess.run(["git", "push"], check=True)
        print(GREEN + "Changes pushed." + RESET)
    except subprocess.CalledProcessError:
        print(RED + "Error during 'git push'" + RESET)
        sys.exit(1)

def check_and_notify_pre_commit():
    """Check for .pre-commit-config.yaml and notify if pre-commit is needed."""
    try:
        with open(".pre-commit-config.yaml"):
            try:
                if subprocess.run(["pre-commit", "--version"], check=True, capture_output=True):
                    subprocess.run(["pre-commit", "install"], check=True, capture_output=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                print(RED + "pre-commit is not installed." + RESET)
                sys.exit(1)
    except FileNotFoundError:
        pass

def main():
    """Main function to handle git operations and user input."""
    git_add()

    check_and_notify_pre_commit()

    commit_message = generate_commit_message()

    if commit_message:
        git_commit(commit_message)

        if read_input(YELLOW + "Do you want to push the changes? (y/n)" + RESET).lower() == "y":
            git_push()
        else:
            print(RED + "Push canceled." + RESET)

if __name__ == "__main__":
    main()
