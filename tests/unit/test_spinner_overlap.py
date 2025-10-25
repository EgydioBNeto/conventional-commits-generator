"""Tests to prevent spinner overlap with success/error messages.

These tests ensure that ProgressSpinner is properly closed before any
success or error messages are printed, preventing visual overlap issues
in the terminal.
"""

from typing import List
from unittest.mock import MagicMock, Mock, patch

from ccg.git import git_commit, git_push, pull_from_remote
from ccg.git_strategies import FilterBranchStrategy


class TestSpinnerNoOverlap:
    """Test that spinners complete before printing success/error messages."""

    @patch("ccg.git.invalidate_repository_cache")
    @patch("ccg.git.print_success")
    @patch("ccg.git.print_error")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git.ProgressSpinner")
    def test_git_commit_success_message_after_spinner(
        self,
        mock_spinner: Mock,
        mock_run: Mock,
        mock_error: Mock,
        mock_success: Mock,
        mock_invalidate: Mock,
    ) -> None:
        """Test git_commit prints success message AFTER spinner exits."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance
        mock_run.return_value = (True, None)

        # Track call order
        call_order: List[str] = []
        mock_spinner_instance.__enter__.side_effect = lambda: (
            call_order.append("spinner_enter"),
            mock_spinner_instance,
        )[1]
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append("spinner_exit")
        mock_success.side_effect = lambda msg: call_order.append("print_success")

        git_commit("feat: test")

        # Verify success message is called AFTER spinner exit
        assert call_order == ["spinner_enter", "spinner_exit", "print_success"]

    @patch("ccg.git.invalidate_repository_cache")
    @patch("ccg.git.print_error")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git.ProgressSpinner")
    def test_git_commit_error_message_after_spinner(
        self,
        mock_spinner: Mock,
        mock_run: Mock,
        mock_error: Mock,
        mock_invalidate: Mock,
    ) -> None:
        """Test git_commit prints error message AFTER spinner exits."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance
        mock_run.return_value = (False, None)

        call_order: List[str] = []
        mock_spinner_instance.__enter__.side_effect = lambda: (
            call_order.append("spinner_enter"),
            mock_spinner_instance,
        )[1]
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append("spinner_exit")
        mock_error.side_effect = lambda msg: call_order.append("print_error")

        git_commit("feat: test")

        assert call_order == ["spinner_enter", "spinner_exit", "print_error"]

    @patch("ccg.git.print_success")
    @patch("ccg.git.get_remote_name")
    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git.ProgressSpinner")
    def test_git_push_success_message_after_spinner(
        self,
        mock_spinner: Mock,
        mock_run: Mock,
        mock_branch: Mock,
        mock_remote: Mock,
        mock_success: Mock,
    ) -> None:
        """Test git_push prints success AFTER spinner exits."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance
        mock_run.return_value = (True, None)
        mock_branch.return_value = "main"
        mock_remote.return_value = "origin"

        call_order: List[str] = []
        mock_spinner_instance.__enter__.side_effect = lambda: (
            call_order.append("spinner_enter"),
            mock_spinner_instance,
        )[1]
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append("spinner_exit")
        mock_success.side_effect = lambda msg: call_order.append("print_success")

        git_push(set_upstream=True)

        assert "spinner_exit" in call_order
        assert "print_success" in call_order
        assert call_order.index("spinner_exit") < call_order.index("print_success")

    @patch("ccg.git.print_error")
    @patch("ccg.git.get_remote_name")
    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git.ProgressSpinner")
    def test_git_push_error_message_after_spinner(
        self,
        mock_spinner: Mock,
        mock_run: Mock,
        mock_branch: Mock,
        mock_remote: Mock,
        mock_error: Mock,
    ) -> None:
        """Test git_push prints error AFTER spinner exits."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance
        mock_run.return_value = (False, "Error")
        mock_branch.return_value = "main"
        mock_remote.return_value = "origin"

        call_order: List[str] = []
        mock_spinner_instance.__enter__.side_effect = lambda: (
            call_order.append("spinner_enter"),
            mock_spinner_instance,
        )[1]
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append("spinner_exit")
        mock_error.side_effect = lambda msg: call_order.append("print_error")

        git_push()

        assert "spinner_exit" in call_order
        assert "print_error" in call_order
        assert call_order.index("spinner_exit") < call_order.index("print_error")

    @patch("ccg.git.print_success")
    @patch("ccg.git.get_remote_name")
    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git.ProgressSpinner")
    def test_pull_from_remote_success_after_spinner(
        self,
        mock_spinner: Mock,
        mock_run: Mock,
        mock_branch: Mock,
        mock_remote: Mock,
        mock_success: Mock,
    ) -> None:
        """Test pull_from_remote prints success AFTER spinner exits."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance
        mock_run.return_value = (True, None)
        mock_branch.return_value = "main"
        mock_remote.return_value = "origin"

        call_order: List[str] = []
        mock_spinner_instance.__enter__.side_effect = lambda: (
            call_order.append("spinner_enter"),
            mock_spinner_instance,
        )[1]
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append("spinner_exit")
        mock_success.side_effect = lambda msg: call_order.append("print_success")

        pull_from_remote()

        assert call_order == ["spinner_enter", "spinner_exit", "print_success"]

    @patch("ccg.git.print_error")
    @patch("ccg.git.get_remote_name")
    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git.ProgressSpinner")
    def test_pull_from_remote_error_after_spinner(
        self,
        mock_spinner: Mock,
        mock_run: Mock,
        mock_branch: Mock,
        mock_remote: Mock,
        mock_error: Mock,
    ) -> None:
        """Test pull_from_remote prints error AFTER spinner exits."""
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance
        mock_run.return_value = (False, None)
        mock_branch.return_value = "main"
        mock_remote.return_value = "origin"

        call_order: List[str] = []
        mock_spinner_instance.__enter__.side_effect = lambda: (
            call_order.append("spinner_enter"),
            mock_spinner_instance,
        )[1]
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append("spinner_exit")
        mock_error.side_effect = lambda msg: call_order.append("print_error")

        pull_from_remote()

        assert call_order == ["spinner_enter", "spinner_exit", "print_error"]


class TestRunGitCommandWithSpinner:
    """Test that run_git_command never prints inside spinner context."""

    @patch("ccg.git.print_success")
    @patch("ccg.git._execute_git_command")
    @patch("ccg.git.ProgressSpinner")
    def test_run_git_command_no_print_inside_spinner(
        self, mock_spinner: Mock, mock_execute: Mock, mock_success: Mock
    ) -> None:
        """Test run_git_command with empty messages doesn't print inside spinner."""
        from ccg.git import run_git_command

        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance
        mock_execute.return_value = (True, "output", "")

        call_order: List[str] = []
        mock_spinner_instance.__enter__.side_effect = lambda: (
            call_order.append("spinner_enter"),
            mock_spinner_instance,
        )[1]
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append("spinner_exit")
        mock_success.side_effect = lambda msg: call_order.append("print_success")

        # Call inside spinner context (simulating what git_commit does)
        with mock_spinner("Test operation"):
            success, output = run_git_command(
                ["git", "test"],
                "",  # Empty error message
                "",  # Empty success message
            )

        # Verify no print_success was called
        assert "print_success" not in call_order
        assert call_order == ["spinner_enter", "spinner_exit"]
