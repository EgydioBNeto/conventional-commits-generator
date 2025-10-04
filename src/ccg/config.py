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
    COMMIT_COUNT: int = 6  # For selecting commits to edit/delete


@dataclass(frozen=True)
class GitConfig:
    """Git operation configuration."""

    DEFAULT_TIMEOUT: int = 60
    PULL_TIMEOUT: int = 120
    FILTER_BRANCH_TIMEOUT: int = 300
    PRE_COMMIT_TIMEOUT: int = 120


@dataclass(frozen=True)
class UIConfig:
    """UI configuration."""

    MIN_BOX_WIDTH: int = 50
    MAX_BOX_WIDTH: int = 100
    DEFAULT_TERM_WIDTH: int = 80
    DEFAULT_TERM_HEIGHT: int = 24


# Singleton instances
INPUT_LIMITS = InputLimits()
GIT_CONFIG = GitConfig()
UI_CONFIG = UIConfig()
