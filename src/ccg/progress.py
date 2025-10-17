"""Progress indicators for long-running operations."""

import sys
import threading
import time
from types import TracebackType
from typing import Optional

from ccg.config import LOGGING_CONFIG
from ccg.utils import RESET, YELLOW


class ProgressSpinner:
    """Show animated spinner during long operations."""

    def __init__(self, message: str = "Processing") -> None:
        """Initialize progress spinner.

        Args:
            message: Message to display alongside the spinner
        """
        self.message = message
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._frame_delay = 0.1  # 100ms per frame

    def __enter__(self) -> "ProgressSpinner":
        """Context manager entry - start spinner."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Context manager exit - stop spinner."""
        self.stop()

    def start(self) -> None:
        """Start spinner animation in background thread."""
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop spinner animation and clear line."""
        self.stop_event.set()

        # Clear immediately to prevent overlap with subsequent output
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.flush()

        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=LOGGING_CONFIG.THREAD_JOIN_TIMEOUT)

        # Clear again to ensure spinner is completely gone
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.flush()

    def _spin(self) -> None:
        """Animation loop - runs in background thread."""
        idx = 0
        while not self.stop_event.is_set():
            frame = self._frames[idx % len(self._frames)]
            # Print spinner with message
            sys.stdout.write(f"\r{YELLOW}{frame} {self.message}...{RESET}")
            sys.stdout.flush()
            idx += 1
            time.sleep(self._frame_delay)
