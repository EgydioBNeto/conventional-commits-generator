#!/usr/bin/env python3
"""
Common logging utilities for CCG scripts.
Provides consistent logging format and colors across all scripts.
"""

import sys
from datetime import datetime
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


class Logger:
    """Standardized logger for CCG scripts."""

    def __init__(self, script_name: str):
        self.script_name = script_name

    def _log(self, level: str, message: str, color: str = Colors.NC) -> None:
        """Internal logging method."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(
            f"{color}[{timestamp}] {level} [{self.script_name}] {message}{Colors.NC}",
            file=sys.stderr,
        )

    def info(self, message: str) -> None:
        """Log info message."""
        self._log("ℹ️  INFO", message, Colors.BLUE)

    def success(self, message: str) -> None:
        """Log success message."""
        self._log("✅ SUCCESS", message, Colors.GREEN)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self._log("⚠️  WARNING", message, Colors.YELLOW)

    def error(self, message: str) -> None:
        """Log error message."""
        self._log("❌ ERROR", message, Colors.RED)

    def step(self, message: str) -> None:
        """Log step message."""
        self._log("🔄 STEP", message, Colors.PURPLE)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self._log("🐛 DEBUG", message, Colors.CYAN)


def get_logger(script_name: Optional[str] = None) -> Logger:
    """Get a logger instance for the script."""
    if script_name is None:
        # Extract script name from caller
        import inspect

        frame = inspect.currentframe().f_back
        script_name = frame.f_globals.get("__name__", "unknown")
        if script_name == "__main__":
            import os

            script_name = os.path.basename(frame.f_globals.get("__file__", "script"))
            script_name = script_name.replace(".py", "")

    return Logger(script_name)


# Convenience functions for backward compatibility
def log_info(message: str) -> None:
    """Log info message (backward compatibility)."""
    logger = get_logger()
    logger.info(message)


def log_success(message: str) -> None:
    """Log success message (backward compatibility)."""
    logger = get_logger()
    logger.success(message)


def log_warning(message: str) -> None:
    """Log warning message (backward compatibility)."""
    logger = get_logger()
    logger.warning(message)


def log_error(message: str) -> None:
    """Log error message (backward compatibility)."""
    logger = get_logger()
    logger.error(message)


def log_step(message: str) -> None:
    """Log step message (backward compatibility)."""
    logger = get_logger()
    logger.step(message)
