"""Utilities and styling for the Conventional Commits Generator."""

import os
import shutil
from typing import Dict, List, Optional

# Import prompt_toolkit with better error handling
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.styles import Style

    # Initialize history objects only if library is available
    type_history = InMemoryHistory()
    scope_history = InMemoryHistory()
    message_history = InMemoryHistory()

    # Define style for prompt_toolkit
    prompt_style = Style.from_dict({
        "prompt": "#00AFFF bold",
        "command": "#00FF00 bold",
        "option": "#FF00FF",
    })

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    # Define dummy variables to avoid reference errors
    type_history = None
    scope_history = None
    message_history = None
    prompt_style = None

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


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{GREEN}{BOLD}{CHECK} {message}{RESET}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{BLUE}{INFO} {message}{RESET}")


def print_process(message: str) -> None:
    """Print a process message."""
    print(f"{YELLOW}{ARROW} {message}{RESET}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{RED}{BOLD}{CROSS} {message}{RESET}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{MAGENTA}{WARNING} {message}{RESET}")


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
            # Choose appropriate history based on type
            history = None
            if history_type == "type":
                history = type_history
            elif history_type == "scope":
                history = scope_history
            elif history_type == "message":
                history = message_history

            # Remove ANSI codes from prompt text to avoid issues
            clean_prompt = prompt_text
            for code in [RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD, UNDERLINE, RESET]:
                clean_prompt = clean_prompt.replace(code, "")

            # Use prompt_toolkit with basic configuration
            result = prompt(
                f"{clean_prompt}: ",
                history=history,
                style=prompt_style
            ).strip()

            return result
        except Exception:
            # Fall back to standard input on error
            return input(f"{prompt_text}: ").strip()
    else:
        # Fall back to the standard input() function
        return input(f"{prompt_text}: ").strip()
