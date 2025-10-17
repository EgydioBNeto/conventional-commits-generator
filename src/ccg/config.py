"""Configuration constants for CCG."""

from dataclasses import dataclass


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


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration."""

    MAX_LOG_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: int = 5
    THREAD_JOIN_TIMEOUT: float = 1.0


INPUT_LIMITS = InputLimits()
GIT_CONFIG = GitConfig()
UI_CONFIG = UIConfig()
LOGGING_CONFIG = LoggingConfig()
