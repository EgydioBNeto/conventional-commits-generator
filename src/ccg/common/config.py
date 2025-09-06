"""Configuration constants and settings for the Conventional Commits Generator."""

from typing import Dict, List

# Git configuration
DEFAULT_GIT_TIMEOUT = 60

# Terminal display thresholds
CHARACTER_USAGE_THRESHOLDS = {
    "NORMAL": 0.7,
    "WARNING": 0.9,
    "HIGH_USAGE": 0.8,
}

# Input limits
INPUT_LIMITS = {
    "type": 8,
    "scope": 16,
    "message": 64,
    "body": 512,
    "tag": 32,
    "tag_message": 512,
    "edit_message": 128,
    "confirmation": 3,
}

# Terminal dimensions fallback
DEFAULT_TERMINAL_SIZE = {
    "WIDTH": 80,
    "HEIGHT": 24,
}

# Box display configuration
COMMIT_MESSAGE_BOX = {
    "MIN_WIDTH": 50,
    "MAX_WIDTH": 100,
    "LEFT_PADDING": 4,
    "RIGHT_PADDING": 4,
    "MARGIN": 4,
}

# Multiline input configuration
MULTILINE_CONFIG = {
    "MAX_LINE_LENGTH": 80,
    "EMPTY_LINE_THRESHOLD": 2,
}

# ANSI color codes
COLORS = {
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "WHITE": "\033[97m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m",
    "RESET": "\033[0m",
}

# Symbols
SYMBOLS = {
    "CHECK": "✓",
    "CROSS": "✗",
    "ARROW": "→",
    "STAR": "★",
    "DIAMOND": "♦",
    "HEART": "♥",
    "WARNING": "⚠",
    "INFO": "ℹ",
    "BULLET": "•",
}

# ASCII Logo
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

# Commit types configuration
COMMIT_TYPES: List[Dict[str, str]] = [
    {
        "type": "feat",
        "emoji_code": ":sparkles:",
        "description": "A new feature for the user or a particular enhancement",
        "color": COLORS["GREEN"],
        "emoji": "✨",
    },
    {
        "type": "fix",
        "emoji_code": ":bug:",
        "description": "A bug fix for the user or a particular issue",
        "color": COLORS["RED"],
        "emoji": "🐛",
    },
    {
        "type": "chore",
        "emoji_code": ":wrench:",
        "description": "Routine tasks, maintenance, or minor updates",
        "color": COLORS["BLUE"],
        "emoji": "🔧",
    },
    {
        "type": "refactor",
        "emoji_code": ":hammer:",
        "description": "Code refactoring without changing its behavior",
        "color": COLORS["MAGENTA"],
        "emoji": "🔨",
    },
    {
        "type": "style",
        "emoji_code": ":lipstick:",
        "description": "Code style changes, formatting, or cosmetic improvements",
        "color": COLORS["CYAN"],
        "emoji": "💄",
    },
    {
        "type": "docs",
        "emoji_code": ":books:",
        "description": "Documentation-related changes",
        "color": COLORS["WHITE"],
        "emoji": "📚",
    },
    {
        "type": "test",
        "emoji_code": ":test_tube:",
        "description": "Adding or modifying tests",
        "color": COLORS["YELLOW"],
        "emoji": "🧪",
    },
    {
        "type": "build",
        "emoji_code": ":package:",
        "description": "Changes that affect the build system or external dependencies",
        "color": COLORS["YELLOW"],
        "emoji": "📦",
    },
    {
        "type": "revert",
        "emoji_code": ":rewind:",
        "description": "Reverts a previous commit",
        "color": COLORS["RED"],
        "emoji": "⏪",
    },
    {
        "type": "ci",
        "emoji_code": ":construction_worker:",
        "description": "Changes to CI configuration files and scripts",
        "color": COLORS["BLUE"],
        "emoji": "👷",
    },
    {
        "type": "perf",
        "emoji_code": ":zap:",
        "description": "A code change that improves performance",
        "color": COLORS["GREEN"],
        "emoji": "⚡",
    },
]

# Error messages
ERROR_MESSAGES = {
    "NOT_GIT_REPO": "Not a git repository. Please initialize one with 'git init'.",
    "EMPTY_COMMIT_MESSAGE": "Commit message cannot be empty.",
    "INVALID_COMMIT_FORMAT": "Invalid commit message format: {error}",
    "GIT_NOT_INSTALLED": "Git is not installed. Please install Git and try again.",
    "COMMAND_TIMEOUT": "Command timed out after {timeout} seconds: {command}",
    "CHARACTER_LIMIT_EXCEEDED": "CHARACTER LIMIT EXCEEDED! ({current}/{max})",
    "INVALID_CONFIRMATION": "Please enter 'y' or 'n'",
}

# Success messages
SUCCESS_MESSAGES = {
    "CHANGES_STAGED": "Changes staged successfully",
    "COMMIT_CREATED": "New commit successfully created!",
    "CHANGES_PUSHED": "Changes pushed successfully!",
    "COMMIT_CONFIRMED": "Commit message confirmed!",
}

# Emoji mappings
EMOJI_MAP = {
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
