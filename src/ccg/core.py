"""Core functionality for the Conventional Commits Generator."""

import sys
from typing import Dict, List, Optional, Tuple

from ccg.utils import (
    BOLD,
    BULLET,
    COMMIT_TYPES,
    CYAN,
    RESET,
    WHITE,
    YELLOW,
    confirm_user_action,
    get_emoji_for_type,
    print_error,
    print_info,
    print_section,
    print_success,
    read_input,
)


def display_commit_types() -> None:
    """Display available commit types with colors and emojis.

    Shows a formatted list of all conventional commit types with their
    corresponding emojis, colors, and descriptions.

    Examples:
        >>> display_commit_types()
        ┌──────────────────────┐
        │ Commit Types         │
        └──────────────────────┘
        1. ✨ feat     - A new feature
        2. 🐛 fix      - A bug fix
        ...
    """
    print_section("Commit Types")
    max_idx_len: int = len(str(len(COMMIT_TYPES)))
    max_type_len: int = max(len(commit_data["type"]) for commit_data in COMMIT_TYPES)

    for i, commit_data in enumerate(COMMIT_TYPES, start=1):
        color: str = commit_data.get("color", WHITE)
        emoji: str = commit_data.get("emoji", BULLET)
        description: str = commit_data["description"]
        idx: str = f"{i}.".ljust(max_idx_len + 1)
        commit_type: str = commit_data["type"].ljust(max_type_len)
        print(f"{idx} {color}{emoji}    {BOLD}{commit_type}{RESET} - {description}")


def choose_commit_type() -> str:
    """Interactively choose a commit type from available options.

    Displays all commit types and prompts user to select one either by
    number (1-11) or by type name (e.g., 'feat', 'fix').

    Returns:
        str: Selected commit type (e.g., 'feat', 'fix', 'chore')

    Raises:
        SystemExit: If user interrupts with Ctrl+C

    Examples:
        >>> choose_commit_type()
        Choose the commit type (number or name): 1
        Selected type: feat
        'feat'

        >>> choose_commit_type()
        Choose the commit type (number or name): fix
        Selected type: fix
        'fix'
    """
    display_commit_types()
    print()

    while True:
        try:
            user_input: str = read_input(
                f"{YELLOW}Choose the commit type (number or name){RESET}",
                history_type="type",
            )

            if not user_input:
                print_error("Input cannot be empty. Please select a valid option.")
                continue

            if user_input.isdigit() and 1 <= int(user_input) <= len(COMMIT_TYPES):
                commit_type: str = COMMIT_TYPES[int(user_input) - 1]["type"]
                print_success(f"Selected type: {BOLD}{commit_type}{RESET}")
                return commit_type

            for commit_data in COMMIT_TYPES:
                if user_input.lower() == commit_data["type"].lower():
                    print_success(f"Selected type: {BOLD}{commit_data['type']}{RESET}")
                    return commit_data["type"]

            print_error("Invalid choice. Please select a valid option.")
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            sys.exit(0)


def get_scope() -> Optional[str]:
    """Get optional scope for the commit.

    Prompts user to enter a scope (e.g., module, component, or file name)
    that provides additional context for the commit.

    Returns:
        Optional[str]: Scope string if provided, None otherwise

    Examples:
        >>> get_scope()
        Enter the scope (optional, press Enter to skip): auth
        Scope set to: auth
        'auth'

        >>> get_scope()
        Enter the scope (optional, press Enter to skip):
        No scope provided
        None
    """
    print_section("Scope")
    print_info("The scope provides context for the commit (e.g., module or file name)")
    print_info("Examples: auth, ui, api, database")

    scope: str = read_input(
        f"{YELLOW}Enter the scope (optional, press Enter to skip){RESET}",
        history_type="scope",
    )

    if scope:
        print_success(f"Scope set to: {BOLD}{scope}{RESET}")
    else:
        print_info("No scope provided")

    return scope if scope else None


def is_breaking_change() -> bool:
    """Ask if commit contains breaking changes.

    Prompts user to indicate whether this commit introduces breaking changes
    that are incompatible with previous versions.

    Returns:
        bool: True if breaking change, False otherwise

    Examples:
        >>> is_breaking_change()
        Is this a BREAKING CHANGE? (y/N): y
        Marked as BREAKING CHANGE
        True

        >>> is_breaking_change()
        Is this a BREAKING CHANGE? (y/N): n
        Not a breaking change
        False
    """
    print_section("Breaking Change")
    print_info("A breaking change means this commit includes incompatible changes")
    print_info("Examples: changing function signatures, removing features, etc.")

    return confirm_user_action(
        f"{YELLOW}Is this a BREAKING CHANGE? (y/n){RESET}",
        success_message=f"Marked as {BOLD}BREAKING CHANGE{RESET}",
        cancel_message="Not a breaking change",
        default_yes=False,
    )


def want_emoji() -> bool:
    """Ask if user wants to include emoji in commit message.

    Prompts user to decide whether to include GitHub-compatible emoji codes
    in the commit message for better visual representation.

    Returns:
        bool: True if emoji should be included, False otherwise

    Examples:
        >>> want_emoji()
        Include emoji in commit message? (Y/n): y
        Emoji will be included in the commit message
        True

        >>> want_emoji()
        Include emoji in commit message? (Y/n): n
        No emoji will be used
        False
    """
    print_section("Emoji")
    print_info("GitHub-compatible emojis can make your commits more visual and expressive")
    print_info("Examples: :sparkles: feat, :bug: fix, :books: docs")

    return confirm_user_action(
        f"{YELLOW}Include emoji in commit message? (y/n){RESET}",
        success_message="Emoji will be included in the commit message",
        cancel_message="No emoji will be used",
    )


def get_commit_message() -> str:
    """Get the main commit message from user.

    Prompts user to enter a clear, concise description of the change.
    Validates that the message is not empty.

    Returns:
        str: Commit message description

    Examples:
        >>> get_commit_message()
        Enter the commit message: implement OAuth login
        Message: implement OAuth login
        'implement OAuth login'

        >>> get_commit_message()
        Enter the commit message:
        Commit message cannot be empty.
        Enter the commit message: fix navigation bug
        Message: fix navigation bug
        'fix navigation bug'
    """
    print_section("Commit Message")
    print_info("Provide a clear, concise description of the change")
    print_info("Examples: 'implement OAuth login', 'fix navigation bug', 'update documentation'")

    while True:
        message: str = read_input(
            f"{YELLOW}Enter the commit message{RESET}", history_type="message"
        )
        if message.strip():
            print_success(f"Message: {BOLD}{message}{RESET}")
            return message
        print_error("Commit message cannot be empty.")


def get_commit_body() -> Optional[str]:
    """Get optional commit body with additional details.

    Prompts user to enter optional additional information such as
    implementation details, breaking changes, or issue references.

    Returns:
        Optional[str]: Commit body if provided, None otherwise

    Examples:
        >>> get_commit_body()
        Commit body (optional): Added Google OAuth integration
        Fixes #123
        Body added: 2 line(s), 5 word(s), 45 characters
        'Added Google OAuth integration\\nFixes #123'

        >>> get_commit_body()
        Commit body (optional):
        No body provided
        None
    """
    print_section("Commit Body")
    print_info("Add implementation details, breaking changes, or issue references (optional)")
    print_info(
        "Examples: 'Added Google OAuth integration', 'BREAKING: API endpoint changed', 'Fixes #123'"
    )

    try:
        body: str = read_input(f"{YELLOW}Commit body{RESET}", history_type="body")

        if body and body.strip():
            word_count: int = len(body.split())
            line_count: int = len(body.split("\n"))
            char_count: int = len(body)
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


def convert_emoji_codes_to_real(text: str) -> str:
    """Convert emoji codes to actual emoji characters.

    Replaces GitHub-compatible emoji codes (e.g., :sparkles:) with their
    corresponding Unicode emoji characters for display.

    Args:
        text: Text containing emoji codes

    Returns:
        str: Text with emoji codes replaced by actual emojis

    Examples:
        >>> convert_emoji_codes_to_real(":sparkles: feat: new feature")
        '✨ feat: new feature'

        >>> convert_emoji_codes_to_real(":bug: fix: resolve bug")
        '🐛 fix: resolve bug'

        >>> convert_emoji_codes_to_real("feat: no emoji")
        'feat: no emoji'
    """
    emoji_map: Dict[str, str] = {
        ":sparkles:": "✨",
        ":bug:": "🐛",
        ":wrench:": "🔧",
        ":hammer:": "🔨",
        ":lipstick:": "💄",
        ":books:": "📚",
        ":test_tube:": "🧪",
        ":package:": "📦",
        ":rewind:": "⏪",
        ":construction_worker:": "👷",
        ":zap:": "⚡",
    }

    result: str = text
    for code, emoji in emoji_map.items():
        result = result.replace(code, emoji)
    return result


def get_visual_width(text: str) -> int:
    """Calculate visual width of text accounting for wide characters.

    Calculates the display width of text by considering East Asian Width
    property of Unicode characters. Wide and fullwidth characters count as 2.

    Args:
        text: Text to measure

    Returns:
        int: Visual width of the text

    Examples:
        >>> get_visual_width("hello")
        5

        >>> get_visual_width("你好")  # Chinese characters are wide
        4

        >>> get_visual_width("hello 你好")
        9
    """
    import unicodedata

    width: int = 0
    for char in text:
        eaw: str = unicodedata.east_asian_width(char)
        if eaw in ("F", "W"):
            width += 2
        elif eaw in ("H", "Na", "N"):
            width += 1
        else:
            width += 1
    return width


def confirm_commit(commit_message_header: str, commit_body: Optional[str] = None) -> bool:
    """Display commit preview and ask for confirmation.

    Shows the formatted commit message with emoji conversion and optional
    body, then prompts user to confirm before proceeding.

    Args:
        commit_message_header: Main commit message header
        commit_body: Optional commit body with additional details

    Returns:
        bool: True if confirmed, False otherwise

    Examples:
        >>> confirm_commit("feat(auth): add login", "Implements OAuth 2.0")
        ┌──────────────────────┐
        │ Review               │
        └──────────────────────┘
        Commit: feat(auth): add login

        Body:
        Implements OAuth 2.0

        Confirm this commit message? (Y/n): y
        True
    """
    print_section("Review")

    # Display commit message with emoji conversion
    display_header: str = convert_emoji_codes_to_real(commit_message_header)
    print(f"{CYAN}Commit:{RESET} {BOLD}{display_header}{RESET}")

    # Display body if present
    if commit_body:
        print()
        print(f"{CYAN}Body:{RESET}")
        for line in commit_body.split("\n"):
            print(line)

    print()
    return confirm_user_action(
        f"{YELLOW}Confirm this commit message? (y/n){RESET}",
        success_message="Commit message confirmed!",
        cancel_message=None,
    )


def confirm_push() -> bool:
    """Ask user if they want to push changes to remote.

    Prompts user to confirm whether to execute 'git push' command
    after creating the commit.

    Returns:
        bool: True if user wants to push, False otherwise

    Examples:
        >>> confirm_push()
        ┌──────────────────────┐
        │ Push Changes         │
        └──────────────────────┘
        This will execute 'git push' command
        Do you want to push these changes? (Y/n): y
        True
    """
    print_section("Push Changes")
    print_info("This will execute 'git push' command")

    return confirm_user_action(
        f"{YELLOW}Do you want to push these changes? (y/n){RESET}",
        success_message=None,
        cancel_message="Not pushing changes",
    )


def validate_commit_message(message: str) -> Tuple[bool, Optional[str]]:
    """Validate commit message against Conventional Commits format.

    Verifies that the message follows the pattern:
    [emoji_code] <type>[optional scope][optional !]: <description>

    Args:
        message: Commit message to validate

    Returns:
        Tuple containing:
        - bool: True if valid, False otherwise
        - Optional[str]: Error message if invalid, None if valid

    Examples:
        >>> validate_commit_message("feat: add new feature")
        (True, None)

        >>> validate_commit_message("feat(auth): add login")
        (True, None)

        >>> validate_commit_message("feat!: breaking change")
        (True, None)

        >>> validate_commit_message(":sparkles: feat: new feature")
        (True, None)

        >>> validate_commit_message("invalid message")
        (False, 'Invalid format. Expected: <type>[optional scope][optional !]: <description>')

        >>> validate_commit_message("invalid: message")
        (False, "Invalid commit type 'invalid'. Valid types: ...")

    Note:
        Valid types: feat, fix, chore, refactor, style, docs, test,
        build, revert, ci, perf
    """
    if not message:
        return False, "Commit message cannot be empty."

    work_message: str = message.strip()

    # Strip emoji code if present
    if work_message.startswith(":"):
        emoji_end: int = work_message.find(":", 1)
        if emoji_end != -1:
            work_message = work_message[emoji_end + 1 :].strip()

    # Split into header and description
    parts: List[str] = work_message.split(":", 1)
    if len(parts) < 2:
        return (
            False,
            "Invalid format. Expected: <type>[optional scope][optional !]: <description>",
        )

    header: str
    description: str
    header, description = parts
    if not description.strip():
        return False, "Description cannot be empty after the colon."

    header_clean: str = header.strip()
    type_part: str = ""

    # Extract type and scope
    if "(" in header_clean and ")" in header_clean:
        paren_start: int = header_clean.find("(")
        paren_end: int = header_clean.find(")", paren_start)

        if paren_end == -1:
            return (
                False,
                "Scope opening parenthesis without closing: use format <type>(<scope>): or <type>(<scope>)!:",
            )

        type_part = header_clean[:paren_start]
        after_scope: str = header_clean[paren_end + 1 :]
        if after_scope and after_scope != "!":
            return (
                False,
                "Invalid characters after scope. Expected nothing or '!' for breaking change.",
            )
    else:
        type_part = header_clean

    # Remove breaking change indicator
    if type_part.endswith("!"):
        type_part = type_part[:-1]

    # Validate commit type
    valid_types: List[str] = [commit_data["type"] for commit_data in COMMIT_TYPES]
    if type_part not in valid_types:
        return (
            False,
            f"Invalid commit type '{type_part}'. Valid types: {', '.join(valid_types)}",
        )

    return True, None


def generate_commit_message() -> Optional[str]:
    """Generate a complete conventional commit message interactively.

    Orchestrates the entire workflow of creating a conventional commit message:
    1. Choose commit type
    2. Enter optional scope
    3. Indicate breaking change
    4. Choose emoji inclusion
    5. Enter commit message
    6. Enter optional body
    7. Confirm the complete message

    Returns:
        Optional[str]: Complete commit message if confirmed, None if cancelled

    Raises:
        SystemExit: If user interrupts with Ctrl+C

    Examples:
        >>> generate_commit_message()
        # ... interactive prompts ...
        ':sparkles: feat(auth): implement OAuth login\\n\\nAdded Google OAuth 2.0 support'

        >>> generate_commit_message()
        # ... user cancels ...
        None
    """
    try:
        commit_type: str = choose_commit_type()
        scope: Optional[str] = get_scope()
        breaking_change: bool = is_breaking_change()
        use_emoji: bool = want_emoji()
        message: str = get_commit_message()
        body: Optional[str] = get_commit_body()

        breaking_indicator: str = "!" if breaking_change else ""
        scope_part: str = f"({scope})" if scope else ""

        type_part: str
        if use_emoji:
            emoji: str = get_emoji_for_type(commit_type, use_code=True)
            type_part = f"{emoji} {commit_type}" if emoji else commit_type
        else:
            type_part = commit_type

        header: str = f"{type_part}{scope_part}{breaking_indicator}: {message}"
        full_commit_message: str = header
        if body:
            full_commit_message += f"\n\n{body}"

        if confirm_commit(header, body):
            return full_commit_message

        print_error("Commit message rejected. Exiting.")
        return None

    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)
