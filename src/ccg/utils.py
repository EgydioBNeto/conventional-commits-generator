"""Utilities and styling for the Conventional Commits Generator."""

import re
import shutil
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, TypeVar

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

prompt_toolkit_available: Optional[bool] = None
_prompt_toolkit_cache: Dict[str, object] = {}

T = TypeVar("T")


def _ensure_prompt_toolkit() -> bool:
    """Lazy load prompt_toolkit on first use.

    Imports and caches all necessary prompt_toolkit components only when needed.
    This reduces startup time for commands that don't require user interaction
    (e.g., --help, --version).

    Returns:
        True if prompt_toolkit is available and loaded, False otherwise
    """
    global prompt_toolkit_available, _prompt_toolkit_cache

    if prompt_toolkit_available is not None:
        return prompt_toolkit_available

    try:
        from prompt_toolkit import prompt
        from prompt_toolkit.document import Document
        from prompt_toolkit.history import InMemoryHistory
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.key_binding.key_processor import KeyPressEvent
        from prompt_toolkit.keys import Keys
        from prompt_toolkit.styles import Style
        from prompt_toolkit.validation import ValidationError, Validator

        histories = {
            "type": InMemoryHistory(),
            "scope": InMemoryHistory(),
            "message": InMemoryHistory(),
            "body": InMemoryHistory(),
        }

        prompt_style = Style.from_dict(
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

        class _ConfirmationValidator(Validator):  # pragma: no cover
            """Validator for yes/no confirmation prompts in prompt_toolkit."""

            def __init__(self, default_yes: bool = True) -> None:
                self.default_yes = default_yes

            def validate(self, document: Document) -> None:
                """Validate the confirmation input."""
                text = document.text

                if not text:
                    return

                result = validate_confirmation_input(text, self.default_yes)
                if result is None:
                    from ccg.config import UI_CONFIG as UI_CFG

                    if len(text) > UI_CFG.CONFIRMATION_MAX_LENGTH:
                        raise ValidationError(
                            message="Please enter 'y' or 'n'",
                            cursor_position=UI_CFG.CONFIRMATION_MAX_LENGTH,
                        )
                    else:
                        raise ValidationError(
                            message="Please enter 'y' or 'n'", cursor_position=len(text)
                        )

        class _RealTimeCounterValidator(Validator):  # pragma: no cover
            """Validator for enforcing character limits in prompt_toolkit."""

            def __init__(self, max_length: int) -> None:
                self.max_length = max_length

            def validate(self, document: Document) -> None:
                """Validate input length against maximum."""
                text = document.text
                length = len(text)

                if length > self.max_length:
                    raise ValidationError(
                        message=f"CHARACTER LIMIT REACHED ({self.max_length}/{self.max_length})",
                        cursor_position=self.max_length,
                    )

        _prompt_toolkit_cache.update(
            {
                "prompt": prompt,
                "Document": Document,
                "InMemoryHistory": InMemoryHistory,
                "KeyBindings": KeyBindings,
                "Keys": Keys,
                "KeyPressEvent": KeyPressEvent,
                "Style": Style,
                "ValidationError": ValidationError,
                "Validator": Validator,
                "histories": histories,
                "prompt_style": prompt_style,
                "ConfirmationValidator": _ConfirmationValidator,
                "RealTimeCounterValidator": _RealTimeCounterValidator,
            }
        )

        prompt_toolkit_available = True
        _update_module_exports()
        return True

    except ImportError:
        prompt_toolkit_available = False
        _update_module_exports()
        return False


def _get_cached(key: str, default: Optional[T] = None) -> Optional[T]:
    """Get a cached prompt_toolkit component, loading if necessary."""
    if _ensure_prompt_toolkit():
        return _prompt_toolkit_cache.get(key, default)  # type: ignore[return-value]
    return default


PROMPT_TOOLKIT_AVAILABLE: bool = False
HISTORIES: Dict[str, object] = {}
PROMPT_STYLE: Optional[object] = None

prompt: Optional[object] = None
Document: Optional[object] = None
InMemoryHistory: Optional[object] = None
KeyBindings: Optional[object] = None
Keys: Optional[object] = None
KeyPressEvent: Optional[object] = None
Style: Optional[object] = None
ValidationError: Optional[object] = None
Validator: Optional[object] = None
ConfirmationValidator: Optional[object] = None
RealTimeCounterValidator: Optional[object] = None


def _update_module_exports() -> None:
    """Update module-level exports after lazy loading."""
    global PROMPT_TOOLKIT_AVAILABLE, HISTORIES, PROMPT_STYLE
    global prompt, Document, InMemoryHistory, KeyBindings, Keys, KeyPressEvent
    global Style, ValidationError, Validator, ConfirmationValidator, RealTimeCounterValidator

    PROMPT_TOOLKIT_AVAILABLE = prompt_toolkit_available or False
    HISTORIES = _get_cached("histories", {}) or {}
    PROMPT_STYLE = _get_cached("prompt_style")

    if prompt is None:
        prompt = _get_cached("prompt")
    if Document is None:
        Document = _get_cached("Document")
    if InMemoryHistory is None:
        InMemoryHistory = _get_cached("InMemoryHistory")
    if KeyBindings is None:
        KeyBindings = _get_cached("KeyBindings")
    if Keys is None:
        Keys = _get_cached("Keys")
    if KeyPressEvent is None:
        KeyPressEvent = _get_cached("KeyPressEvent")
    if Style is None:
        Style = _get_cached("Style")
    if ValidationError is None:
        ValidationError = _get_cached("ValidationError")
    if Validator is None:
        Validator = _get_cached("Validator")
    if ConfirmationValidator is None:
        ConfirmationValidator = _get_cached("ConfirmationValidator")
    if RealTimeCounterValidator is None:
        RealTimeCounterValidator = _get_cached("RealTimeCounterValidator")


from ccg.config import BLUE, BOLD, COMMIT_TYPES, CYAN, GREEN
from ccg.config import INPUT_LIMITS as INPUT_LIMITS_CONFIG
from ccg.config import MAGENTA, RED, RESET, UNDERLINE, WHITE, YELLOW

# Re-export color codes for backward compatibility
__all__ = [
    "BOLD",
    "BLUE",
    "COMMIT_TYPES",
    "CYAN",
    "GREEN",
    "MAGENTA",
    "RED",
    "RESET",
    "UNDERLINE",
    "WHITE",
    "YELLOW",
]

CHECK = "✓"
CROSS = "✗"
ARROW = "→"
WARNING = "⚠"
INFO = "ℹ"
BULLET = "•"

INPUT_LIMITS: Dict[str, int] = {
    "type": INPUT_LIMITS_CONFIG.TYPE,
    "scope": INPUT_LIMITS_CONFIG.SCOPE,
    "message": INPUT_LIMITS_CONFIG.MESSAGE,
    "body": INPUT_LIMITS_CONFIG.BODY,
    "tag": INPUT_LIMITS_CONFIG.TAG,
    "tag_message": INPUT_LIMITS_CONFIG.TAG_MESSAGE,
    "edit_message": INPUT_LIMITS_CONFIG.EDIT_MESSAGE,
    "confirmation": INPUT_LIMITS_CONFIG.CONFIRMATION,
    "commit_count": INPUT_LIMITS_CONFIG.COMMIT_COUNT,
    "commit_hash": INPUT_LIMITS_CONFIG.COMMIT_HASH,
}

# Pre-compiled regex pattern for performance optimization
# Compiling at module level avoids re-compilation on every function call
# Validates SemVer 2.0.0 format: https://semver.org/
_SEMVER_PATTERN = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


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
    from ccg.config import UI_CONFIG as UI_CFG

    if len(user_input) > UI_CFG.CONFIRMATION_MAX_LENGTH:
        return None

    if not user_input:
        return default_yes

    normalized = user_input.lower().strip()
    if normalized in ["y", "yes"]:
        return True
    elif normalized in ["n", "no"]:
        return False
    else:
        return None


def is_valid_semver(tag: str) -> bool:
    """Validate if a string is a valid SemVer 2.0.0 tag.

    Args:
        tag: The tag string to validate.

    Returns:
        True if the tag is a valid SemVer tag, False otherwise.

    Examples:
        >>> is_valid_semver("v1.2.3")
        True
        >>> is_valid_semver("1.0.0-alpha.1")
        True
        >>> is_valid_semver("invalid")
        False
    """
    return _SEMVER_PATTERN.match(tag) is not None


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

    def get_toolbar_tokens() -> List[Tuple[str, str]]:  # pragma: no cover
        try:
            from prompt_toolkit.application.current import get_app

            app = get_app()
            if app and app.current_buffer:
                current_length = len(app.current_buffer.text)

                from ccg.config import UI_CONFIG as UI_CFG_COLOR

                if current_length <= max_length * UI_CFG_COLOR.WARNING_THRESHOLD:
                    color = "class:toolbar.text"
                elif current_length <= max_length * UI_CFG_COLOR.DANGER_THRESHOLD:
                    color = "class:toolbar.warning"
                else:
                    color = "class:toolbar.danger"

                if is_confirmation:
                    from ccg.config import UI_CONFIG as UI_CFG

                    max_conf = UI_CFG.CONFIRMATION_MAX_LENGTH
                    counter_text = f"{current_length}/{max_conf}"
                    if current_length >= max_conf:
                        counter_text = f"LIMIT: {counter_text}"
                else:
                    counter_text = f"{current_length}/{max_length}"
                    if current_length >= max_length:
                        counter_text = f"LIMIT: {counter_text}"

                try:
                    term_width_local = shutil.get_terminal_size().columns
                except (OSError, ValueError, AttributeError):
                    from ccg.config import UI_CONFIG as UI_CFG_TERM

                    term_width_local = UI_CFG_TERM.DEFAULT_TERM_WIDTH

                padding = max(0, term_width_local - len(counter_text) - 4)

                return [("", " " * padding), (color, counter_text)]
            from ccg.config import UI_CONFIG as UI_CFG

            default_max = UI_CFG.CONFIRMATION_MAX_LENGTH if is_confirmation else max_length
            return [("class:toolbar.text", f"0/{default_max}")]
        except Exception:
            from ccg.config import UI_CONFIG as UI_CFG

            default_max = UI_CFG.CONFIRMATION_MAX_LENGTH if is_confirmation else max_length
            return [("class:toolbar.text", f"0/{default_max}")]

    return get_toolbar_tokens


def create_input_key_bindings(
    max_length: int = 0,
    is_confirmation: bool = False,
    multiline: bool = False,
    default_yes: bool = True,
) -> Optional[object]:
    """Create custom key bindings for prompt_toolkit input handling.

    Configures keyboard shortcuts and input behaviors including character limits,
    multiline support, confirmation defaults, and navigation keys.

    Args:
        max_length: Maximum characters allowed (0 = no limit)
        is_confirmation: If True, auto-fill default on Enter
        multiline: If True, enable multiline mode with Ctrl+D to submit
        default_yes: Default confirmation value (only used if is_confirmation=True)

    Returns:
        KeyBindings object for prompt_toolkit, or None if unavailable

    Note:
        Prevents input beyond max_length with visual bell feedback.
        Handles standard navigation keys (arrows, home, end, backspace, delete).
    """
    if not _ensure_prompt_toolkit():
        return None

    from ccg import utils as utils_module

    KeyBindings_cls = utils_module.KeyBindings
    Keys_cls = utils_module.Keys

    if KeyBindings_cls is None or Keys_cls is None:
        return None

    kb = KeyBindings_cls()  # type: ignore[operator]

    if not multiline:

        @kb.add(Keys_cls.ControlM)  # type: ignore[misc,attr-defined]
        def _(event: Any) -> None:  # pragma: no cover
            if is_confirmation and not event.app.current_buffer.text.strip():
                event.app.current_buffer.text = "y" if default_yes else "n"
            event.app.current_buffer.validate_and_handle()

    else:

        @kb.add(Keys_cls.ControlD)  # type: ignore[misc,attr-defined]
        def _(event: Any) -> None:  # pragma: no cover
            event.app.current_buffer.validate_and_handle()

        @kb.add(Keys_cls.Escape, Keys_cls.Enter)  # type: ignore[misc,attr-defined]
        def _(event: Any) -> None:  # pragma: no cover
            event.app.current_buffer.validate_and_handle()

    @kb.add(Keys_cls.Any)  # type: ignore[misc,attr-defined]
    def _(event: Any) -> None:  # pragma: no cover
        current_text = event.app.current_buffer.text
        new_char = event.data
        would_be_text = current_text + new_char

        from ccg.config import UI_CONFIG as UI_CFG

        if is_confirmation and len(would_be_text) > UI_CFG.CONFIRMATION_MAX_LENGTH:
            return
        elif max_length > 0 and len(would_be_text) > max_length:
            try:
                event.app.output.bell()
            except (AttributeError, OSError):
                pass
            event.app.invalidate()
            return
        event.app.current_buffer.insert_text(new_char)

    @kb.add(Keys_cls.Backspace)  # type: ignore[misc,attr-defined]
    def _(event: Any) -> None:  # pragma: no cover
        event.app.current_buffer.delete_before_cursor()

    @kb.add(Keys_cls.Delete)  # type: ignore[misc,attr-defined]
    def _(event: Any) -> None:  # pragma: no cover
        event.app.current_buffer.delete()

    @kb.add(Keys_cls.Left)  # type: ignore[misc,attr-defined]
    def _(event: Any) -> None:  # pragma: no cover
        event.app.current_buffer.cursor_left()

    @kb.add(Keys_cls.Right)  # type: ignore[misc,attr-defined]
    def _(event: Any) -> None:  # pragma: no cover
        event.app.current_buffer.cursor_right()

    @kb.add(Keys_cls.Home)  # type: ignore[misc,attr-defined]
    def _(event: Any) -> None:  # pragma: no cover
        event.app.current_buffer.cursor_position = 0

    @kb.add(Keys_cls.End)  # type: ignore[misc,attr-defined]
    def _(event: Any) -> None:  # pragma: no cover
        event.app.current_buffer.cursor_position = len(event.app.current_buffer.text)

    return kb  # type: ignore[no-any-return]


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

    from ccg import utils as utils_module

    if _ensure_prompt_toolkit() and utils_module.PROMPT_TOOLKIT_AVAILABLE:
        try:
            prompt_fn = utils_module.prompt
            histories = utils_module.HISTORIES
            prompt_style = utils_module.PROMPT_STYLE
            RealTimeCounterValidator_cls = utils_module.RealTimeCounterValidator

            if prompt_fn is None:  # pragma: no cover
                return read_input_fallback(prompt_text, max_length, default_text)

            clean_prompt = strip_color_codes(prompt_text)

            history = histories.get(history_type) if history_type else None
            validator = RealTimeCounterValidator_cls(max_length) if max_length and RealTimeCounterValidator_cls else None  # type: ignore[operator]
            key_bindings = create_input_key_bindings(max_length if max_length else 0)
            bottom_toolbar = create_counter_toolbar(max_length) if max_length else None

            result = str(
                prompt_fn(  # type: ignore[operator]
                    f"{clean_prompt}: ",
                    history=history,
                    style=prompt_style,
                    default=default_text or "",
                    validator=validator,
                    validate_while_typing=True,
                    key_bindings=key_bindings,
                    bottom_toolbar=bottom_toolbar,
                )
            ).strip()

            return result
        except (EOFError, KeyboardInterrupt):  # pragma: no cover
            print()
            raise
        except (ImportError, AttributeError, TypeError, Exception) as e:
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

    prompt_display = prompt_text
    if default_yes:
        prompt_display = prompt_display.replace("(y/n)", "(Y/n)")
    else:
        prompt_display = prompt_display.replace("(y/n)", "(y/N)")

    from ccg import utils as utils_module

    if _ensure_prompt_toolkit() and utils_module.PROMPT_TOOLKIT_AVAILABLE:
        try:
            prompt_fn = utils_module.prompt
            prompt_style = utils_module.PROMPT_STYLE
            ConfirmationValidator_cls = utils_module.ConfirmationValidator

            if prompt_fn is None:  # pragma: no cover
                raise AttributeError("prompt_fn is None")

            clean_prompt = strip_color_codes(prompt_display)

            validator = ConfirmationValidator_cls(default_yes) if ConfirmationValidator_cls else None  # type: ignore[operator]
            key_bindings = create_input_key_bindings(is_confirmation=True, default_yes=default_yes)
            from ccg.config import UI_CONFIG as UI_CFG

            bottom_toolbar = create_counter_toolbar(
                UI_CFG.CONFIRMATION_MAX_LENGTH, is_confirmation=True
            )

            user_input = prompt_fn(  # type: ignore[operator]
                f"{clean_prompt}: ",
                validator=validator,
                validate_while_typing=True,
                key_bindings=key_bindings,
                style=prompt_style,
                bottom_toolbar=bottom_toolbar,
            ).strip()
        except (EOFError, KeyboardInterrupt):  # pragma: no cover
            print()
            raise
        except (ImportError, AttributeError, TypeError, Exception):
            while True:
                try:
                    clean_prompt = strip_color_codes(prompt_display)

                    default_hint = "Y/n" if default_yes else "y/N"
                    print(
                        f"{WHITE}{INFO} Press Enter for default ({default_hint}) or type y/yes or n/no{RESET}"
                    )
                    user_input = input(f"{clean_prompt}: ").strip()

                    from ccg.config import UI_CONFIG as UI_CFG

                    if len(user_input) > UI_CFG.CONFIRMATION_MAX_LENGTH:
                        print_error(
                            f"CHARACTER LIMIT EXCEEDED! ({UI_CFG.CONFIRMATION_MAX_LENGTH} characters maximum)"
                        )
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

                from ccg.config import UI_CONFIG as UI_CFG

                if len(user_input) > UI_CFG.CONFIRMATION_MAX_LENGTH:
                    print_error(
                        f"CHARACTER LIMIT EXCEEDED! ({UI_CFG.CONFIRMATION_MAX_LENGTH} characters maximum)"
                    )
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


def _read_multiline_fallback(default_text: Optional[str], max_length: Optional[int]) -> str:
    """Fallback multiline input when prompt_toolkit is unavailable.

    Args:
        default_text: Optional default text
        max_length: Optional maximum character limit

    Returns:
        User input as string with newlines, or default_text if empty
    """
    if default_text:
        print(f"{BLUE}Enter new content (or press Enter twice to finish):{RESET}")
    else:
        print(f"{BLUE}Enter additional details (or press Enter twice to finish):{RESET}")
    if max_length:
        print(f"{BLUE}Maximum {max_length} characters allowed{RESET}")

    lines: List[str] = []
    empty_line_count = 0
    total_chars = 0
    from ccg.config import UI_CONFIG as UI_CFG

    max_line_length = UI_CFG.MULTILINE_MAX_LINE_LENGTH

    try:
        while True:
            try:
                if max_length and total_chars > 0:
                    remaining = max_length - total_chars
                    if remaining <= 0:
                        print_error(f"Character limit of {max_length} reached.")
                        break
                    elif remaining <= max_length * UI_CFG.CRITICAL_THRESHOLD:
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
                    print(" " * UI_CFG.LINE_CLEAR_LENGTH, end="\r")

                if len(line) > max_line_length:
                    print_error(f"Line too long! Maximum {max_line_length} characters per line.")
                    print_warning(f"Current line has {len(line)} characters. Please shorten it.")
                    continue

                potential_total = total_chars + len(line) + (1 if lines else 0)

                if max_length and potential_total > max_length:
                    remaining = max_length - total_chars
                    if remaining <= 0:  # pragma: no cover
                        print_error(f"Character limit of {max_length} reached.")
                        break
                    else:
                        print_error(f"Line too long! Only {remaining} characters remaining total.")
                        print_warning("Try a shorter line or finish your input.")
                        continue

                if not line:
                    empty_line_count += 1
                    if empty_line_count >= UI_CFG.EMPTY_LINES_TO_EXIT:
                        break
                    lines.append(line)
                    total_chars += 1
                else:
                    empty_line_count = 0
                    lines.append(line)
                    total_chars += len(line) + (1 if lines else 0)

            except (EOFError, KeyboardInterrupt):
                raise

    except KeyboardInterrupt:  # pragma: no cover
        print()
        raise

    while lines and not lines[-1]:
        lines.pop()

    result = "\n".join(lines).strip()

    if not result and default_text:
        return default_text

    return result


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
        With prompt_toolkit: Use Ctrl+D to submit
        Without prompt_toolkit: Press Enter twice (empty line) to finish
        Maximum 80 characters per line in fallback mode
        Displays character usage feedback after input
    """
    from ccg import utils as utils_module

    if _ensure_prompt_toolkit() and utils_module.PROMPT_TOOLKIT_AVAILABLE and max_length:
        try:
            prompt_multiline = utils_module.prompt
            prompt_style = utils_module.PROMPT_STYLE
            RealTimeCounterValidator_cls = utils_module.RealTimeCounterValidator

            if prompt_multiline is None:  # pragma: no cover
                raise AttributeError("prompt_multiline is None")

            print(f"{BLUE}Press Ctrl+D to finish. Press Enter for new line.{RESET}")
            print(f"{BLUE}Maximum {max_length} characters allowed{RESET}")

            validator = RealTimeCounterValidator_cls(max_length) if RealTimeCounterValidator_cls else None  # type: ignore[operator]
            key_bindings = create_input_key_bindings(max_length, multiline=True)
            bottom_toolbar = create_counter_toolbar(max_length)

            result_str = str(
                prompt_multiline(  # type: ignore[operator]
                    "",
                    multiline=True,
                    style=prompt_style,
                    default=default_text or "",
                    validator=validator,
                    validate_while_typing=True,
                    key_bindings=key_bindings,
                    bottom_toolbar=bottom_toolbar,
                )
            ).strip()

            return result_str

        except (EOFError, KeyboardInterrupt):  # pragma: no cover
            print()
            raise
        except (ImportError, AttributeError, TypeError, Exception):  # pragma: no cover
            pass

    return _read_multiline_fallback(default_text, max_length)


_ensure_prompt_toolkit()
