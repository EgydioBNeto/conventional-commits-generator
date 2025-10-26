"""Unit tests for git_strategies.py module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from ccg.git_strategies import (
    EDIT_STRATEGIES,
    AmendStrategy,
    FilterBranchStrategy,
    edit_commit_with_strategy,
)


class TestAmendStrategy:
    """Tests for AmendStrategy class."""

    def test_can_handle_latest_commit(self):
        """Test can_handle returns True for latest commit."""
        strategy = AmendStrategy()
        assert strategy.can_handle("abc123", "abc123") is True

    def test_can_handle_old_commit(self):
        """Test can_handle returns False for old commit."""
        strategy = AmendStrategy()
        assert strategy.can_handle("abc123", "def456") is False

    def test_get_description(self):
        """Test get_description returns correct description."""
        strategy = AmendStrategy()
        description = strategy.get_description()
        assert "amend" in description.lower()
        assert "latest" in description.lower()

    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_ccg_dir_creation_failure(self, mock_ensure_ccg_dir):
        """Test edit handles CCG directory creation failure."""
        mock_ensure_ccg_dir.return_value = None

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature")

        assert result is False

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_success(
        self,
        mock_ensure_ccg_dir,
        mock_create_secure,
        mock_invalidate,
        mock_run_git,
    ):
        """Test edit successfully amends commit."""
        # Mock ensure_ccg_directory returning a Path
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        # Mock the secure temp file creation
        mock_message_file = MagicMock(spec=Path)
        mock_message_file.__str__.return_value = (
            "/home/user/.ccg/commit_message_amend_abc123.tmp"
        )
        mock_message_file.exists.return_value = True
        mock_create_secure.return_value = mock_message_file

        mock_run_git.return_value = (True, None)

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature", "Body text")

        assert result is True
        mock_create_secure.assert_called_once_with(
            mock_ccg_dir,
            "commit_message_amend_abc123.tmp",
            "feat: new feature\n\nBody text",
        )
        mock_run_git.assert_called_once_with(
            [
                "git",
                "commit",
                "--amend",
                "-F",
                "/home/user/.ccg/commit_message_amend_abc123.tmp",
                "--no-verify",
            ],
            "Failed to amend commit message for 'abc123'",
            "Commit message for 'abc123' updated successfully",
        )
        mock_invalidate.assert_called_once()
        mock_message_file.unlink.assert_called_once()

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_without_body(
        self, mock_ensure_ccg_dir, mock_create_secure, mock_run_git
    ):
        """Test edit with only subject line (no body)."""
        # Mock ensure_ccg_directory returning a Path
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        # Mock the secure temp file creation
        mock_message_file = MagicMock(spec=Path)
        mock_message_file.__str__.return_value = (
            "/home/user/.ccg/commit_message_amend_abc123.tmp"
        )
        mock_message_file.exists.return_value = True
        mock_create_secure.return_value = mock_message_file

        mock_run_git.return_value = (True, None)

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature")

        assert result is True
        mock_create_secure.assert_called_once_with(
            mock_ccg_dir, "commit_message_amend_abc123.tmp", "feat: new feature"
        )

    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_temp_file_creation_failure(
        self, mock_ensure_ccg_dir, mock_create_secure
    ):
        """Test edit handles temp file creation failure."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        mock_create_secure.side_effect = IOError("Permission denied")

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature")

        assert result is False

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_git_command_failure(
        self, mock_ensure_ccg_dir, mock_create_secure, mock_run_git
    ):
        """Test edit handles git command failure."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        # Mock the secure temp file creation
        mock_message_file = MagicMock(spec=Path)
        mock_message_file.__str__.return_value = (
            "/home/user/.ccg/commit_message_amend_abc123.tmp"
        )
        mock_message_file.exists.return_value = True
        mock_create_secure.return_value = mock_message_file

        mock_run_git.return_value = (False, None)

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature")

        assert result is False
        mock_message_file.unlink.assert_called_once()

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_cleanup_on_unlink_failure(
        self,
        mock_ensure_ccg_dir,
        mock_create_secure,
        mock_invalidate,
        mock_run_git,
    ):
        """Test edit handles cleanup failure gracefully."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        # Mock the secure temp file creation
        mock_message_file = MagicMock(spec=Path)
        mock_message_file.__str__.return_value = (
            "/home/user/.ccg/commit_message_amend_abc123.tmp"
        )
        mock_message_file.exists.return_value = True
        mock_message_file.unlink.side_effect = OSError("Cleanup failed")
        mock_create_secure.return_value = mock_message_file

        mock_run_git.return_value = (True, None)

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature")

        assert result is True


class TestFilterBranchStrategy:
    """Tests for FilterBranchStrategy class."""

    def test_can_handle_latest_commit(self):
        """Test can_handle returns False for latest commit."""
        strategy = FilterBranchStrategy()
        assert strategy.can_handle("abc123", "abc123") is False

    def test_can_handle_old_commit(self):
        """Test can_handle returns True for old commit."""
        strategy = FilterBranchStrategy()
        assert strategy.can_handle("abc123", "def456") is True

    def test_get_description(self):
        """Test get_description returns correct description."""
        strategy = FilterBranchStrategy()
        description = strategy.get_description()
        assert "filter-branch" in description.lower()
        assert "old" in description.lower() or "history" in description.lower()

    @patch("ccg.git_strategies.print_success")
    @patch("ccg.git_strategies.print_info")
    @patch("ccg.git_strategies.print_process")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.create_executable_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_success(
        self,
        mock_spinner,
        mock_ensure_ccg_dir,
        mock_create_exec,
        mock_create_secure,
        mock_invalidate,
        mock_run_git,
        mock_print_process,
        mock_print_info,
        mock_print_success,
    ):
        """Test edit successfully edits old commit."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True

        mock_create_secure.return_value = mock_message_file
        mock_create_exec.return_value = mock_script_file

        mock_run_git.return_value = (True, "Success")

        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature", "Body text")

        assert result is True
        mock_invalidate.assert_called_once()
        mock_print_success.assert_called_once()
        mock_print_process.assert_called_once()
        mock_print_info.assert_called_once()

    @patch("ccg.git_strategies.print_success")
    @patch("ccg.git_strategies.print_info")
    @patch("ccg.git_strategies.print_process")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.create_executable_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_with_initial_commit_flag(
        self,
        mock_spinner,
        mock_ensure_ccg_dir,
        mock_create_exec,
        mock_create_secure,
        mock_invalidate,
        mock_run_git,
        mock_print_process,
        mock_print_info,
        mock_print_success,
    ):
        """Test edit handles initial commit flag correctly."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True

        mock_create_secure.return_value = mock_message_file
        mock_create_exec.return_value = mock_script_file

        mock_run_git.return_value = (True, "Success")

        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature", is_initial_commit=True)

        assert result is True
        mock_print_success.assert_called_once()
        mock_print_process.assert_called_once()
        mock_print_info.assert_called_once()

    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_ccg_dir_creation_failure(self, mock_ensure_ccg_dir):
        """Test edit handles CCG directory creation failure."""
        mock_ensure_ccg_dir.return_value = None

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is False

    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_message_file_creation_failure(
        self, mock_ensure_ccg_dir, mock_create_secure
    ):
        """Test edit handles message file creation failure."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        mock_create_secure.side_effect = IOError("Write failed")

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is False

    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.create_executable_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    def test_edit_script_file_creation_failure(
        self, mock_ensure_ccg_dir, mock_create_exec, mock_create_secure
    ):
        """Test edit handles script file creation failure."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        mock_message_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True

        # Message file succeeds, but script file fails
        mock_create_secure.return_value = mock_message_file
        mock_create_exec.side_effect = PermissionError("Permission denied")

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is False

    @patch("builtins.print")
    @patch("ccg.git_strategies.print_error")
    @patch("ccg.git_strategies.print_info")
    @patch("ccg.git_strategies.print_process")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.create_executable_temp_file")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_git_command_failure(
        self,
        mock_spinner,
        mock_ensure_ccg_dir,
        mock_run_git,
        mock_create_exec,
        mock_create_secure,
        mock_print_process,
        mock_print_info,
        mock_print_error,
        mock_print,
    ):
        """Test edit handles git command failure."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True

        mock_create_secure.return_value = mock_message_file
        mock_create_exec.return_value = mock_script_file

        mock_run_git.return_value = (False, "Error occurred")

        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is False
        assert mock_print_error.call_count == 2
        mock_print.assert_called_once_with("Error occurred")
        mock_print_process.assert_called_once()
        mock_print_info.assert_called_once()

    @patch("ccg.git_strategies.print_success")
    @patch("ccg.git_strategies.print_info")
    @patch("ccg.git_strategies.print_process")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.create_executable_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_cleanup_on_success(
        self,
        mock_spinner,
        mock_ensure_ccg_dir,
        mock_create_exec,
        mock_create_secure,
        mock_invalidate,
        mock_run_git,
        mock_print_process,
        mock_print_info,
        mock_print_success,
    ):
        """Test edit cleans up temporary files on success."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True

        mock_create_secure.return_value = mock_message_file
        mock_create_exec.return_value = mock_script_file

        mock_run_git.return_value = (True, "Success")

        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is True
        mock_message_file.unlink.assert_called_once()
        mock_script_file.unlink.assert_called_once()

    @patch("ccg.git_strategies.print_success")
    @patch("ccg.git_strategies.print_info")
    @patch("ccg.git_strategies.print_process")
    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.create_executable_temp_file")
    @patch("ccg.git_strategies.ensure_ccg_directory")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_cleanup_failure_handled_gracefully(
        self,
        mock_spinner,
        mock_ensure_ccg_dir,
        mock_create_exec,
        mock_create_secure,
        mock_invalidate,
        mock_run_git,
        mock_print_process,
        mock_print_info,
        mock_print_success,
    ):
        """Test edit handles cleanup failure gracefully."""
        mock_ccg_dir = Path("/home/user/.ccg")
        mock_ensure_ccg_dir.return_value = mock_ccg_dir

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True
        mock_message_file.unlink.side_effect = OSError("Cleanup failed")

        mock_create_secure.return_value = mock_message_file
        mock_create_exec.return_value = mock_script_file

        mock_run_git.return_value = (True, "Success")

        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is True


class TestEditStrategiesRegistry:
    """Tests for EDIT_STRATEGIES registry."""

    def test_registry_contains_strategies(self):
        """Test EDIT_STRATEGIES contains both strategies."""
        assert len(EDIT_STRATEGIES) == 2
        assert any(isinstance(s, AmendStrategy) for s in EDIT_STRATEGIES)
        assert any(isinstance(s, FilterBranchStrategy) for s in EDIT_STRATEGIES)


class TestEditCommitWithStrategy:
    """Tests for edit_commit_with_strategy function."""

    @patch("ccg.git_strategies.EDIT_STRATEGIES")
    def test_selects_correct_strategy_for_latest_commit(self, mock_strategies):
        """Test function selects AmendStrategy for latest commit."""
        mock_amend = MagicMock(spec=AmendStrategy)
        mock_amend.can_handle.return_value = True
        mock_amend.edit.return_value = True

        mock_filter = MagicMock(spec=FilterBranchStrategy)
        mock_filter.can_handle.return_value = False

        mock_strategies.__iter__.return_value = [mock_amend, mock_filter]

        result = edit_commit_with_strategy("abc123", "abc123", "feat: new feature")

        assert result is True
        mock_amend.can_handle.assert_called_once_with("abc123", "abc123")
        mock_amend.edit.assert_called_once_with("abc123", "feat: new feature", None)

    @patch("ccg.git_strategies.EDIT_STRATEGIES")
    def test_selects_correct_strategy_for_old_commit(self, mock_strategies):
        """Test function selects FilterBranchStrategy for old commit."""
        mock_amend = MagicMock(spec=AmendStrategy)
        mock_amend.can_handle.return_value = False

        mock_filter = MagicMock(spec=FilterBranchStrategy)
        mock_filter.can_handle.return_value = True
        mock_filter.edit.return_value = True

        mock_strategies.__iter__.return_value = [mock_amend, mock_filter]

        result = edit_commit_with_strategy(
            "abc123", "def456", "feat: new feature", "Body text"
        )

        assert result is True
        mock_filter.can_handle.assert_called_once_with("abc123", "def456")
        mock_filter.edit.assert_called_once_with(
            "abc123", "feat: new feature", "Body text"
        )

    @patch("ccg.git_strategies.EDIT_STRATEGIES")
    def test_passes_kwargs_to_strategy(self, mock_strategies):
        """Test function passes kwargs to selected strategy."""
        mock_filter = MagicMock(spec=FilterBranchStrategy)
        mock_filter.can_handle.return_value = True
        mock_filter.edit.return_value = True

        mock_strategies.__iter__.return_value = [mock_filter]

        result = edit_commit_with_strategy(
            "abc123", "def456", "feat: new feature", is_initial_commit=True
        )

        assert result is True
        mock_filter.edit.assert_called_once_with(
            "abc123", "feat: new feature", None, is_initial_commit=True
        )

    @patch("ccg.git_strategies.EDIT_STRATEGIES")
    def test_returns_false_when_no_strategy_found(self, mock_strategies):
        """Test function returns False when no strategy can handle commit."""
        mock_amend = MagicMock(spec=AmendStrategy)
        mock_amend.can_handle.return_value = False

        mock_filter = MagicMock(spec=FilterBranchStrategy)
        mock_filter.can_handle.return_value = False

        mock_strategies.__iter__.return_value = [mock_amend, mock_filter]

        result = edit_commit_with_strategy("abc123", "def456", "feat: new feature")

        assert result is False
