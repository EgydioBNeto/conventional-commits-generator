"""Helper functions for common operations."""

import shutil
import unicodedata
from typing import List, Tuple

from .config import (
    CHARACTER_USAGE_THRESHOLDS,
    COLORS,
    COMMIT_TYPES,
    DEFAULT_TERMINAL_SIZE,
    EMOJI_MAP,
)


def get_terminal_size() -> Tuple[int, int]:
    """Get terminal size with fallback."""
    try:
        return shutil.get_terminal_size()
    except Exception:
        return DEFAULT_TERMINAL_SIZE["WIDTH"], DEFAULT_TERMINAL_SIZE["HEIGHT"]


def clean_ansi_codes(text: str) -> str:
    """Remove ANSI color codes from text."""
    for code in COLORS.values():
        text = text.replace(code, "")
    return text


def get_visual_width(text: str) -> int:
    """Get the visual width of text considering Unicode characters."""
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


def convert_emoji_codes_to_real(text: str) -> str:
    """Convert emoji codes to real emojis."""
    result = text
    for code, emoji in EMOJI_MAP.items():
        result = result.replace(code, emoji)
    return result


def get_emoji_for_type(commit_type: str, use_code: bool = False) -> str:
    """Get emoji for commit type."""
    for type_info in COMMIT_TYPES:
        if type_info["type"] == commit_type:
            return type_info["emoji_code"] if use_code else type_info["emoji"]
    return ""


def calculate_usage_color_class(current_length: int, max_length: int) -> str:
    """Calculate color class based on character usage."""
    usage_ratio = current_length / max_length

    if usage_ratio <= CHARACTER_USAGE_THRESHOLDS["NORMAL"]:
        return "class:toolbar.text"
    elif usage_ratio <= CHARACTER_USAGE_THRESHOLDS["WARNING"]:
        return "class:toolbar.warning"
    else:
        return "class:toolbar.danger"


def format_character_usage_message(current_length: int, max_length: int) -> str:
    """Format character usage message with appropriate styling."""
    usage_ratio = current_length / max_length

    if usage_ratio >= 1.0:
        return f"{COLORS['GREEN']}{current_length}/{max_length} characters{COLORS['RESET']}"
    elif usage_ratio >= CHARACTER_USAGE_THRESHOLDS["HIGH_USAGE"]:
        return f"{COLORS['YELLOW']}{current_length}/{max_length} characters used{COLORS['RESET']}"
    else:
        return f"{COLORS['WHITE']}{current_length}/{max_length} characters used{COLORS['RESET']}"


def truncate_text_to_width(text: str, max_width: int) -> str:
    """Truncate text to fit within max width, accounting for visual width."""
    if get_visual_width(text) <= max_width:
        return text

    truncated = ""
    for char in text:
        test_text = truncated + char + "..."
        if get_visual_width(test_text) <= max_width:
            truncated += char
        else:
            break
    return truncated + "..."


def split_commit_hash_list(commits: List[Tuple]) -> List[str]:
    """Extract commit hashes from commit tuples."""
    return [commit[0] for commit in commits]


def find_matching_commits(commits: List[Tuple], selection: str) -> List[Tuple]:
    """Find commits matching the selection string."""
    return [c for c in commits if c[0].startswith(selection)]
