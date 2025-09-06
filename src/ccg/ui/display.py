"""Display utilities and formatting for the Conventional Commits Generator."""

from typing import Optional

from ..common.config import ASCII_LOGO, COLORS, COMMIT_MESSAGE_BOX, SYMBOLS
from ..common.helpers import (
    convert_emoji_codes_to_real,
    get_terminal_size,
    get_visual_width,
    truncate_text_to_width,
)
from .input import confirm_user_action, read_input


def print_logo() -> None:
    """Print the application logo."""
    print(f"{COLORS['WHITE']}{COLORS['BOLD']}{ASCII_LOGO}{COLORS['RESET']}")


def print_section(text: str) -> None:
    """Print a section header with border."""
    print()
    print(f"{COLORS['BLUE']}{COLORS['BOLD']}┌{'─' * (len(text) + 2)}┐{COLORS['RESET']}")
    print(f"{COLORS['BLUE']}{COLORS['BOLD']}│ {text} │{COLORS['RESET']}")
    print(f"{COLORS['BLUE']}{COLORS['BOLD']}└{'─' * (len(text) + 2)}┘{COLORS['RESET']}")


def print_message(
    color: str, symbol: str, message: str, bold: bool = False, end: str = "\n"
) -> None:
    """Print a formatted message with color and symbol."""
    bold_code = COLORS["BOLD"] if bold else ""
    print(f"{color}{bold_code}{symbol} {message}{COLORS['RESET']}", end=end)


def print_success(message: str, end: str = "\n") -> None:
    """Print a success message."""
    print_message(COLORS["GREEN"], SYMBOLS["CHECK"], message, bold=True, end=end)


def print_info(message: str, end: str = "\n") -> None:
    """Print an info message."""
    print_message(COLORS["WHITE"], SYMBOLS["INFO"], message, end=end)


def print_process(message: str) -> None:
    """Print a process message."""
    print_message(COLORS["YELLOW"], SYMBOLS["ARROW"], message)


def print_error(message: str) -> None:
    """Print an error message."""
    print_message(COLORS["RED"], SYMBOLS["CROSS"], message, bold=True)


def print_warning(message: str) -> None:
    """Print a warning message."""
    print_message(COLORS["MAGENTA"], SYMBOLS["WARNING"], message)


def format_commit_message_box(
    commit_message_header: str, commit_body: Optional[str] = None
) -> None:
    """Format and display a commit message with clear visual separation for review."""
    display_header = convert_emoji_codes_to_real(commit_message_header)

    print(f"{COLORS['BOLD']}{COLORS['WHITE']}{display_header}{COLORS['RESET']}")

    if commit_body:
        print()
        # Split body into lines and print each without indentation
        body_lines = commit_body.split("\n")
        for line in body_lines:
            if line.strip():  # Only print non-empty lines
                print(f"{COLORS['WHITE']}{line}{COLORS['RESET']}")
            else:
                print()  # Empty line

    print()
