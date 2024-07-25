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

    while True:
        try:
            print(YELLOW + "Choose the commit type:" + RESET)
            for i, commit_type_explanation in enumerate(
                commit_types_explanation, start=1):
                print(f"{i}. {commit_type_explanation}")

            user_input = read_input(
                YELLOW + "Choose the commit type or enter directly " +
                "(e.g., feat, fix, chore):" + RESET
            )

            # Check if the user input is a number
            if user_input.isdigit() and 1 <= int(user_input) <= len(
                commit_types_explanation):
                commit_type = commit_types_explanation[
                    int(user_input) - 1].split()[0]
            elif user_input.lower() in [
                ct.split()[0].lower() for ct in commit_types_explanation]:
                commit_type = user_input.lower()
            else:
                print(RED + "Invalid choice." + RESET)
                continue

            if commit_type.strip():
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

def main():
    """Main function to handle git operations and user input."""
    try:
        subprocess.run(["git", "add", "."], capture_output=True, check=True)
    except subprocess.CalledProcessError as error:
        print(RED + error.stderr.decode() + RESET)
        sys.exit(1)
    except FileNotFoundError:
        print(RED + "Git is not installed. Please install Git and try again." + RESET)
        sys.exit(1)

    commit_message = generate_commit_message()

    if commit_message:
        try:
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            print(GREEN + "New commit successfully made." + RESET)

            push = read_input(YELLOW + "Do you want to push the changes? (y/n)" + RESET).lower()
            if push == "y":
                try:
                    subprocess.run(["git", "push"], check=True)
                    print(GREEN + "Changes pushed to the repository." + RESET)
                except subprocess.CalledProcessError as error:
                    print(RED + error.stderr.decode() + RESET)
            else:
                print(RED + "Push canceled." + RESET)
        except subprocess.CalledProcessError as error:
            print(RED + error.stderr.decode() + RESET)

if __name__ == "__main__":
    main()
