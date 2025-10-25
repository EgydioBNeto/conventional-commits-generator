"""Configuration constants for CCG."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class InputLimits:
    """Input length limits for various fields."""

    TYPE: int = 8
    SCOPE: int = 16
    MESSAGE: int = 64
    BODY: int = 512
    TAG: int = 32
    TAG_MESSAGE: int = 512
    EDIT_MESSAGE: int = 128
    CONFIRMATION: int = 3
    COMMIT_COUNT: int = 6
    COMMIT_HASH: int = 7


@dataclass(frozen=True)
class GitConfig:
    """Git operation configuration."""

    DEFAULT_TIMEOUT: int = 60
    PULL_TIMEOUT: int = 120
    FILTER_BRANCH_TIMEOUT: int = 300
    PRE_COMMIT_TIMEOUT: int = 120
    REBASE_TIMEOUT: int = 120
    REMOTE_CHECK_TIMEOUT: int = 15
    TAG_PUSH_TIMEOUT: int = 30
    STATUS_CHECK_TIMEOUT: int = 10
    SHORT_HASH_LENGTH: int = 7
    MAX_LOG_ERROR_CHARS: int = 500
    LOG_PREVIEW_LENGTH: int = 80


@dataclass(frozen=True)
class UIConfig:
    """UI configuration."""

    MIN_BOX_WIDTH: int = 50
    MAX_BOX_WIDTH: int = 100
    DEFAULT_TERM_WIDTH: int = 80
    DEFAULT_TERM_HEIGHT: int = 24
    MULTILINE_MAX_LINE_LENGTH: int = 80
    CONFIRMATION_MAX_LENGTH: int = 3
    HELP_FLAGS: tuple[str, ...] = ("-h", "--help")
    TERMINAL_CLEAR_WIDTH: int = 100
    LINE_CLEAR_LENGTH: int = 50
    EMPTY_LINES_TO_EXIT: int = 2
    WARNING_THRESHOLD: float = 0.7
    DANGER_THRESHOLD: float = 0.9
    CRITICAL_THRESHOLD: float = 0.2
    ARGPARSE_HELP_POSITION: int = 50
    ARGPARSE_MAX_WIDTH: int = 100


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration."""

    MAX_LOG_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: int = 5
    THREAD_JOIN_TIMEOUT: float = 1.0


# ANSI Color codes for terminal output
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

# Commit types configuration with emoji and color coding
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

INPUT_LIMITS = InputLimits()
GIT_CONFIG = GitConfig()
UI_CONFIG = UIConfig()
LOGGING_CONFIG = LoggingConfig()
