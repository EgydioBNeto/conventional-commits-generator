"""Logging configuration for CCG."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ccg.config import LOGGING_CONFIG


def setup_logging(verbose: bool = False) -> None:
    r"""Configure structured logging for CCG.

    Creates a rotating log file in ~/.ccg/ccg.log with the following behavior:
    - File logs: Always DEBUG level, rotates at 10MB, keeps 5 backups
    - Console logs: Disabled by default, DEBUG level if verbose=True

    Args:
        verbose: If True, enable DEBUG console output to stderr. Otherwise no console output

    Example:
        >>> setup_logging(verbose=True)
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("This will be logged to file and console")

    Log Location:
        - Linux/Mac: ~/.ccg/ccg.log
        - Windows: %USERPROFILE%\.ccg\ccg.log
    """
    # Create log directory
    log_dir = Path.home() / ".ccg"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "ccg.log"

    # Configure root logger for ccg package
    logger = logging.getLogger("ccg")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Format with context
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation (10MB, 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOGGING_CONFIG.MAX_LOG_SIZE_BYTES,
        backupCount=LOGGING_CONFIG.BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Console handler (only if verbose)
    # Use stderr to avoid conflicts with spinner animations on stdout
    if verbose:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

    # Log startup
    logger.info("=" * 60)
    logger.info("CCG logging initialized (verbose=%s)", verbose)
    logger.info("Log file: %s", log_file)
    logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return logging.getLogger(f"ccg.{name}")
