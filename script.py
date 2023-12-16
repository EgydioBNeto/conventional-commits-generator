#!/usr/bin/env python3

import subprocess

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def read_input(prompt):
    return input(f"{prompt}: ").strip()

def choose_commit_type():
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
        # Choose commit type
        print(YELLOW + "Choose the commit type:" + RESET)
        for i, commit_type_explanation in enumerate(commit_types_explanation, start=1):
            print(f"{i}. {commit_type_explanation}")

        user_input = read_input(YELLOW + "Choose the commit type or enter directly (e.g., feat, fix, chore):" + RESET)

        # Check if the user input is a number
        if user_input.isdigit() and 1 <= int(user_input) <= len(commit_types_explanation):
            commit_type = commit_types_explanation[int(user_input) - 1].split()[0]
        elif user_input.lower() in [ct.split()[0].lower() for ct in commit_types_explanation]:
            commit_type = user_input.lower()
        else:
            print(RED + "Invalid choice." + RESET)
            continue

        # Validate if the commit type is not empty
        if commit_type.strip():
            return commit_type
        else:
            print(RED + "Invalid choice. Commit type cannot be empty." + RESET)


def generate_commit_message():
    commit_type = choose_commit_type()

    # Choose scope
    scope = read_input(YELLOW + "Enter the scope (optional, press Enter to skip)" + RESET)

    # Commit message
    while True:
        message = read_input(YELLOW + "Enter the commit message" + RESET)

        # Validate if the message is not empty
        if message.strip():
            break
        else:
            print(RED + "Commit message cannot be empty. Please enter a valid message." + RESET)

    # Build commit message in conventional format
    if scope:
        commit_message = f"{commit_type}({scope}): {message}"
    else:
        commit_message = f"{commit_type}: {message}"

    # Display commit message
    print(YELLOW + "Commit message:" + RESET)
    print(GREEN + commit_message + RESET)

    # Confirm if the user really wants to commit
    confirm = read_input(YELLOW + "Do you want to confirm this commit? (y/n)" + RESET).lower()
    if confirm != "y":
        print(RED + "Commit canceled." + RESET)
        return None

    return commit_message


def main():
    commit_message = generate_commit_message()

    if commit_message:
        # Commit changes
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", commit_message])
        print(GREEN + "New commit successfully made, push to the repository" + RESET)


if __name__ == "__main__":
    main()
