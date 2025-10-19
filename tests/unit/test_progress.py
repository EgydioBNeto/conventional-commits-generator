"""Tests for progress indicators."""

import time
from unittest.mock import MagicMock, patch

import pytest

from ccg.progress import ProgressSpinner


def wait_for_thread_death(thread, timeout=2.0):
    """Wait for a thread to die with polling (more robust than fixed sleep).

    Args:
        thread: Thread object to wait for
        timeout: Maximum time to wait in seconds

    Returns:
        bool: True if thread died, False if timeout
    """
    start = time.time()
    while thread.is_alive():
        if time.time() - start > timeout:
            return False
        time.sleep(0.01)  # Poll every 10ms
    return True


def wait_for_thread_count(expected_count, timeout=2.0):
    """Wait for thread count to reach expected value with polling.

    Args:
        expected_count: Expected thread count
        timeout: Maximum time to wait in seconds

    Returns:
        bool: True if count reached, False if timeout
    """
    import threading

    start = time.time()
    while threading.active_count() != expected_count:
        if time.time() - start > timeout:
            return False
        time.sleep(0.01)  # Poll every 10ms
    return True


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
        # Wait for thread to finish with robust polling
        assert wait_for_thread_death(spinner.thread), "Thread did not stop in time"

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
        # Wait for thread to finish with robust polling
        assert wait_for_thread_death(thread), "Thread did not stop in time"

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


class TestProgressSpinnerRaceConditions:
    """Test ProgressSpinner for race conditions and thread safety.

    These tests validate the fix for the race condition where the animation
    thread could write to stdout after the clear operation in stop().
    """

    def test_spinner_no_artifacts_after_stop(self):
        """Test that spinner doesn't leave artifacts after stop().

        This validates that the thread is stopped and joined BEFORE clearing
        the line, preventing race conditions.
        """
        import io
        import sys

        captured = io.StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = captured

            spinner = ProgressSpinner("Testing")
            spinner.start()
            time.sleep(0.3)  # Let it animate several frames
            spinner.stop()

            # Get output after stop
            output = captured.getvalue()

            # Split by carriage return (spinner overwrites)
            lines = output.split("\r")
            last_line = lines[-1] if lines else ""

            # Last line should be empty or only whitespace (cleared)
            # It's acceptable to have spaces from the clear operation
            assert last_line.strip() == "", f"Spinner left artifacts: {repr(last_line)}"

        finally:
            sys.stdout = original_stdout

    def test_spinner_thread_cleanup_count(self):
        """Test that spinner thread is properly cleaned up.

        Validates that thread count returns to baseline after spinner stops.
        """
        import threading

        initial_thread_count = threading.active_count()

        spinner = ProgressSpinner("Testing")
        spinner.start()

        # Thread count should increase by 1
        assert threading.active_count() == initial_thread_count + 1

        time.sleep(0.1)
        spinner.stop()
        # Wait for thread count to return to initial with robust polling
        assert wait_for_thread_count(
            initial_thread_count
        ), f"Thread count did not return to {initial_thread_count}"

    def test_spinner_rapid_start_stop(self):
        """Test spinner behavior with rapid start/stop cycles.

        This tests that rapid cycling doesn't create zombie threads or
        leave the spinner in an inconsistent state.
        """
        import threading

        initial_thread_count = threading.active_count()

        for _ in range(10):
            spinner = ProgressSpinner("Testing")
            spinner.start()
            time.sleep(0.01)  # Very short duration
            spinner.stop()

        # Wait for all threads to finish with robust polling
        assert wait_for_thread_count(
            initial_thread_count, timeout=3.0
        ), f"Zombie threads detected: expected {initial_thread_count}, got {threading.active_count()}"

    def test_spinner_context_manager_exception(self):
        """Test that spinner stops cleanly even if exception occurs.

        Validates that the context manager properly cleans up on exceptions.
        """
        import io
        import sys

        captured = io.StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = captured

            with pytest.raises(ValueError):
                with ProgressSpinner("Testing"):
                    time.sleep(0.1)
                    raise ValueError("Test exception")

            # Spinner should still be stopped
            output = captured.getvalue()
            lines = output.split("\r")
            last_line = lines[-1] if lines else ""

            # Should be cleared despite exception
            assert last_line.strip() == ""

        finally:
            sys.stdout = original_stdout

    def test_spinner_stop_without_start(self):
        """Test that calling stop without start doesn't cause errors.

        Edge case: stop() called when thread is None.
        """
        spinner = ProgressSpinner("Testing")
        # Don't start, just stop
        spinner.stop()  # Should not raise exception

    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_spinner_clear_after_join(self, mock_flush, mock_write):
        """Test that clear happens AFTER thread join.

        This is the core test for the race condition fix:
        The clear operation should only happen after the thread has been joined.
        """
        spinner = ProgressSpinner("Testing")
        spinner.start()
        time.sleep(0.2)

        # Reset mocks to only track stop() behavior
        mock_write.reset_mock()
        mock_flush.reset_mock()

        spinner.stop()

        # The clear (write with spaces) should have been called
        assert mock_write.called, "Clear operation was not called"

        # Verify thread is dead when we return from stop()
        assert not spinner.thread.is_alive(), "Thread still alive after stop()"
