"""Input validators for the Conventional Commits Generator."""

from typing import Optional, Tuple

from ..common.config import COMMIT_TYPES, ERROR_MESSAGES


def validate_confirmation_input(user_input: str) -> Optional[bool]:
    """Validate user confirmation input (y/n)."""
    if not user_input or len(user_input) > 3:
        return None

    normalized = user_input.lower().strip()
    if normalized in ["y", "yes"]:
        return True
    elif normalized in ["n", "no"]:
        return False
    else:
        return None


def validate_commit_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate conventional commit message format and content.

    Ensures the commit message follows conventional commit standards
    with proper type, optional scope, and descriptive message content.
    Also allows non-conventional commit messages with special suffixes like [skip-release].

    Args:
        message: Commit message to validate

    Returns:
        Tuple of (is_valid, error_message_or_None)

    Example:
        valid, error = validate_commit_message("feat(auth): add login")
        if not valid:
            print(f"Invalid commit: {error}")
    """
    if not message:
        return False, ERROR_MESSAGES["EMPTY_COMMIT_MESSAGE"]

    work_message = message.strip()

    # Allow messages with [skip-release] or similar patterns (non-conventional commits)
    if "[skip-release]" in work_message or work_message.startswith(
        ("Update ", "Create ", "Delete ", "Add ", "Remove ", "Fix ", "Merge ")
    ):
        # These are valid Git commit messages that don't need to follow conventional commit format
        return True, None

    # Handle emoji prefix
    if work_message.startswith(":"):
        emoji_end = work_message.find(":", 1)
        if emoji_end != -1:
            work_message = work_message[emoji_end + 1 :].strip()

    # Split by colon
    parts = work_message.split(":", 1)
    if len(parts) < 2:
        return False, "Invalid format. Expected: <type>[optional scope][optional !]: <description>"

    header, description = parts
    if not description.strip():
        return False, "Description cannot be empty after the colon."

    header_clean = header.strip()
    type_part = ""

    # Handle scope in parentheses
    if "(" in header_clean and ")" in header_clean:
        paren_start = header_clean.find("(")
        paren_end = header_clean.find(")", paren_start)

        if paren_end == -1:
            return (
                False,
                "Scope opening parenthesis without closing: use format <type>(<scope>): or <type>(<scope>)!:",
            )

        type_part = header_clean[:paren_start]
        after_scope = header_clean[paren_end + 1 :]
        if after_scope and after_scope != "!":
            return (
                False,
                "Invalid characters after scope. Expected nothing or '!' for breaking change.",
            )
    else:
        type_part = header_clean

    # Handle breaking change indicator
    if type_part.endswith("!"):
        type_part = type_part[:-1]

    # Validate commit type
    valid_types = [commit_data["type"] for commit_data in COMMIT_TYPES]
    if type_part not in valid_types:
        return False, f"Invalid commit type '{type_part}'. Valid types: {', '.join(valid_types)}"

    return True, None


def validate_character_limit(text: str, max_length: int) -> Tuple[bool, Optional[str]]:
    """Validate text against character limit."""
    if len(text) > max_length:
        return False, ERROR_MESSAGES["CHARACTER_LIMIT_EXCEEDED"].format(
            current=len(text), max=max_length
        )
    return True, None
