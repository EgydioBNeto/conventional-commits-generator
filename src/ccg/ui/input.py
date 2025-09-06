"""Input handling and UI components."""

import shutil
from typing import Callable, Optional, Tuple

from ..common.config import CHARACTER_USAGE_THRESHOLDS, COLORS, INPUT_LIMITS, MULTILINE_CONFIG
from ..common.helpers import clean_ansi_codes, format_character_usage_message
from .validation import validate_confirmation_input

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
        "tag_message": InMemoryHistory(),
        "edit_message": InMemoryHistory(),
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

    class CCGConfirmationValidator(Validator):
        """
        Unified validator for yes/no confirmations in CCG interface.

        Provides consistent validation for confirmation prompts throughout
        the CCG application with clear error messages.
        """

        def validate(self, document):
            text = document.text

            if not text:
                return

            result = validate_confirmation_input(text)
            if result is None:
                if len(text) > 3:
                    raise ValidationError(message="Please enter 'y' or 'n'", cursor_position=3)
                else:
                    raise ValidationError(
                        message="Please enter 'y' or 'n'", cursor_position=len(text)
                    )

    class CCGLengthValidator(Validator):
        """
        Unified validator for character limits in CCG inputs.

        Enforces character limits across all CCG input fields with
        real-time feedback and consistent error reporting.

        Args:
            max_length: Maximum allowed characters
        """

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

    # Backward compatibility aliases
    ConfirmationValidator = CCGConfirmationValidator
    RealTimeCounterValidator = CCGLengthValidator

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    HISTORIES = {}
    PROMPT_STYLE = None

    class CCGConfirmationValidator:
        """Fallback validator when prompt_toolkit is not available."""

        def validate(self, document):
            pass

    class CCGLengthValidator:
        """Fallback validator when prompt_toolkit is not available."""

        def __init__(self, max_length: int):
            self.max_length = max_length

        def validate(self, document):
            pass

    # Backward compatibility aliases
    ConfirmationValidator = CCGConfirmationValidator
    RealTimeCounterValidator = CCGLengthValidator

    KeyBindings = object  # Dummy for type hints when not available


def create_counter_toolbar(max_length: int, is_confirmation: bool = False) -> Callable:
    """Create a toolbar that shows character count."""

    def get_toolbar_tokens():
        try:
            from prompt_toolkit.application.current import get_app

            app = get_app()
            if app and app.current_buffer:
                current_length = len(app.current_buffer.text)

                if current_length <= max_length * CHARACTER_USAGE_THRESHOLDS["NORMAL"]:
                    color = "class:toolbar.text"
                elif current_length <= max_length * CHARACTER_USAGE_THRESHOLDS["WARNING"]:
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
                except Exception:
                    term_width = 80

                padding = max(0, term_width - len(counter_text) - 4)
                return [("", " " * padding), (color, counter_text)]

            return [("class:toolbar.text", f"0/{3 if is_confirmation else max_length}")]
        except Exception:
            return [("class:toolbar.text", f"0/{3 if is_confirmation else max_length}")]

    return get_toolbar_tokens


def create_input_key_bindings(
    max_length: int = 0, is_confirmation: bool = False, multiline: bool = False
):
    """Create key bindings for input handling."""
    kb = KeyBindings()

    if not multiline:

        @kb.add(Keys.ControlM)
        def _(event):
            # For confirmation prompts with empty input, don't auto-fill
            # Let the confirmation logic handle the default based on the prompt text
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
            except Exception:
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
    """Read input with optional history and validation."""
    if max_length is None and history_type:
        max_length = INPUT_LIMITS.get(history_type, 0)

    if history_type == "body":
        return read_multiline_input(default_text, max_length)

    if PROMPT_TOOLKIT_AVAILABLE:
        try:
            clean_prompt = clean_ansi_codes(prompt_text)
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
                print(f"    {format_character_usage_message(len(result), max_length)}")

            return result
        except (EOFError, KeyboardInterrupt):
            # User pressed Ctrl+D/Ctrl+C - exit immediately instead of falling back
            raise
        except Exception:
            return read_input_fallback(prompt_text, max_length, default_text)
    else:
        return read_input_fallback(prompt_text, max_length, default_text)


def read_input_fallback(
    prompt_text: str, max_length: Optional[int] = None, default_text: Optional[str] = None
) -> str:
    """Fallback input reader when prompt_toolkit is not available."""
    from ..common.config import SYMBOLS
    from .display import print_error, print_info, print_warning

    clean_prompt = clean_ansi_codes(prompt_text)

    if default_text:
        print(f"Default: {default_text}")

    if max_length:
        print(
            f"{COLORS['WHITE']}{SYMBOLS['INFO']} Maximum {max_length} characters allowed{COLORS['RESET']}"
        )

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
                print(f"    {format_character_usage_message(len(user_input), max_length)}")

            return user_input

        except KeyboardInterrupt:
            raise
        except EOFError:
            # User pressed Ctrl+D or reached EOF
            from .display import print_info

            print_info("Goodbye!")
            raise SystemExit(0)


def confirm_user_action(
    prompt_text: str, success_message: Optional[str] = None, cancel_message: Optional[str] = None
) -> bool:
    """
    Get user confirmation with y/n input.

    Supports both [Y/n] (default yes) and [y/N] (default no) patterns.
    The default is determined by the capitalized letter in the prompt.

    Args:
        prompt_text: Confirmation prompt with [Y/n] or [y/N] pattern
        success_message: Message to show on yes/true response
        cancel_message: Message to show on no/false response

    Returns:
        True for yes/confirm, False for no/cancel

    Example:
        confirm_user_action("Continue? [Y/n]")  # Defaults to yes
        confirm_user_action("Delete all? [y/N]")  # Defaults to no
    """
    from ..common.config import SYMBOLS
    from .display import print_error, print_info, print_success

    user_input = ""
    used_default = False

    if PROMPT_TOOLKIT_AVAILABLE:
        try:
            clean_prompt = clean_ansi_codes(prompt_text)
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

            # Check if default was used
            if not user_input:
                if "[Y/n]" in prompt_text:
                    user_input = "y"
                    used_default = True
                elif "[y/N]" in prompt_text:
                    user_input = "n"
                    used_default = True
        except (EOFError, KeyboardInterrupt):
            # User pressed Ctrl+D/Ctrl+C - exit immediately instead of falling back
            raise
        except Exception:
            user_input, used_default = _confirm_fallback(prompt_text)
    else:
        user_input, used_default = _confirm_fallback(prompt_text)

    result = validate_confirmation_input(user_input)

    if result:
        if success_message:
            print_success(success_message)
        return True
    else:
        if cancel_message:
            print_info(cancel_message)
        return False


def _confirm_fallback(prompt_text: str) -> Tuple[str, bool]:
    """Fallback confirmation input."""
    from ..common.config import SYMBOLS
    from .display import print_error, print_info

    used_default = False

    while True:
        try:
            clean_prompt = clean_ansi_codes(prompt_text)
            user_input = input(f"{clean_prompt}: ").strip()

            # Handle default case when input is empty
            if not user_input:
                if "[Y/n]" in prompt_text:
                    user_input = "y"
                    used_default = True
                elif "[y/N]" in prompt_text:
                    user_input = "n"
                    used_default = True

            if len(user_input) > 3:
                print_error("CHARACTER LIMIT EXCEEDED! (3 characters maximum)")
                continue

            result = validate_confirmation_input(user_input)
            if result is not None:
                return user_input, used_default
            print_error("Please enter 'y' or 'n'")

        except KeyboardInterrupt:
            raise
        except EOFError:
            # User pressed Ctrl+D or reached EOF
            from .display import print_info

            print_info("Goodbye!")
            raise SystemExit(0)


def read_multiline_input(
    default_text: Optional[str] = None, max_length: Optional[int] = None
) -> str:
    """Read multiline input."""
    from ..common.config import SYMBOLS
    from .display import print_error, print_info, print_warning

    if PROMPT_TOOLKIT_AVAILABLE and max_length:
        try:
            print(
                f"{COLORS['BLUE']}Press Ctrl+D or Escape+Enter to finish. Press Enter for new line.{COLORS['RESET']}"
            )
            print(f"{COLORS['BLUE']}Maximum {max_length} characters allowed{COLORS['RESET']}")

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
                print(f"    {format_character_usage_message(len(result), max_length)}")

            return result

        except Exception:
            pass

    return _read_multiline_fallback(default_text, max_length)


def _read_multiline_fallback(
    default_text: Optional[str] = None, max_length: Optional[int] = None
) -> str:
    """Fallback multiline input reader."""
    from ..common.config import SYMBOLS
    from .display import print_error, print_info, print_warning

    if default_text:
        print(
            f"{COLORS['BLUE']}Enter new content (or press Enter twice to finish):{COLORS['RESET']}"
        )
    else:
        print(
            f"{COLORS['BLUE']}Enter additional details (or press Enter twice to finish):{COLORS['RESET']}"
        )
    if max_length:
        print(f"{COLORS['BLUE']}Maximum {max_length} characters allowed{COLORS['RESET']}")

    lines = []
    empty_line_count = 0
    total_chars = 0
    max_line_length = MULTILINE_CONFIG["MAX_LINE_LENGTH"]

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
                            f"    {COLORS['YELLOW']}{SYMBOLS['WARNING']} {total_chars}/{max_length} characters{COLORS['RESET']}",
                            end="\r",
                        )
                    else:
                        print(
                            f"    {COLORS['WHITE']}{SYMBOLS['INFO']} {total_chars}/{max_length} characters{COLORS['RESET']}",
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
                    if empty_line_count >= MULTILINE_CONFIG["EMPTY_LINE_THRESHOLD"]:
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

    if result and max_length:
        print(f"    {format_character_usage_message(len(result), max_length)}")

    return result
