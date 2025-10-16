"""Unit tests for logging.py module."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestSetupLogging:
    """Tests for setup_logging function."""

    @patch("ccg.logging.Path.home")
    def test_setup_logging_creates_directory(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should create .ccg directory if it doesn't exist."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path
        log_dir = tmp_path / ".ccg"

        assert not log_dir.exists()

        setup_logging(verbose=False)

        assert log_dir.exists()
        assert log_dir.is_dir()

    @patch("ccg.logging.Path.home")
    def test_setup_logging_creates_log_file(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should create ccg.log file."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        setup_logging(verbose=False)

        # Log file should exist after first log message
        assert log_file.exists()

    @patch("ccg.logging.Path.home")
    def test_setup_logging_verbose_adds_console_handler(
        self, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should add console handler when verbose=True."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=True)

        logger = logging.getLogger("ccg")
        # Should have 2 handlers: file + console
        assert len(logger.handlers) == 2

        # Check that one handler is StreamHandler (console)
        handler_types = [type(h).__name__ for h in logger.handlers]
        assert "StreamHandler" in handler_types
        assert "RotatingFileHandler" in handler_types

    @patch("ccg.logging.Path.home")
    def test_setup_logging_no_verbose_no_console_handler(
        self, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should not add console handler when verbose=False."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=False)

        logger = logging.getLogger("ccg")
        # Should have only 1 handler: file
        assert len(logger.handlers) == 1

        # Check that it's a RotatingFileHandler
        assert type(logger.handlers[0]).__name__ == "RotatingFileHandler"

    @patch("ccg.logging.Path.home")
    def test_setup_logging_sets_debug_level(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should set logger level to DEBUG."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=False)

        logger = logging.getLogger("ccg")
        assert logger.level == logging.DEBUG

    @patch("ccg.logging.Path.home")
    def test_setup_logging_clears_existing_handlers(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should clear existing handlers before adding new ones."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        # Setup logging first time
        setup_logging(verbose=False)
        logger = logging.getLogger("ccg")
        first_handler_count = len(logger.handlers)

        # Setup logging second time
        setup_logging(verbose=True)
        second_handler_count = len(logger.handlers)

        # Should have exactly 2 handlers (not accumulated)
        assert second_handler_count == 2

    @patch("ccg.logging.Path.home")
    def test_setup_logging_file_handler_has_rotation(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should configure file handler with rotation (10MB, 5 backups)."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=False)

        logger = logging.getLogger("ccg")
        file_handler = logger.handlers[0]

        # Check that it's a RotatingFileHandler
        assert type(file_handler).__name__ == "RotatingFileHandler"

        # Check rotation settings
        assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
        assert file_handler.backupCount == 5

    @patch("ccg.logging.Path.home")
    def test_setup_logging_logs_initialization_message(
        self, mock_home: Mock, tmp_path: Path, capsys
    ) -> None:
        """Should log initialization message."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=True)  # verbose=True to see console output

        captured = capsys.readouterr()
        assert "CCG logging initialized" in captured.err
        assert "verbose=True" in captured.err

    @patch("ccg.logging.Path.home")
    def test_setup_logging_logs_file_path(self, mock_home: Mock, tmp_path: Path, capsys) -> None:
        """Should log the log file path."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path
        expected_log_file = tmp_path / ".ccg" / "ccg.log"

        setup_logging(verbose=True)

        captured = capsys.readouterr()
        assert "Log file:" in captured.err
        assert str(expected_log_file) in captured.err

    @patch("ccg.logging.Path.home")
    def test_setup_logging_formatter_has_correct_format(
        self, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should use correct log format with all required fields."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=False)

        logger = logging.getLogger("ccg")
        handler = logger.handlers[0]
        formatter = handler.formatter

        # Check format string contains all required elements
        assert formatter is not None
        format_string = formatter._fmt
        assert "%(asctime)s" in format_string
        assert "%(name)s" in format_string
        assert "%(levelname)s" in format_string
        assert "%(funcName)s" in format_string
        assert "%(lineno)d" in format_string
        assert "%(message)s" in format_string

    @patch("ccg.logging.Path.home")
    def test_setup_logging_file_handler_has_utf8_encoding(
        self, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should configure file handler with UTF-8 encoding."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=False)

        logger = logging.getLogger("ccg")
        file_handler = logger.handlers[0]

        # Check encoding
        assert file_handler.encoding == "utf-8"

    @patch("ccg.logging.Path.home")
    def test_setup_logging_console_handler_has_debug_level_when_verbose(
        self, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should set console handler to DEBUG level when verbose=True."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=True)

        logger = logging.getLogger("ccg")
        # Find the console handler
        console_handler = next(h for h in logger.handlers if type(h).__name__ == "StreamHandler")

        assert console_handler.level == logging.DEBUG

    @patch("ccg.logging.Path.home")
    def test_setup_logging_file_handler_always_debug_level(
        self, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should set file handler to DEBUG level regardless of verbose flag."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        # Test with verbose=False
        setup_logging(verbose=False)
        logger = logging.getLogger("ccg")
        file_handler = logger.handlers[0]
        assert file_handler.level == logging.DEBUG

        # Test with verbose=True
        setup_logging(verbose=True)
        logger = logging.getLogger("ccg")
        file_handler = next(h for h in logger.handlers if type(h).__name__ == "RotatingFileHandler")
        assert file_handler.level == logging.DEBUG


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger_instance(self) -> None:
        """Should return a logging.Logger instance."""
        from ccg.logging import get_logger

        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)

    def test_get_logger_prefixes_with_ccg(self) -> None:
        """Should prefix logger name with 'ccg.'."""
        from ccg.logging import get_logger

        logger = get_logger("test_module")

        assert logger.name == "ccg.test_module"

    def test_get_logger_different_names_return_different_loggers(self) -> None:
        """Should return different logger instances for different names."""
        from ccg.logging import get_logger

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1 is not logger2
        assert logger1.name != logger2.name

    def test_get_logger_same_name_returns_same_logger(self) -> None:
        """Should return same logger instance for same name."""
        from ccg.logging import get_logger

        logger1 = get_logger("module1")
        logger2 = get_logger("module1")

        assert logger1 is logger2

    def test_get_logger_with_dunder_name(self) -> None:
        """Should work correctly with __name__ pattern."""
        from ccg.logging import get_logger

        logger = get_logger("ccg.cli")

        assert logger.name == "ccg.ccg.cli"  # Double prefix (expected behavior)

    def test_get_logger_empty_name(self) -> None:
        """Should handle empty name."""
        from ccg.logging import get_logger

        logger = get_logger("")

        assert logger.name == "ccg."

    @patch("ccg.logging.Path.home")
    def test_get_logger_inherits_parent_configuration(
        self, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should inherit configuration from parent 'ccg' logger."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path

        # Setup logging first
        setup_logging(verbose=False)

        # Get a child logger
        logger = get_logger("test_module")

        # Child logger should inherit parent's level
        parent_logger = logging.getLogger("ccg")
        assert logger.parent == parent_logger


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    @patch("ccg.logging.Path.home")
    def test_logging_writes_to_file(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should write log messages to file."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        setup_logging(verbose=False)
        logger = get_logger("test")

        logger.info("Test message")

        # Read log file
        assert log_file.exists()
        log_content = log_file.read_text(encoding="utf-8")
        assert "Test message" in log_content

    @patch("ccg.logging.Path.home")
    def test_logging_includes_all_format_fields(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should include all format fields in log output."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        setup_logging(verbose=False)
        logger = get_logger("test_module")

        logger.warning("Test warning message")

        log_content = log_file.read_text(encoding="utf-8")
        # Check for timestamp (format: YYYY-MM-DD HH:MM:SS)
        assert "-" in log_content and ":" in log_content
        # Check for module name
        assert "ccg.test_module" in log_content
        # Check for log level
        assert "WARNING" in log_content
        # Check for function name
        assert "test_logging_includes_all_format_fields" in log_content
        # Check for message
        assert "Test warning message" in log_content

    @patch("ccg.logging.Path.home")
    def test_logging_verbose_prints_to_console(
        self, mock_home: Mock, tmp_path: Path, capsys
    ) -> None:
        """Should print to console when verbose=True."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=True)
        logger = get_logger("test")

        logger.info("Console test message")

        captured = capsys.readouterr()
        assert "Console test message" in captured.err

    @patch("ccg.logging.Path.home")
    def test_logging_non_verbose_does_not_print_to_console(
        self, mock_home: Mock, tmp_path: Path, capsys
    ) -> None:
        """Should not print to console when verbose=False."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path

        setup_logging(verbose=False)
        logger = get_logger("test")

        logger.info("Silent test message")

        captured = capsys.readouterr()
        # Should not see the message in console (only initialization messages)
        assert "Silent test message" not in captured.out

    @patch("ccg.logging.Path.home")
    def test_logging_handles_unicode_characters(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should correctly handle unicode characters in log messages."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        setup_logging(verbose=False)
        logger = get_logger("test")

        unicode_message = "Test with emoji ✨ and special chars: äöü, 日本語"
        logger.info(unicode_message)

        log_content = log_file.read_text(encoding="utf-8")
        assert unicode_message in log_content

    @patch("ccg.logging.Path.home")
    def test_logging_different_levels(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should correctly log different log levels."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        setup_logging(verbose=False)
        logger = get_logger("test")

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        log_content = log_file.read_text(encoding="utf-8")
        assert "DEBUG" in log_content
        assert "INFO" in log_content
        assert "WARNING" in log_content
        assert "ERROR" in log_content
        assert "CRITICAL" in log_content
        assert "Debug message" in log_content
        assert "Info message" in log_content
        assert "Warning message" in log_content
        assert "Error message" in log_content
        assert "Critical message" in log_content


class TestLoggingEdgeCases:
    """Edge case tests for logging functionality."""

    @patch("ccg.logging.Path.home")
    def test_setup_logging_multiple_calls_idempotent(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should be idempotent when called multiple times."""
        from ccg.logging import setup_logging

        mock_home.return_value = tmp_path

        # Call multiple times
        setup_logging(verbose=False)
        setup_logging(verbose=False)
        setup_logging(verbose=True)

        logger = logging.getLogger("ccg")
        # Should still have correct number of handlers
        assert len(logger.handlers) == 2  # file + console (last call was verbose=True)

    @patch("ccg.logging.Path.home")
    def test_setup_logging_handles_long_messages(self, mock_home: Mock, tmp_path: Path) -> None:
        """Should handle very long log messages."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        setup_logging(verbose=False)
        logger = get_logger("test")

        long_message = "A" * 10000
        logger.info(long_message)

        log_content = log_file.read_text(encoding="utf-8")
        assert long_message in log_content

    @patch("ccg.logging.Path.home")
    def test_setup_logging_handles_newlines_in_messages(
        self, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should handle newlines in log messages."""
        from ccg.logging import get_logger, setup_logging

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        setup_logging(verbose=False)
        logger = get_logger("test")

        multiline_message = "Line 1\nLine 2\nLine 3"
        logger.info(multiline_message)

        log_content = log_file.read_text(encoding="utf-8")
        assert "Line 1" in log_content
        assert "Line 2" in log_content
        assert "Line 3" in log_content
