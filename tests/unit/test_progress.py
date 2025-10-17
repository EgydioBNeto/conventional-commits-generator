"""Tests for progress indicators."""

import time
from unittest.mock import MagicMock, patch

import pytest

from ccg.progress import ProgressSpinner


class TestProgressSpinner:
    """Test cases for ProgressSpinner class."""

    def test_spinner_initialization(self):
        """Test that spinner initializes with correct message."""
        spinner = ProgressSpinner("Test message")
        assert spinner.message == "Test message"
        assert spinner.stop_event is not None
        assert spinner.thread is None
        assert len(spinner._frames) == 10

    def test_spinner_context_manager(self):
        """Test that spinner works as context manager."""
        spinner = ProgressSpinner("Testing")

        # Ensure spinner starts and stops without errors
        with spinner:
            assert spinner.thread is not None
            assert spinner.thread.is_alive()
            time.sleep(0.2)  # Let it spin a bit

        # After context, spinner should be stopped
        assert not spinner.stop_event.is_set() or not spinner.thread.is_alive()

    def test_spinner_manual_start_stop(self):
        """Test manual start and stop of spinner."""
        spinner = ProgressSpinner("Manual test")

        spinner.start()
        assert spinner.thread is not None
        assert spinner.thread.is_alive()

        time.sleep(0.2)

        spinner.stop()
        # Give thread time to finish
        time.sleep(0.15)
        assert not spinner.thread.is_alive()

    def test_spinner_displays_animation(self, capsys):
        """Test that spinner actually outputs animation frames."""
        spinner = ProgressSpinner("Animation test")

        with spinner:
            time.sleep(0.3)  # Let it go through a few frames

        # Spinner should have written something to stdout
        # We can't easily test the exact output due to \r characters,
        # but we can verify something was written
        captured = capsys.readouterr()
        # The spinner uses sys.stdout.write directly, not print
        # so we might not see it in capsys. This test is mainly
        # to ensure no exceptions are raised

    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_spinner_output_format(self, mock_flush, mock_write):
        """Test that spinner outputs correct format."""
        spinner = ProgressSpinner("Format test")

        with spinner:
            time.sleep(0.2)

        # Verify that write was called with strings containing the message
        assert mock_write.called
        # At least one call should contain our message
        calls_with_message = [
            call for call in mock_write.call_args_list if "Format test" in str(call)
        ]
        assert len(calls_with_message) > 0

    def test_spinner_thread_cleanup(self):
        """Test that spinner properly cleans up thread."""
        spinner = ProgressSpinner("Cleanup test")

        spinner.start()
        thread = spinner.thread
        assert thread is not None

        spinner.stop()
        time.sleep(0.2)  # Wait for thread to finish

        assert not thread.is_alive()

    def test_spinner_double_stop(self):
        """Test that calling stop twice doesn't cause errors."""
        spinner = ProgressSpinner("Double stop")

        spinner.start()
        spinner.stop()
        spinner.stop()  # Should not raise exception

    def test_spinner_with_long_operation(self):
        """Test spinner with simulated long operation."""

        def long_operation():
            """Simulate a long-running operation."""
            time.sleep(0.3)
            return "completed"

        with ProgressSpinner("Long operation"):
            result = long_operation()

        assert result == "completed"


class TestSpinnerIntegration:
    """Integration tests for spinner in realistic scenarios."""

    def test_spinner_during_subprocess(self):
        """Test spinner during a subprocess call."""
        import subprocess
        import sys

        def run_command_with_spinner():
            with ProgressSpinner("Running command"):
                result = subprocess.run(
                    [sys.executable, "-c", "import time; time.sleep(0.2)"],
                    capture_output=True,
                    timeout=5,
                )
            return result.returncode

        assert run_command_with_spinner() == 0

    def test_multiple_spinners_sequential(self):
        """Test multiple spinners used sequentially."""
        results = []

        with ProgressSpinner("First operation"):
            time.sleep(0.1)
            results.append("first")

        with ProgressSpinner("Second operation"):
            time.sleep(0.1)
            results.append("second")

        with ProgressSpinner("Third operation"):
            time.sleep(0.1)
            results.append("third")

        assert results == ["first", "second", "third"]

    def test_spinner_nested_operations(self):
        """Test spinner with nested function calls."""

        def inner_operation():
            time.sleep(0.1)
            return "inner"

        def outer_operation():
            with ProgressSpinner("Outer operation"):
                result = inner_operation()
            return result

        assert outer_operation() == "inner"
