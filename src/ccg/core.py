"""Core functionality for the Conventional Commits Generator."""

import sys
from typing import Optional, Tuple

from ccg.utils import (
    BOLD,
    BULLET,
    COMMIT_TYPES,
    CYAN,
    RESET,
    TERM_WIDTH,
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
    print_section("Commit Types")
    max_idx_len = len(str(len(COMMIT_TYPES)))
    max_type_len = max(len(commit_data["type"]) for commit_data in COMMIT_TYPES)

    for i, commit_data in enumerate(COMMIT_TYPES, start=1):
        color = commit_data.get("color", WHITE)
        emoji = commit_data.get("emoji", BULLET)
        description = commit_data["description"]
        idx = f"{i}.".ljust(max_idx_len + 1)
        commit_type = commit_data["type"].ljust(max_type_len)
        print(f"{idx} {color}{emoji}    {BOLD}{commit_type}{RESET} - {description}")


def choose_commit_type() -> str:
    display_commit_types()
    print()

    while True:
        try:
            user_input = read_input(
                f"{YELLOW}Choose the commit type (number or name){RESET}", history_type="type"
            )

            if not user_input:
                print_error("Input cannot be empty. Please select a valid option.")
                continue

            if user_input.isdigit() and 1 <= int(user_input) <= len(COMMIT_TYPES):
                commit_type = COMMIT_TYPES[int(user_input) - 1]["type"]
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
    print_section("Scope")
    print_info("The scope provides context for the commit (e.g., module or file name)")
    print_info("Examples: auth, ui, api, database")

    scope = read_input(
        f"{YELLOW}Enter the scope (optional, press Enter to skip){RESET}", history_type="scope"
    )

    if scope:
        print_success(f"Scope set to: {BOLD}{scope}{RESET}")
    else:
        print_info("No scope provided")

    return scope if scope else None


def is_breaking_change() -> bool:
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
    print_section("Emoji")
    print_info("GitHub-compatible emojis can make your commits more visual and expressive")
    print_info("Examples: :sparkles: feat, :bug: fix, :books: docs")

    return confirm_user_action(
        f"{YELLOW}Include emoji in commit message? (y/n){RESET}",
        success_message="Emoji will be included in the commit message",
        cancel_message="No emoji will be used",
    )


def get_commit_message() -> str:
    print_section("Commit Message")
    print_info("Provide a clear, concise description of the change")
    print_info("Examples: 'implement OAuth login', 'fix navigation bug', 'update documentation'")

    while True:
        message = read_input(f"{YELLOW}Enter the commit message{RESET}", history_type="message")
        if message.strip():
            print_success(f"Message: {BOLD}{message}{RESET}")
            return message
        print_error("Commit message cannot be empty.")


def get_commit_body() -> Optional[str]:
    print_section("Commit Body")
    print_info("Add implementation details, breaking changes, or issue references (optional)")
    print_info(
        "Examples: 'Added Google OAuth integration', 'BREAKING: API endpoint changed', 'Fixes #123'"
    )

    try:
        body = read_input(f"{YELLOW}Commit body{RESET}", history_type="body")

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


def convert_emoji_codes_to_real(text: str) -> str:
    emoji_map = {
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

    result = text
    for code, emoji in emoji_map.items():
        result = result.replace(code, emoji)
    return result


def get_visual_width(text: str) -> int:
    import unicodedata

    width = 0
    for char in text:
        eaw = unicodedata.east_asian_width(char)
        if eaw in ("F", "W"):
            width += 2
        elif eaw in ("H", "Na", "N"):
            width += 1
        else:
            width += 1
    return width


def confirm_commit(commit_message_header: str, commit_body: Optional[str] = None) -> bool:
    print_section("Review")

    # Display commit message with emoji conversion
    display_header = convert_emoji_codes_to_real(commit_message_header)
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
    print_section("Push Changes")
    print_info("This will execute 'git push' command")

    return confirm_user_action(
        f"{YELLOW}Do you want to push these changes? (y/n){RESET}",
        success_message=None,
        cancel_message="Not pushing changes",
    )


def validate_commit_message(message: str) -> Tuple[bool, Optional[str]]:
    if not message:
        return False, "Commit message cannot be empty."

    work_message = message.strip()

    if work_message.startswith(":"):
        emoji_end = work_message.find(":", 1)
        if emoji_end != -1:
            work_message = work_message[emoji_end + 1 :].strip()

    parts = work_message.split(":", 1)
    if len(parts) < 2:
        return False, "Invalid format. Expected: <type>[optional scope][optional !]: <description>"

    header, description = parts
    if not description.strip():
        return False, "Description cannot be empty after the colon."

    header_clean = header.strip()
    type_part = ""

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

    if type_part.endswith("!"):
        type_part = type_part[:-1]

    valid_types = [commit_data["type"] for commit_data in COMMIT_TYPES]
    if type_part not in valid_types:
        return False, f"Invalid commit type '{type_part}'. Valid types: {', '.join(valid_types)}"

    return True, None


def generate_commit_message() -> Optional[str]:
    try:
        commit_type = choose_commit_type()
        scope = get_scope()
        breaking_change = is_breaking_change()
        use_emoji = want_emoji()
        message = get_commit_message()
        body = get_commit_body()

        breaking_indicator = "!" if breaking_change else ""
        scope_part = f"({scope})" if scope else ""

        if use_emoji:
            emoji = get_emoji_for_type(commit_type, use_code=True)
            type_part = f"{emoji} {commit_type}" if emoji else commit_type
        else:
            type_part = commit_type

        header = f"{type_part}{scope_part}{breaking_indicator}: {message}"
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
