"""Core functionality for the Conventional Commits Generator."""

import sys
from typing import Optional, Tuple

from ..common.config import COLORS, COMMIT_TYPES, SYMBOLS
from ..common.helpers import convert_emoji_codes_to_real, get_emoji_for_type, get_visual_width
from ..ui.display import (
    format_commit_message_box,
    print_error,
    print_info,
    print_section,
    print_success,
)
from ..ui.input import confirm_user_action, read_input
from ..ui.validation import validate_commit_message


def display_commit_types() -> None:
    """Display available commit types in a formatted list."""
    print_section("Commit Types")
    max_idx_len = len(str(len(COMMIT_TYPES)))
    max_type_len = max(len(commit_data["type"]) for commit_data in COMMIT_TYPES)

    for i, commit_data in enumerate(COMMIT_TYPES, start=1):
        color = commit_data.get("color", COLORS["WHITE"])
        emoji = commit_data.get("emoji", SYMBOLS["BULLET"])
        description = commit_data["description"]
        idx = f"{i}.".ljust(max_idx_len + 1)
        commit_type = commit_data["type"].ljust(max_type_len)
        print(
            f"{idx} {color}{emoji}    {COLORS['BOLD']}{commit_type}{COLORS['RESET']} - {description}"
        )


def _validate_commit_type_selection(user_input: str) -> Optional[str]:
    """Validate and return commit type from user input."""
    if not user_input:
        return None

    # Check if input is a number
    if user_input.isdigit() and 1 <= int(user_input) <= len(COMMIT_TYPES):
        return COMMIT_TYPES[int(user_input) - 1]["type"]

    # Check if input matches a commit type name
    for commit_data in COMMIT_TYPES:
        if user_input.lower() == commit_data["type"].lower():
            return commit_data["type"]

    return None


def choose_commit_type() -> str:
    """Interactive commit type selection."""
    display_commit_types()

    while True:
        try:
            user_input = read_input(
                f"{COLORS['YELLOW']}Choose the commit type (number or name){COLORS['RESET']}",
                history_type="type",
            )

            if not user_input:
                print_error("Input cannot be empty. Please select a valid option.")
                continue

            commit_type = _validate_commit_type_selection(user_input)
            if commit_type:
                print_success(f"Selected type: {COLORS['BOLD']}{commit_type}{COLORS['RESET']}")
                return commit_type

            print_error("Invalid choice. Please select a valid option.")
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            sys.exit(0)


def get_scope() -> Optional[str]:
    """Interactive scope input."""
    print_section("Scope")
    print_info("The scope provides context for the commit (e.g., module or file name)")
    print_info("Examples: auth, ui, api, database")

    scope = read_input(
        f"{COLORS['YELLOW']}Enter the scope (optional, press Enter to skip){COLORS['RESET']}",
        history_type="scope",
    )

    if scope:
        print_success(f"Scope set to: {COLORS['BOLD']}{scope}{COLORS['RESET']}")
    else:
        print_info("No scope provided")

    return scope if scope else None


def is_breaking_change() -> bool:
    """Interactive breaking change confirmation."""
    print_section("Breaking Change")
    print_info("A breaking change means this commit includes incompatible changes")
    print_info("Examples: changing function signatures, removing features, etc.")

    return confirm_user_action(
        f"{COLORS['YELLOW']}Is this a BREAKING CHANGE? [y/N]{COLORS['RESET']}",
        success_message=f"Marked as {COLORS['BOLD']}BREAKING CHANGE{COLORS['RESET']}",
        cancel_message="Not a breaking change",
    )


def want_emoji() -> bool:
    """Interactive emoji preference selection."""
    print_section("Emoji")
    print_info("GitHub-compatible emojis can make your commits more visual and expressive")
    print_info("Examples: :sparkles: feat, :bug: fix, :books: docs")

    return confirm_user_action(
        f"{COLORS['YELLOW']}Include emoji in commit message? [Y/n]{COLORS['RESET']}",
        success_message="Emoji will be included in the commit message",
        cancel_message="No emoji will be used",
    )


def get_commit_message() -> str:
    """Interactive commit message input."""
    print_section("Commit Message")
    print_info("Provide a clear, concise description of the change")
    print_info("Examples: 'implement OAuth login', 'fix navigation bug', 'update documentation'")

    while True:
        message = read_input(
            f"{COLORS['YELLOW']}Enter the commit message{COLORS['RESET']}", history_type="message"
        )
        if message.strip():
            print_success(f"Message: {COLORS['BOLD']}{message}{COLORS['RESET']}")
            return message
        print_error("Commit message cannot be empty.")


def get_commit_body() -> Optional[str]:
    """Interactive commit body input."""
    print_section("Commit Body")
    print_info("Add implementation details, breaking changes, or issue references (optional)")
    print_info(
        "Examples: 'Added Google OAuth integration', 'BREAKING: API endpoint changed', 'Fixes #123'"
    )

    try:
        body = read_input(f"{COLORS['YELLOW']}Commit body{COLORS['RESET']}", history_type="body")

        if body and body.strip():
            word_count = len(body.split())
            line_count = len(body.split("\n"))
            char_count = len(body)
            print_success(
                f"Body added: {line_count} line(s), {word_count} word(s), {char_count} characters"
            )
            return body
        else:
            print_info("No body provided")
            return None

    except KeyboardInterrupt:
        print("\nSkipping commit body...")
        return None


def confirm_commit(commit_message_header: str, commit_body: Optional[str] = None) -> bool:
    """Interactive commit message confirmation."""
    print_section("Review")
    format_commit_message_box(commit_message_header, commit_body)

    return confirm_user_action(
        f"{COLORS['YELLOW']}Confirm this commit message? [Y/n]{COLORS['RESET']}",
        success_message="Commit message confirmed!",
        cancel_message=None,
    )


def confirm_push() -> bool:
    """Interactive push confirmation."""
    from ..git.operations import get_current_branch
    from ..ui.display import print_error, print_info

    # Check if we're in detached HEAD state
    branch_name = get_current_branch()
    if branch_name and branch_name.startswith("HEAD-"):
        print_section("Push Changes")
        print_error("Cannot push from detached HEAD state.")
        print_info("Please create and checkout a branch first: git checkout -b <branch-name>")
        return False

    print_section("Push Changes")
    print_info("This will execute 'git push' command")

    return confirm_user_action(
        f"{COLORS['YELLOW']}Do you want to push these changes? [Y/n]{COLORS['RESET']}",
        success_message=None,
        cancel_message="Not pushing changes",
    )


def _build_commit_header(
    commit_type: str, scope: Optional[str], breaking_change: bool, use_emoji: bool, message: str
) -> str:
    """Build the commit message header."""
    breaking_indicator = "!" if breaking_change else ""
    scope_part = f"({scope})" if scope else ""

    if use_emoji:
        emoji = get_emoji_for_type(commit_type, use_code=True)
        type_part = f"{emoji} {commit_type}" if emoji else commit_type
    else:
        type_part = commit_type

    return f"{type_part}{scope_part}{breaking_indicator}: {message}"


def generate_commit_message() -> Optional[str]:
    """Generate a conventional commit message through interactive prompts."""
    try:
        commit_type = choose_commit_type()
        scope = get_scope()
        breaking_change = is_breaking_change()
        use_emoji = want_emoji()
        message = get_commit_message()
        body = get_commit_body()

        header = _build_commit_header(commit_type, scope, breaking_change, use_emoji, message)
        full_commit_message = header
        if body:
            full_commit_message += f"\n\n{body}"

        if confirm_commit(header, body):
            return full_commit_message

        print_error("Commit message rejected. Exiting.")
        return None

    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)

    return None
