"""Core functionality for the Conventional Commits Generator."""

import sys
from typing import Optional

from ccg.utils import (
    COMMIT_TYPES, print_header, print_section, print_success,
    print_info, print_error, read_input, BOLD, YELLOW, GREEN, RESET, WHITE, BULLET
)


def display_commit_types() -> None:
    """Display available commit types with explanations."""
    print_header("Commit Types")

    # Calculate max digits for index numbers
    max_idx_len = len(str(len(COMMIT_TYPES)))

    # Calculate max length of types for alignment
    max_type_len = max(len(commit_data["type"]) for commit_data in COMMIT_TYPES)

    # Print commit types in a nice format
    for i, commit_data in enumerate(COMMIT_TYPES, start=1):
        color = commit_data.get("color", WHITE)
        symbol = commit_data.get("symbol", BULLET)

        idx = f"{i}.".ljust(max_idx_len + 1)
        commit_type = commit_data["type"].ljust(max_type_len)

        print(
            f"{idx} {color}{BOLD}{symbol} {commit_type}{RESET} - {commit_data['description']}"
        )


def choose_commit_type() -> str:
    """Prompt the user to choose a commit type.

    Returns:
        str: The selected commit type
    """
    display_commit_types()
    print()

    while True:
        try:
            user_input = read_input(
                f"{YELLOW}Choose the commit type{RESET}",
                history_type="type"
            )

            # Check if input is a number
            if user_input.isdigit() and 1 <= int(user_input) <= len(COMMIT_TYPES):
                commit_type = COMMIT_TYPES[int(user_input) - 1]["type"]
                print_success(f"Selected type: {BOLD}{commit_type}{RESET}")
                return commit_type

            # Check if input matches a commit type directly
            for commit_data in COMMIT_TYPES:
                if user_input.lower() == commit_data["type"].lower():
                    print_success(f"Selected type: {BOLD}{commit_data['type']}{RESET}")
                    return commit_data["type"]

            print_error("Invalid choice. Please select a valid option.")
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            sys.exit(0)


def get_scope() -> Optional[str]:
    """Get the commit scope from user input.

    Returns:
        Optional[str]: The scope if provided, None otherwise
    """
    print_section("Scope")
    print_info("The scope provides context for the commit (e.g., module or file name)")
    scope = read_input(
        f"{YELLOW}Enter the scope (optional){RESET}",
        history_type="scope"
    )

    if scope:
        print_success(f"Scope set to: {BOLD}{scope}{RESET}")
    else:
        print_info("No scope provided")

    return scope if scope else None


def is_breaking_change() -> bool:
    """Check if the commit is a breaking change.

    Returns:
        bool: True if breaking change, False otherwise
    """
    print_section("Breaking Change")
    print_info("A breaking change means this commit includes incompatible API changes")

    while True:
        breaking = read_input(
            f"{YELLOW}Is this a BREAKING CHANGE? (y/n){RESET}"
        ).lower()
        if breaking in ("y", "n"):
            if breaking == "y":
                print_success(f"Marked as {BOLD}BREAKING CHANGE{RESET}")
            else:
                print_info("Not a breaking change")
            return breaking == "y"
        print_error("Invalid choice. Please enter 'y' or 'n'.")


def get_commit_message() -> str:
    """Get the commit message from user input.

    Returns:
        str: The commit message
    """
    print_section("Commit Message")
    print_info("Provide a clear, concise description of the change")

    while True:
        message = read_input(
            f"{YELLOW}Enter the commit message{RESET}",
            history_type="message"
        )
        if message.strip():
            print_success(f"Message: {BOLD}{message}{RESET}")
            return message
        print_error("Commit message cannot be empty.")


def confirm_commit(commit_message: str) -> bool:
    """Ask user to confirm the generated commit message.

    Args:
        commit_message: The generated commit message

    Returns:
        bool: True if confirmed, False otherwise
    """
    print_section("Review")
    print(f"{GREEN}Your commit message:{RESET}")
    print()
    print(f"{GREEN}{BOLD}{commit_message}{RESET}")
    print()

    while True:
        confirm = read_input(f"{YELLOW}Confirm this commit? (y/n){RESET}").lower()
        if confirm == "y":
            print_success("Commit message confirmed!")
            return True
        elif confirm == "n":
            return False
        print_error("Invalid choice. Please enter 'y' or 'n'.")


def confirm_push() -> bool:
    """Ask user to confirm push.

    Returns:
        bool: True if confirmed, False otherwise
    """
    print_section("Push Changes")
    print_info("You can push your changes to the remote repository")

    confirm = read_input(
        f"{YELLOW}Do you want to push these changes? (y/n){RESET}"
    ).lower()

    if confirm == "y":
        print_info("Preparing to push changes...")
    else:
        print_info("Not pushing changes")

    return confirm == "y"


def generate_commit_message() -> Optional[str]:
    """Generate a conventional commit message based on user input.

    Returns:
        Optional[str]: The generated commit message if successful, None otherwise
    """
    try:
        print_header("Conventional Commit Generator")

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
        if confirm_commit(commit_message):
            return commit_message

        print("\nExiting. Goodbye!")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)

    return None
