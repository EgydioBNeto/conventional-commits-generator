"""Tests to prevent spinner overlap with success/error messages.

These tests ensure that ProgressSpinner is properly closed before any
success or error messages are printed, preventing visual overlap issues
in the terminal.
"""

from typing import Callable, List
from unittest.mock import MagicMock, Mock, patch

import pytest

from ccg.git import git_commit, git_push, pull_from_remote
from ccg.git_strategies import FilterBranchStrategy


class TestSpinnerNoOverlap:
    """Test that spinners complete before printing success/error messages."""

    @pytest.mark.parametrize(
        "function,args,kwargs,success_result",
        [
            (git_commit, ("feat: test",), {}, True),
            (git_commit, ("feat: test",), {}, False),
            (git_push, (), {"set_upstream": True}, True),
            (git_push, (), {}, False),
            (pull_from_remote, (), {}, True),
            (pull_from_remote, (), {}, False),
        ],
    )
    @patch("ccg.git.ProgressSpinner")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git.print_success")
    @patch("ccg.git.print_error")
    def test_git_operations_print_after_spinner(
        self,
        mock_error: Mock,
        mock_success: Mock,
        mock_run: Mock,
        mock_spinner: Mock,
        function: Callable,
        args: tuple,
        kwargs: dict,
        success_result: bool,
    ) -> None:
        """Test git operations print success/error AFTER spinner exits."""
        # Setup mocks
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance
        mock_run.return_value = (success_result, None if success_result else "Error")

        # Track call order
        call_order: List[str] = []
        mock_spinner_instance.__enter__.side_effect = lambda: (
            call_order.append("spinner_enter"),
            mock_spinner_instance,
        )[1]
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append(
            "spinner_exit"
        )
        mock_success.side_effect = lambda msg: call_order.append("print_success")
        mock_error.side_effect = lambda msg: call_order.append("print_error")

        # Apply all patches (some functions don't need all, but it's harmless)
        with patch("ccg.git.invalidate_repository_cache"):
            with patch("ccg.git.get_remote_name", return_value="origin"):
                with patch("ccg.git.get_current_branch", return_value="main"):
                    function(*args, **kwargs)

        # Verify correct message is called AFTER spinner exit
        expected_print = "print_success" if success_result else "print_error"
        assert "spinner_enter" in call_order
        assert "spinner_exit" in call_order
        assert expected_print in call_order
        assert call_order.index("spinner_exit") < call_order.index(expected_print)


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
        mock_spinner_instance.__exit__.side_effect = lambda *args: call_order.append(
            "spinner_exit"
        )
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
