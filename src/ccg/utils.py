"""Utilities and styling for the Conventional Commits Generator."""

import os
import shutil
import sys
from typing import Dict, List, Optional

ASCII_LOGO = r"""
 ________      ________      ________
|\   ____\    |\   ____\    |\   ____\
\ \  \___|    \ \  \___|    \ \  \___|
 \ \  \        \ \  \        \ \  \  ___
  \ \  \____    \ \  \____    \ \  \|\  \
   \ \_______\   \ \_______\   \ \_______\
    \|_______|    \|_______|    \|_______|

 Conventional Commits Generator
"""

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.styles import Style
    from prompt_toolkit.validation import ValidationError, Validator

    HISTORIES = {
        "type": InMemoryHistory(),
        "scope": InMemoryHistory(),
        "message": InMemoryHistory(),
        "body": InMemoryHistory(),
    }

    PROMPT_STYLE = Style.from_dict(
        {
            "prompt": "#00AFFF bold",
            "command": "#00FF00 bold",
            "option": "#FF00FF",
            "validation-toolbar": "#FF0000 bold",
            "toolbar.text": "#666666 noinherit",
            "toolbar.warning": "#FF8C00 noinherit",
            "toolbar.danger": "#FF4444 noinherit",
            "toolbar": "noinherit",
            "bottom-toolbar": "noinherit",
            "bottom-toolbar.text": "noinherit",
        }
    )

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    HISTORIES = {}
    PROMPT_STYLE = None

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

# Symbols
CHECK = "✓"
CROSS = "✗"
ARROW = "→"
STAR = "★"
DIAMOND = "♦"
HEART = "♥"
WARNING = "⚠"
INFO = "ℹ"
BULLET = "•"

try:
    TERM_WIDTH, TERM_HEIGHT = shutil.get_terminal_size()
except Exception:
    TERM_WIDTH, TERM_HEIGHT = 80, 24

INPUT_LIMITS = {
    "type": 8,
    "scope": 16,
    "message": 64,
    "body": 512,
    "tag": 32,
    "confirmation": 3,
}

COMMIT_TYPES: List[Dict[str, str]] = [
    {
        "type": "feat",
        "emoji_code": ":sparkles:",
        "description": "A new feature for the user or a particular enhancement",
        "color": GREEN,
        "emoji": "✨",
    },
    {
        "type": "fix",
        "emoji_code": ":bug:",
        "description": "A bug fix for the user or a particular issue",
        "color": RED,
        "emoji": "🐛",
    },
    {
        "type": "chore",
        "emoji_code": ":wrench:",
        "description": "Routine tasks, maintenance, or minor updates",
        "color": BLUE,
        "emoji": "🔧",
    },
    {
        "type": "refactor",
        "emoji_code": ":hammer:",
        "description": "Code refactoring without changing its behavior",
        "color": MAGENTA,
        "emoji": "🔨",
    },
    {
        "type": "style",
        "emoji_code": ":lipstick:",
        "description": "Code style changes, formatting, or cosmetic improvements",
        "color": CYAN,
        "emoji": "💄",
    },
    {
        "type": "docs",
        "emoji_code": ":books:",
        "description": "Documentation-related changes",
        "color": WHITE,
        "emoji": "📚",
    },
    {
        "type": "test",
        "emoji_code": ":test_tube:",
        "description": "Adding or modifying tests",
        "color": YELLOW,
        "emoji": "🧪",
    },
    {
        "type": "build",
        "emoji_code": ":package:",
        "description": "Changes that affect the build system or external dependencies",
        "color": YELLOW,
        "emoji": "📦",
    },
    {
        "type": "revert",
        "emoji_code": ":rewind:",
        "description": "Reverts a previous commit",
        "color": RED,
        "emoji": "⏪",
    },
    {
        "type": "ci",
        "emoji_code": ":construction_worker:",
        "description": "Changes to CI configuration files and scripts",
        "color": BLUE,
        "emoji": "👷",
    },
    {
        "type": "perf",
        "emoji_code": ":zap:",
        "description": "A code change that improves performance",
        "color": GREEN,
        "emoji": "⚡",
    },
]


def get_emoji_for_type(commit_type: str, use_code: bool = False) -> str:
    for type_info in COMMIT_TYPES:
        if type_info["type"] == commit_type:
            return type_info["emoji_code"] if use_code else type_info["emoji"]
    return ""


def print_logo() -> None:
    print(f"{WHITE}{BOLD}{ASCII_LOGO}{RESET}")


def print_section(text: str) -> None:
    print()
    print(f"{BLUE}{BOLD}┌{'─' * (len(text) + 2)}┐{RESET}")
    print(f"{BLUE}{BOLD}│ {text} │{RESET}")
    print(f"{BLUE}{BOLD}└{'─' * (len(text) + 2)}┘{RESET}")


def print_message(
    color: str, symbol: str, message: str, bold: bool = False, end: str = "\n"
) -> None:
    bold_code = BOLD if bold else ""
    print(f"{color}{bold_code}{symbol} {message}{RESET}", end=end)


def print_success(message: str, end: str = "\n") -> None:
    print_message(GREEN, CHECK, message, bold=True, end=end)


def print_info(message: str, end: str = "\n") -> None:
    print_message(WHITE, INFO, message, end=end)


def print_process(message: str) -> None:
    print_message(YELLOW, ARROW, message)


def print_error(message: str) -> None:
    print_message(RED, CROSS, message, bold=True)


def print_warning(message: str) -> None:
    print_message(MAGENTA, WARNING, message)


def validate_confirmation_input(user_input: str) -> Optional[bool]:
    if not user_input or len(user_input) > 3:
        return None

    normalized = user_input.lower().strip()
    if normalized in ["y", "yes"]:
        return True
    elif normalized in ["n", "no"]:
        return False
    else:
        return None


class ConfirmationValidator(Validator):
    def validate(self, document):
        text = document.text

        if not text:
            return

        result = validate_confirmation_input(text)
        if result is None:
            if len(text) > 3:
                raise ValidationError(message="Please enter 'y' or 'n'", cursor_position=3)
            else:
                raise ValidationError(message="Please enter 'y' or 'n'", cursor_position=len(text))


class RealTimeCounterValidator(Validator):
    def __init__(self, max_length: int):
        self.max_length = max_length

    def validate(self, document):
        text = document.text
        length = len(text)

        if length > self.max_length:
            raise ValidationError(
                message=f"CHARACTER LIMIT REACHED ({self.max_length}/{self.max_length})",
                cursor_position=self.max_length,
            )


def create_counter_toolbar(max_length: int, is_confirmation: bool = False):
    def get_toolbar_tokens():
        try:
            from prompt_toolkit.application.current import get_app

            app = get_app()
            if app and app.current_buffer:
                current_length = len(app.current_buffer.text)

                if current_length <= max_length * 0.7:
                    color = "class:toolbar.text"
                elif current_length <= max_length * 0.9:
                    color = "class:toolbar.warning"
                else:
                    color = "class:toolbar.danger"

                if is_confirmation:
                    counter_text = f"{current_length}/3"
                    if current_length >= 3:
                        counter_text = f"LIMIT: {counter_text}"
                else:
                    counter_text = f"{current_length}/{max_length}"
                    if current_length >= max_length:
                        counter_text = f"LIMIT: {counter_text}"

                try:
                    term_width = shutil.get_terminal_size().columns
                except:
                    term_width = 80

                padding = max(0, term_width - len(counter_text) - 4)

                return [("", " " * padding), (color, counter_text)]
            return [("class:toolbar.text", f"0/{3 if is_confirmation else max_length}")]
        except:
            return [("class:toolbar.text", f"0/{3 if is_confirmation else max_length}")]

    return get_toolbar_tokens


def create_input_key_bindings(
    max_length: int = 0, is_confirmation: bool = False, multiline: bool = False
):
    kb = KeyBindings()

    if not multiline:

        @kb.add(Keys.ControlM)
        def _(event):
            if is_confirmation and not event.app.current_buffer.text.strip():
                event.app.current_buffer.text = "y"
            event.app.current_buffer.validate_and_handle()

    else:

        @kb.add(Keys.ControlD)
        def _(event):
            event.app.current_buffer.validate_and_handle()

        @kb.add(Keys.Escape, Keys.Enter)
        def _(event):
            event.app.current_buffer.validate_and_handle()

    @kb.add(Keys.Any)
    def _(event):
        current_text = event.app.current_buffer.text
        new_char = event.data
        would_be_text = current_text + new_char

        if is_confirmation and len(would_be_text) > 3:
            return
        elif max_length > 0 and len(would_be_text) > max_length:
            try:
                event.app.output.bell()
            except:
                pass
            event.app.invalidate()
            return
        event.app.current_buffer.insert_text(new_char)

    for key in [Keys.Backspace, Keys.Delete, Keys.Left, Keys.Right, Keys.Home, Keys.End]:

        @kb.add(key)
        def handle_key(event, key=key):
            if key == Keys.Backspace:
                event.app.current_buffer.delete_before_cursor()
            elif key == Keys.Delete:
                event.app.current_buffer.delete()
            elif key == Keys.Left:
                event.app.current_buffer.cursor_left()
            elif key == Keys.Right:
                event.app.current_buffer.cursor_right()
            elif key == Keys.Home:
                event.app.current_buffer.cursor_position = 0
            elif key == Keys.End:
                event.app.current_buffer.cursor_position = len(event.app.current_buffer.text)

    return kb


def read_input(
    prompt_text: str,
    history_type: Optional[str] = None,
    default_text: Optional[str] = None,
    max_length: Optional[int] = None,
) -> str:
    if max_length is None and history_type:
        max_length = INPUT_LIMITS.get(history_type, 0)

    if history_type == "body":
        return read_multiline_input(default_text, max_length)

    if PROMPT_TOOLKIT_AVAILABLE:
        try:
            clean_prompt = prompt_text
            for code in [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD, UNDERLINE, RESET]:
                clean_prompt = clean_prompt.replace(code, "")

            history = HISTORIES.get(history_type) if history_type else None
            validator = RealTimeCounterValidator(max_length) if max_length else None
            key_bindings = create_input_key_bindings(max_length)
            bottom_toolbar = create_counter_toolbar(max_length) if max_length else None

            result = prompt(
                f"{clean_prompt}: ",
                history=history,
                style=PROMPT_STYLE,
                default=default_text or "",
                validator=validator,
                validate_while_typing=True,
                key_bindings=key_bindings,
                bottom_toolbar=bottom_toolbar,
            ).strip()

            if result and max_length:
                current_length = len(result)
                if current_length >= max_length:
                    print(f"    {GREEN}{CHECK} Used all {max_length} characters{RESET}")
                elif current_length >= max_length * 0.8:
                    print(
                        f"    {YELLOW}{WARNING} {current_length}/{max_length} characters used{RESET}"
                    )
                else:
                    print(f"    {WHITE}{INFO} {current_length}/{max_length} characters used{RESET}")

            return result
        except Exception:
            return read_input_fallback(prompt_text, max_length, default_text)
    else:
        return read_input_fallback(prompt_text, max_length, default_text)


def read_input_fallback(
    prompt_text: str, max_length: Optional[int] = None, default_text: Optional[str] = None
) -> str:
    clean_prompt = prompt_text
    for code in [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD, UNDERLINE, RESET]:
        clean_prompt = clean_prompt.replace(code, "")

    if default_text:
        print(f"Default: {default_text}")

    if max_length:
        print(f"{WHITE}{INFO} Maximum {max_length} characters allowed{RESET}")

    while True:
        try:
            user_input = input(f"{clean_prompt}: ").strip()

            if not user_input and default_text:
                user_input = default_text

            if max_length and len(user_input) > max_length:
                print_error(f"CHARACTER LIMIT EXCEEDED! ({len(user_input)}/{max_length})")
                print_warning("Please shorten your input and try again.")
                continue

            if user_input and max_length:
                current_length = len(user_input)
                if current_length >= max_length:
                    print(f"    {GREEN}{CHECK} Used all {max_length} characters{RESET}")
                elif current_length >= max_length * 0.8:
                    print(
                        f"    {YELLOW}{WARNING} {current_length}/{max_length} characters used{RESET}"
                    )
                else:
                    print(f"    {WHITE}{INFO} {current_length}/{max_length} characters used{RESET}")

            return user_input

        except KeyboardInterrupt:
            raise


def confirm_user_action(
    prompt_text: str, success_message: Optional[str] = None, cancel_message: Optional[str] = None
) -> bool:
    user_input = ""

    if PROMPT_TOOLKIT_AVAILABLE:
        try:
            clean_prompt = prompt_text
            for code in [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD, UNDERLINE, RESET]:
                clean_prompt = clean_prompt.replace(code, "")

            validator = ConfirmationValidator()
            key_bindings = create_input_key_bindings(is_confirmation=True)
            bottom_toolbar = create_counter_toolbar(3, is_confirmation=True)

            user_input = prompt(
                f"{clean_prompt}: ",
                validator=validator,
                validate_while_typing=True,
                key_bindings=key_bindings,
                style=PROMPT_STYLE,
                bottom_toolbar=bottom_toolbar,
            ).strip()
        except Exception:
            while True:
                clean_prompt = prompt_text
                for code in [
                    RED,
                    GREEN,
                    YELLOW,
                    BLUE,
                    MAGENTA,
                    CYAN,
                    WHITE,
                    BOLD,
                    UNDERLINE,
                    RESET,
                ]:
                    clean_prompt = clean_prompt.replace(code, "")

                print(f"{WHITE}{INFO} Maximum 3 characters allowed (y/yes or n/no){RESET}")
                user_input = input(f"{clean_prompt}: ").strip()

                if len(user_input) > 3:
                    print_error("CHARACTER LIMIT EXCEEDED! (3 characters maximum)")
                    continue

                result = validate_confirmation_input(user_input)
                if result is not None:
                    break
                print_error("Please enter 'y' or 'n'")
    else:
        while True:
            clean_prompt = prompt_text
            for code in [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD, UNDERLINE, RESET]:
                clean_prompt = clean_prompt.replace(code, "")

            print(f"{WHITE}{INFO} Maximum 3 characters allowed (y/yes or n/no){RESET}")
            user_input = input(f"{clean_prompt}: ").strip()

            if len(user_input) > 3:
                print_error("CHARACTER LIMIT EXCEEDED! (3 characters maximum)")
                continue

            result = validate_confirmation_input(user_input)
            if result is not None:
                break
            print_error("Please enter 'y' or 'n'")

    result = validate_confirmation_input(user_input)

    if result:
        if success_message:
            print_success(success_message)
        return True
    else:
        if cancel_message:
            print_info(cancel_message)
        return False


def read_multiline_input(
    default_text: Optional[str] = None, max_length: Optional[int] = None
) -> str:
    if PROMPT_TOOLKIT_AVAILABLE and max_length:
        try:
            from prompt_toolkit import prompt

            if default_text:
                print(f"Current content:\n{default_text}")
            print(f"{BLUE}Press Ctrl+D or Escape+Enter to finish. Press Enter for new line.{RESET}")
            print(f"{BLUE}Maximum {max_length} characters allowed{RESET}")

            validator = RealTimeCounterValidator(max_length)
            key_bindings = create_input_key_bindings(max_length, multiline=True)
            bottom_toolbar = create_counter_toolbar(max_length)

            result = prompt(
                "",
                multiline=True,
                style=PROMPT_STYLE,
                default=default_text or "",
                validator=validator,
                validate_while_typing=True,
                key_bindings=key_bindings,
                bottom_toolbar=bottom_toolbar,
            ).strip()

            if result:
                char_count = len(result)
                if char_count >= max_length:
                    print(f"    {GREEN}{CHECK} Used all {max_length} characters{RESET}")
                elif char_count >= max_length * 0.8:
                    print(f"    {YELLOW}{WARNING} {char_count}/{max_length} characters used{RESET}")
                else:
                    print(f"    {WHITE}{INFO} {char_count}/{max_length} characters used{RESET}")

            return result

        except Exception:
            pass

    if default_text:
        print(f"Current content:\n{default_text}")
        print(f"{BLUE}Enter new content (or press Enter twice to finish):{RESET}")
    else:
        print(f"{BLUE}Enter additional details (or press Enter twice to finish):{RESET}")
    if max_length:
        print(f"{BLUE}Maximum {max_length} characters allowed{RESET}")

    lines = []
    empty_line_count = 0
    total_chars = 0
    max_line_length = 80

    try:
        while True:
            try:
                if max_length and total_chars > 0:
                    remaining = max_length - total_chars
                    if remaining <= 0:
                        print_error(f"Character limit of {max_length} reached.")
                        break
                    elif remaining <= max_length * 0.2:
                        print(
                            f"    {YELLOW}{WARNING} {total_chars}/{max_length} characters{RESET}",
                            end="\r",
                        )
                    else:
                        print(
                            f"    {WHITE}{INFO} {total_chars}/{max_length} characters{RESET}",
                            end="\r",
                        )

                line = input()

                if max_length and total_chars > 0:
                    print(" " * 50, end="\r")

                if len(line) > max_line_length:
                    print_error(f"Line too long! Maximum {max_line_length} characters per line.")
                    print_warning(f"Current line has {len(line)} characters. Please shorten it.")
                    continue

                potential_total = total_chars + len(line) + (1 if lines else 0)

                if max_length and potential_total > max_length:
                    remaining = max_length - total_chars
                    if remaining <= 0:
                        print_error(f"Character limit of {max_length} reached.")
                        break
                    else:
                        print_error(f"Line too long! Only {remaining} characters remaining total.")
                        print_warning("Try a shorter line or finish your input.")
                        continue

                if not line:
                    empty_line_count += 1
                    if empty_line_count >= 2:
                        break
                    lines.append(line)
                    total_chars += 1
                else:
                    empty_line_count = 0
                    lines.append(line)
                    total_chars += len(line) + (1 if lines else 0)

            except EOFError:
                break
            except KeyboardInterrupt:
                raise

    except KeyboardInterrupt:
        print("\nSkipping...")
        return ""

    while lines and not lines[-1]:
        lines.pop()

    result = "\n".join(lines).strip()

    if not result and default_text:
        return default_text

    if result:
        char_count = len(result)
        if max_length:
            if char_count >= max_length:
                print(f"    {GREEN}{CHECK} Used all {max_length} characters{RESET}")
            elif char_count >= max_length * 0.8:
                print(f"    {YELLOW}{WARNING} {char_count}/{max_length} characters used{RESET}")
            else:
                print(f"    {WHITE}{INFO} {char_count}/{max_length} characters used{RESET}")

    return result
