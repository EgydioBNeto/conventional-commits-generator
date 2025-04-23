"""Core functionality for the Conventional Commits Generator."""

import sys
from typing import Optional, List, Dict

from ccg.utils import (
    COMMIT_TYPES, print_header, print_section, print_success,
    print_info, print_error, print_warning, read_input,
    BOLD, YELLOW, GREEN, RESET, WHITE, BULLET, TERM_WIDTH
)


def display_commit_types() -> None:
    """Display available commit types with explanations in a visually appealing format."""
    print_header("Commit Types")

    # Calculate max digits for index numbers
    max_idx_len = len(str(len(COMMIT_TYPES)))

    # Calculate max length of types for alignment
    max_type_len = max(len(commit_data["type"]) for commit_data in COMMIT_TYPES)

    # Print commit types in a visually appealing format with boxes
    for i, commit_data in enumerate(COMMIT_TYPES, start=1):
        color = commit_data.get("color", WHITE)
        symbol = commit_data.get("symbol", BULLET)

        idx = f"{i}.".ljust(max_idx_len + 1)
        commit_type = commit_data["type"].ljust(max_type_len)

        # Create a nice box around each type
        box_width = TERM_WIDTH - 8
        description = commit_data["description"]

        print(f"{idx} {color}{BOLD}{symbol} {commit_type}{RESET} - {description}")


def choose_commit_type() -> str:
    """Prompt the user to choose a commit type in a user-friendly manner.

    Returns:
        str: The selected commit type
    """
    display_commit_types()
    print()

    while True:
        try:
            user_input = read_input(
                f"{YELLOW}Choose the commit type (number or name){RESET}",
                history_type="type"
            )

            if not user_input:
                print_error("Input cannot be empty. Please select a valid option.")
                continue

            # Check if input is a number
            if user_input.isdigit() and 1 <= int(user_input) <= len(COMMIT_TYPES):
                commit_type = COMMIT_TYPES[int(user_input) - 1]["type"]
                print_success(f"Selected type: {BOLD}{commit_type}{RESET}")
                return commit_type

            # Check if input matches a commit type directly (case insensitive)
            for commit_data in COMMIT_TYPES:
                if user_input.lower() == commit_data["type"].lower():
                    print_success(f"Selected type: {BOLD}{commit_data['type']}{RESET}")
                    return commit_data["type"]

            print_error("Invalid choice. Please select a valid option.")
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            sys.exit(0)


def get_scope() -> Optional[str]:
    """Get the commit scope from user input with improved user experience.

    Returns:
        Optional[str]: The scope if provided, None otherwise
    """
    print_section("Scope")
    print_info("The scope provides context for the commit (e.g., module or file name)")
    print_info("Examples: auth, ui, api, database")

    scope = read_input(
        f"{YELLOW}Enter the scope (optional, press Enter to skip){RESET}",
        history_type="scope"
    )

    if scope:
        print_success(f"Scope set to: {BOLD}{scope}{RESET}")
    else:
        print_info("No scope provided")

    return scope if scope else None


def is_breaking_change() -> bool:
    """Check if the commit is a breaking change with improved user experience.

    Returns:
        bool: True if breaking change, False otherwise
    """
    print_section("Breaking Change")
    print_info("A breaking change means this commit includes incompatible changes")
    print_info("Examples: changing function signatures, removing features, etc.")

    while True:
        breaking = read_input(
            f"{YELLOW}Is this a BREAKING CHANGE? (y/n){RESET}"
        ).lower()

        if not breaking:
            print_warning("Please enter 'y' or 'n'")
            continue

        if breaking in ("y", "yes"):
            print_success(f"Marked as {BOLD}BREAKING CHANGE{RESET}")
            return True
        elif breaking in ("n", "no"):
            print_info("Not a breaking change")
            return False

        print_error("Invalid choice. Please enter 'y' or 'n'.")


def get_commit_message() -> str:
    """Get the commit message from user input with examples and guidance.

    Returns:
        str: The commit message
    """
    print_section("Commit Message")
    print_info("Provide a clear, concise description of the change")
    print_info("Examples: 'implement OAuth login', 'fix navigation bug', 'update documentation'")

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
    """Ask user to confirm the generated commit message with a visually appealing preview.

    Args:
        commit_message: The generated commit message

    Returns:
        bool: True if confirmed, False otherwise
    """
    print_section("Review")

    # Create a nice preview box
    box_width = min(len(commit_message) + 6, TERM_WIDTH - 4)

    print(f"{GREEN}┌{'─' * box_width}┐{RESET}")
    print(f"{GREEN}│{' ' * box_width}│{RESET}")
    print(f"{WHITE}│  {BOLD}{commit_message}{RESET}{WHITE}{' ' * (box_width - len(commit_message) - 2)}│{RESET}")
    print(f"{GREEN}│{' ' * box_width}│{RESET}")
    print(f"{GREEN}└{'─' * box_width}┘{RESET}")
    print()

    while True:
        confirm = read_input(f"{YELLOW}Confirm this commit message? (y/n){RESET}").lower()

        if not confirm:
            print_warning("Please enter 'y' or 'n'")
            continue

        if confirm in ("y", "yes"):
            print_success("Commit message confirmed!")
            return True
        elif confirm in ("n", "no"):
            return False

        print_error("Invalid choice. Please enter 'y' or 'n'.")


def confirm_push() -> bool:
    """Ask user to confirm push with improved user experience.

    Returns:
        bool: True if confirmed, False otherwise
    """
    print_section("Push Changes")
    print_info("You can push your changes to the remote repository")
    print_info("This will execute 'git push' command")

    while True:
        confirm = read_input(
            f"{YELLOW}Do you want to push these changes? (y/n){RESET}"
        ).lower()

        if not confirm:
            print_warning("Please enter 'y' or 'n'")
            continue

        if confirm in ("y", "yes"):
            print_info("Preparing to push changes...")
            return True
        elif confirm in ("n", "no"):
            print_info("Not pushing changes")
            return False

        print_error("Invalid choice. Please enter 'y' or 'n'.")


def generate_commit_message() -> Optional[str]:
    """Generate a conventional commit message based on user input.

    Returns:
        Optional[str]: The generated commit message if successful, None otherwise
    """
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
        if confirm_commit(commit_message):
            return commit_message

        print_error("Commit message rejected. Exiting.")
        return None

    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)

    return None
