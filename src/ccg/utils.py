"""Utilities and styling for the Conventional Commits Generator."""

import os
import shutil
from typing import Dict, List, Optional, Any, Callable

# ASCII Logo for CCG
ASCII_LOGO = r"""
   ______   ______   ______
  / ____/  / ____/  / ____/
 / /      / /      / / __
/ /___   / /___   / /_/ /
\____/   \____/   \____/

 Conventional Commits Generator
"""

# Import prompt_toolkit with better error handling
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style

    # Initialize history objects
    HISTORIES = {
        "type": InMemoryHistory(),
        "scope": InMemoryHistory(),
        "message": InMemoryHistory()
    }

    # Define style for prompt_toolkit
    PROMPT_STYLE = Style.from_dict({
        "prompt": "#00AFFF bold",
        "command": "#00FF00 bold",
        "option": "#FF00FF",
    })

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    # Define dummy variables to avoid reference errors
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

# Symbols for better UX
CHECK = "✓"
CROSS = "✗"
ARROW = "→"
STAR = "★"
DIAMOND = "♦"
HEART = "♥"
WARNING = "⚠"
INFO = "ℹ"
BULLET = "•"

# Get terminal size with fallback
try:
    TERM_WIDTH, TERM_HEIGHT = shutil.get_terminal_size()
except Exception:
    TERM_WIDTH, TERM_HEIGHT = 80, 24

# Commit types with descriptions and styling
COMMIT_TYPES: List[Dict[str, str]] = [
    {
        "type": "feat",
        "description": "A new feature for the user or a particular enhancement",
        "color": GREEN,
        "symbol": STAR,
    },
    {
        "type": "fix",
        "description": "A bug fix for the user or a particular issue",
        "color": RED,
        "symbol": HEART,
    },
    {
        "type": "chore",
        "description": "Routine tasks, maintenance, or minor updates",
        "color": BLUE,
        "symbol": BULLET,
    },
    {
        "type": "refactor",
        "description": "Code refactoring without changing its behavior",
        "color": MAGENTA,
        "symbol": DIAMOND,
    },
    {
        "type": "style",
        "description": "Code style changes, formatting, or cosmetic improvements",
        "color": CYAN,
        "symbol": BULLET,
    },
    {
        "type": "docs",
        "description": "Documentation-related changes",
        "color": WHITE,
        "symbol": INFO,
    },
    {
        "type": "test",
        "description": "Adding or modifying tests",
        "color": YELLOW,
        "symbol": CHECK,
    },
    {
        "type": "build",
        "description": "Changes that affect the build system or external dependencies",
        "color": YELLOW,
        "symbol": BULLET,
    },
    {
        "type": "revert",
        "description": "Reverts a previous commit",
        "color": RED,
        "symbol": ARROW,
    },
    {
        "type": "ci",
        "description": "Changes to CI configuration files and scripts",
        "color": BLUE,
        "symbol": BULLET,
    },
    {
        "type": "perf",
        "description": "A code change that improves performance",
        "color": GREEN,
        "symbol": ARROW,
    },
]


def print_logo() -> None:
    """Print the ASCII logo."""
    print(f"{CYAN}{BOLD}{ASCII_LOGO}{RESET}")


def print_header(text: str) -> None:
    """Print a stylized header."""
    print()
    print(f"{CYAN}{BOLD}{'═' * TERM_WIDTH}{RESET}")
    print(f"{CYAN}{BOLD}{text.center(TERM_WIDTH)}{RESET}")
    print(f"{CYAN}{BOLD}{'═' * TERM_WIDTH}{RESET}")
    print()


def print_section(text: str) -> None:
    """Print a section divider."""
    print()
    print(f"{BLUE}{BOLD}┌{'─' * (len(text) + 2)}┐{RESET}")
    print(f"{BLUE}{BOLD}│ {text} │{RESET}")
    print(f"{BLUE}{BOLD}└{'─' * (len(text) + 2)}┘{RESET}")


def print_message(color: str, symbol: str, message: str, bold: bool = False) -> None:
    """Print a formatted message with the given color and symbol.

    Args:
        color: ANSI color code
        symbol: Symbol to display
        message: Message to print
        bold: Whether to make the text bold
    """
    bold_code = BOLD if bold else ""
    print(f"{color}{bold_code}{symbol} {message}{RESET}")


def print_success(message: str) -> None:
    """Print a success message."""
    print_message(GREEN, CHECK, message, bold=True)


def print_info(message: str) -> None:
    """Print an info message."""
    print_message(BLUE, INFO, message)


def print_process(message: str) -> None:
    """Print a process message."""
    print_message(YELLOW, ARROW, message)


def print_error(message: str) -> None:
    """Print an error message."""
    print_message(RED, CROSS, message, bold=True)


def print_warning(message: str) -> None:
    """Print a warning message."""
    print_message(MAGENTA, WARNING, message)


def print_complete() -> None:
    """Print a completion message."""
    print()
    print(f"{GREEN}{BOLD}{STAR} All done! {STAR}{RESET}")
    print()


def read_input(prompt_text: str, history_type: Optional[str] = None) -> str:
    """Read user input with a given prompt, supporting arrow keys and history.

    Args:
        prompt_text: The text to display as the prompt
        history_type: Type of history to use ("type", "scope", "message", or None)

    Returns:
        The user input as a string
    """
    if PROMPT_TOOLKIT_AVAILABLE:
        try:
            # Get appropriate history based on type
            history = HISTORIES.get(history_type) if history_type else None

            # Remove ANSI codes from prompt text to avoid issues
            clean_prompt = prompt_text
            for code in [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD, UNDERLINE, RESET]:
                clean_prompt = clean_prompt.replace(code, "")

            # Use prompt_toolkit with basic configuration
            result = prompt(
                f"{clean_prompt}: ",
                history=history,
                style=PROMPT_STYLE
            ).strip()

            return result
        except Exception:
            # Fall back to standard input on error
            return input(f"{prompt_text}: ").strip()
    else:
        # Fall back to the standard input() function
        return input(f"{prompt_text}: ").strip()
