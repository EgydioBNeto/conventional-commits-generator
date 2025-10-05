"""Utilities and styling for the Conventional Commits Generator."""

import shutil
from typing import Any, Callable, Dict, List, Optional, Tuple

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

    HISTORIES: Dict[str, Any] = {
        "type": InMemoryHistory(),
        "scope": InMemoryHistory(),
        "message": InMemoryHistory(),
        "body": InMemoryHistory(),
    }

    PROMPT_STYLE: Any = Style.from_dict(
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

    class ConfirmationValidator(Validator):
        """Validator for yes/no confirmation prompts in prompt_toolkit.

        Validates that user input is a valid confirmation response (y/yes/n/no)
        or empty (uses default). Shows error message for invalid inputs.

        Args:
            default_yes: Default value when input is empty
        """

        def __init__(self, default_yes: bool = True) -> None:
            self.default_yes = default_yes

        def validate(self, document: Any) -> None:
            """Validate the confirmation input."""
            text = document.text

            if not text:
                return

            result = validate_confirmation_input(text, self.default_yes)
            if result is None:
                if len(text) > 3:
                    raise ValidationError(message="Please enter 'y' or 'n'", cursor_position=3)
                else:
                    raise ValidationError(
                        message="Please enter 'y' or 'n'", cursor_position=len(text)
                    )

    class RealTimeCounterValidator(Validator):
        """Validator for enforcing character limits in prompt_toolkit.

        Prevents user from entering more than the maximum allowed characters
        by raising a validation error when limit is exceeded.

        Args:
            max_length: Maximum number of characters allowed
        """

        def __init__(self, max_length: int) -> None:
            self.max_length = max_length

        def validate(self, document: Any) -> None:
            """Validate input length against maximum."""
            text = document.text
            length = len(text)

            if length > self.max_length:
                raise ValidationError(
                    message=f"CHARACTER LIMIT REACHED ({self.max_length}/{self.max_length})",
                    cursor_position=self.max_length,
                )

    PROMPT_TOOLKIT_AVAILABLE: bool = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    HISTORIES: Dict[str, Any] = {}  # type: ignore[no-redef]
    PROMPT_STYLE: Any = None  # type: ignore[no-redef]
    ConfirmationValidator = None  # type: ignore[misc, assignment]
    RealTimeCounterValidator = None  # type: ignore[misc, assignment]

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
    TERM_WIDTH: int
    TERM_HEIGHT: int
    TERM_WIDTH, TERM_HEIGHT = shutil.get_terminal_size()
except Exception:
    from ccg.config import UI_CONFIG

    TERM_WIDTH, TERM_HEIGHT = (
        UI_CONFIG.DEFAULT_TERM_WIDTH,
        UI_CONFIG.DEFAULT_TERM_HEIGHT,
    )

# Import configuration - backward compatibility dict
from ccg.config import INPUT_LIMITS as INPUT_LIMITS_CONFIG

INPUT_LIMITS: Dict[str, int] = {
    "type": INPUT_LIMITS_CONFIG.TYPE,
    "scope": INPUT_LIMITS_CONFIG.SCOPE,
    "message": INPUT_LIMITS_CONFIG.MESSAGE,
    "body": INPUT_LIMITS_CONFIG.BODY,
    "tag": INPUT_LIMITS_CONFIG.TAG,
    "tag_message": INPUT_LIMITS_CONFIG.TAG_MESSAGE,
    "edit_message": INPUT_LIMITS_CONFIG.EDIT_MESSAGE,
    "confirmation": INPUT_LIMITS_CONFIG.CONFIRMATION,
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
    """Get the emoji or emoji code for a given commit type.

    Looks up the emoji associated with a conventional commit type from the
    COMMIT_TYPES list. Can return either the actual emoji character or the
    GitHub-compatible emoji code.

    Args:
        commit_type: The commit type (e.g., "feat", "fix", "chore")
        use_code: If True, return emoji code (":sparkles:"), else actual emoji ("✨")

    Returns:
        Emoji string or emoji code, empty string if type not found

    Examples:
        >>> get_emoji_for_type("feat")
        '✨'
        >>> get_emoji_for_type("feat", use_code=True)
        ':sparkles:'
    """
    for type_info in COMMIT_TYPES:
        if type_info["type"] == commit_type:
            return type_info["emoji_code"] if use_code else type_info["emoji"]
    return ""


def print_logo() -> None:
    """Print the CCG ASCII art logo in bold white.

    Displays the application's branded ASCII logo at the start of operations
    and in help messages.

    Note:
        Logo is defined in the ASCII_LOGO constant
    """
    print(f"{WHITE}{BOLD}{ASCII_LOGO}{RESET}")


def strip_color_codes(text: str) -> str:
    """Remove ANSI color codes from text.

    Args:
        text: Text containing ANSI color codes

    Returns:
        Text with all color codes removed
    """
    color_codes = [
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
    ]
    result = text
    for code in color_codes:
        result = result.replace(code, "")
    return result


def print_section(text: str) -> None:
    """Print a section header with a decorative box border.

    Creates a visually distinct section header surrounded by box-drawing
    characters in blue/bold style.

    Args:
        text: Section title to display

    Examples:
        >>> print_section("Git Staging")
        # Displays:
        # ┌─────────────┐
        # │ Git Staging │
        # └─────────────┘
    """
    print()
    print(f"{BLUE}{BOLD}┌{'─' * (len(text) + 2)}┐{RESET}")
    print(f"{BLUE}{BOLD}│ {text} │{RESET}")
    print(f"{BLUE}{BOLD}└{'─' * (len(text) + 2)}┘{RESET}")


def print_message(
    color: str, symbol: str, message: str, bold: bool = False, end: str = "\n"
) -> None:
    """Print a formatted message with color, symbol, and optional bold.

    Generic message printer used by specialized functions like print_success,
    print_error, etc. Provides consistent formatting across the application.

    Args:
        color: ANSI color code (e.g., GREEN, RED, YELLOW)
        symbol: Symbol to display before message (e.g., CHECK, CROSS, WARNING)
        message: The message text to display
        bold: If True, apply bold formatting
        end: String to append at the end (default: newline)

    Note:
        Always resets formatting after the message to prevent color bleed
    """
    bold_code = BOLD if bold else ""
    print(f"{color}{bold_code}{symbol} {message}{RESET}", end=end)


def print_success(message: str, end: str = "\n") -> None:
    """Print a success message in bold green with checkmark symbol.

    Args:
        message: Success message to display
        end: String to append at the end (default: newline)
    """
    print_message(GREEN, CHECK, message, bold=True, end=end)


def print_info(message: str, end: str = "\n") -> None:
    """Print an informational message in white with info symbol.

    Args:
        message: Information message to display
        end: String to append at the end (default: newline)
    """
    print_message(WHITE, INFO, message, end=end)


def print_process(message: str) -> None:
    """Print a process/progress message in yellow with arrow symbol.

    Used to indicate ongoing operations or processes.

    Args:
        message: Process message to display
    """
    print_message(YELLOW, ARROW, message)


def print_error(message: str) -> None:
    """Print an error message in bold red with cross symbol.

    Args:
        message: Error message to display
    """
    print_message(RED, CROSS, message, bold=True)


def print_warning(message: str) -> None:
    """Print a warning message in magenta with warning symbol.

    Args:
        message: Warning message to display
    """
    print_message(MAGENTA, WARNING, message)


def validate_confirmation_input(user_input: str, default_yes: bool = True) -> Optional[bool]:
    """Validate user input for yes/no confirmation prompts.

    Checks if user input is a valid confirmation response (y/yes/n/no) and
    returns the corresponding boolean. Handles empty input by using the default.

    Args:
        user_input: User's input string
        default_yes: Default value when input is empty (True for Yes, False for No)

    Returns:
        True for yes, False for no, None for invalid input

    Note:
        Case-insensitive. Maximum 3 characters allowed to prevent accidental long inputs.
    """
    if len(user_input) > 3:
        return None

    # Empty input uses default
    if not user_input:
        return default_yes

    normalized = user_input.lower().strip()
    if normalized in ["y", "yes"]:
        return True
    elif normalized in ["n", "no"]:
        return False
    else:
        return None


def create_counter_toolbar(
    max_length: int, is_confirmation: bool = False
) -> Optional[Callable[[], List[Tuple[str, str]]]]:
    """Create a bottom toolbar function for prompt_toolkit showing character count.

    Generates a callable that displays a real-time character counter with color
    coding based on proximity to the limit (green → yellow → red).

    Args:
        max_length: Maximum character limit to display
        is_confirmation: If True, use 3-char limit for confirmation prompts

    Returns:
        Callable that returns toolbar tokens for prompt_toolkit, or None if unavailable

    Note:
        Color changes at 70% (warning) and 90% (danger) of max_length.
        Right-aligned with padding calculated from terminal width.
    """

    def get_toolbar_tokens() -> List[Tuple[str, str]]:
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
    max_length: int = 0,
    is_confirmation: bool = False,
    multiline: bool = False,
    default_yes: bool = True,
) -> Any:
    """Create custom key bindings for prompt_toolkit input handling.

    Configures keyboard shortcuts and input behaviors including character limits,
    multiline support, confirmation defaults, and navigation keys.

    Args:
        max_length: Maximum characters allowed (0 = no limit)
        is_confirmation: If True, auto-fill default on Enter
        multiline: If True, enable multiline mode with Ctrl+D/Escape+Enter to submit
        default_yes: Default confirmation value (only used if is_confirmation=True)

    Returns:
        KeyBindings object for prompt_toolkit, or None if unavailable

    Note:
        Prevents input beyond max_length with visual bell feedback.
        Handles standard navigation keys (arrows, home, end, backspace, delete).
    """
    kb = KeyBindings()

    if not multiline:

        @kb.add(Keys.ControlM)
        def _(event: Any) -> None:
            if is_confirmation and not event.app.current_buffer.text.strip():
                event.app.current_buffer.text = "y" if default_yes else "n"
            event.app.current_buffer.validate_and_handle()

    else:

        @kb.add(Keys.ControlD)
        def _(event: Any) -> None:
            event.app.current_buffer.validate_and_handle()

        @kb.add(Keys.Escape, Keys.Enter)
        def _(event: Any) -> None:
            event.app.current_buffer.validate_and_handle()

    @kb.add(Keys.Any)
    def _(event: Any) -> None:
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

    for key in [
        Keys.Backspace,
        Keys.Delete,
        Keys.Left,
        Keys.Right,
        Keys.Home,
        Keys.End,
    ]:

        @kb.add(key)
        def handle_key(event: Any, key: Any = key) -> None:
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
    """Read single-line input from user with validation and history.

    Provides an enhanced input experience using prompt_toolkit (if available)
    with features like history navigation, character limits, real-time validation,
    and a character counter toolbar. Falls back to basic input if unavailable.

    Args:
        prompt_text: Prompt message to display (color codes will be stripped)
        history_type: Type of history to use ("type", "scope", "message", "body", etc.)
        default_text: Default value to pre-fill in the input
        max_length: Maximum characters allowed (auto-detected from history_type if not provided)

    Returns:
        User input string (stripped of leading/trailing whitespace)

    Raises:
        EOFError: If user presses Ctrl+D
        KeyboardInterrupt: If user presses Ctrl+C

    Note:
        For body input (multiline), delegates to read_multiline_input.
        Displays character usage feedback after input is submitted.
    """
    if max_length is None and history_type:
        max_length = INPUT_LIMITS.get(history_type, 0)

    if history_type == "body":
        return read_multiline_input(default_text, max_length)

    if PROMPT_TOOLKIT_AVAILABLE:
        try:
            clean_prompt = strip_color_codes(prompt_text)

            history = HISTORIES.get(history_type) if history_type else None
            validator = RealTimeCounterValidator(max_length) if max_length else None
            key_bindings = create_input_key_bindings(max_length if max_length else 0)
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
        except (EOFError, KeyboardInterrupt):
            print()
            raise
        except Exception:
            return read_input_fallback(prompt_text, max_length, default_text)
    else:
        return read_input_fallback(prompt_text, max_length, default_text)


def read_input_fallback(
    prompt_text: str,
    max_length: Optional[int] = None,
    default_text: Optional[str] = None,
) -> str:
    """Fallback input function when prompt_toolkit is unavailable.

    Provides basic input functionality with character limit validation using
    standard Python input(). Loops until valid input is provided.

    Args:
        prompt_text: Prompt message to display (color codes will be stripped)
        max_length: Optional maximum character limit
        default_text: Optional default value

    Returns:
        User input string (stripped), or default_text if input is empty

    Raises:
        EOFError: If user presses Ctrl+D
        KeyboardInterrupt: If user presses Ctrl+C

    Note:
        Shows character usage feedback after successful input
    """
    clean_prompt = strip_color_codes(prompt_text)

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

        except (EOFError, KeyboardInterrupt):
            print()
            raise


def confirm_user_action(
    prompt_text: str,
    success_message: Optional[str] = None,
    cancel_message: Optional[str] = None,
    default_yes: bool = True,
) -> bool:
    """Prompt user for yes/no confirmation with validation.

    Displays a confirmation prompt and validates the user's response. Supports
    default values (indicated by uppercase letter in prompt) and provides
    helpful feedback messages.

    Args:
        prompt_text: Confirmation question (should contain "(y/n)")
        success_message: Message to show if user confirms (None to skip)
        cancel_message: Message to show if user cancels (None to skip)
        default_yes: If True, default to Yes on Enter; otherwise default to No

    Returns:
        True if user confirmed, False if user cancelled

    Raises:
        EOFError: If user presses Ctrl+D
        KeyboardInterrupt: If user presses Ctrl+C

    Note:
        Automatically converts "(y/n)" to "(Y/n)" or "(y/N)" based on default_yes.
        Uses prompt_toolkit if available, falls back to basic input otherwise.
    """
    user_input = ""

    # Replace (y/n) with (Y/n) or (y/N) based on default
    prompt_display = prompt_text
    if default_yes:
        prompt_display = prompt_display.replace("(y/n)", "(Y/n)")
    else:
        prompt_display = prompt_display.replace("(y/n)", "(y/N)")

    if PROMPT_TOOLKIT_AVAILABLE:
        try:
            clean_prompt = strip_color_codes(prompt_display)

            validator = ConfirmationValidator(default_yes)
            key_bindings = create_input_key_bindings(is_confirmation=True, default_yes=default_yes)
            bottom_toolbar = create_counter_toolbar(3, is_confirmation=True)

            user_input = prompt(
                f"{clean_prompt}: ",
                validator=validator,
                validate_while_typing=True,
                key_bindings=key_bindings,
                style=PROMPT_STYLE,
                bottom_toolbar=bottom_toolbar,
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise
        except Exception:
            while True:
                try:
                    clean_prompt = strip_color_codes(prompt_display)

                    default_hint = "Y/n" if default_yes else "y/N"
                    print(
                        f"{WHITE}{INFO} Press Enter for default ({default_hint}) or type y/yes or n/no{RESET}"
                    )
                    user_input = input(f"{clean_prompt}: ").strip()

                    if len(user_input) > 3:
                        print_error("CHARACTER LIMIT EXCEEDED! (3 characters maximum)")
                        continue

                    result = validate_confirmation_input(user_input, default_yes)
                    if result is not None:
                        break
                    print_error("Please enter 'y' or 'n'")
                except (EOFError, KeyboardInterrupt):
                    print()
                    raise
    else:
        while True:
            try:
                clean_prompt = strip_color_codes(prompt_display)

                default_hint = "Y/n" if default_yes else "y/N"
                print(
                    f"{WHITE}{INFO} Press Enter for default ({default_hint}) or type y/yes or n/no{RESET}"
                )
                user_input = input(f"{clean_prompt}: ").strip()

                if len(user_input) > 3:
                    print_error("CHARACTER LIMIT EXCEEDED! (3 characters maximum)")
                    continue

                result = validate_confirmation_input(user_input, default_yes)
                if result is not None:
                    break
                print_error("Please enter 'y' or 'n'")
            except (EOFError, KeyboardInterrupt):
                print()
                raise

    result = validate_confirmation_input(user_input, default_yes)

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
    """Read multiline input from user with character limit validation.

    Allows users to enter multiple lines of text for commit bodies or other
    long-form content. Uses prompt_toolkit for enhanced experience if available,
    otherwise falls back to basic multiline input with double-Enter to finish.

    Args:
        default_text: Optional default text to pre-fill
        max_length: Optional maximum total character limit

    Returns:
        Multiline input as a single string (with newlines), or default_text if empty

    Raises:
        EOFError: If user presses Ctrl+D
        KeyboardInterrupt: If user presses Ctrl+C

    Note:
        With prompt_toolkit: Use Ctrl+D or Escape+Enter to submit
        Without prompt_toolkit: Press Enter twice (empty line) to finish
        Maximum 80 characters per line in fallback mode
        Displays character usage feedback after input
    """
    if PROMPT_TOOLKIT_AVAILABLE and max_length:
        try:
            from prompt_toolkit import prompt

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

        except (EOFError, KeyboardInterrupt):
            print()
            raise
        except Exception:
            pass

    if default_text:
        print(f"{BLUE}Enter new content (or press Enter twice to finish):{RESET}")
    else:
        print(f"{BLUE}Enter additional details (or press Enter twice to finish):{RESET}")
    if max_length:
        print(f"{BLUE}Maximum {max_length} characters allowed{RESET}")

    lines: List[str] = []
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

            except (EOFError, KeyboardInterrupt):
                break

    except KeyboardInterrupt:
        print()
        raise

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
