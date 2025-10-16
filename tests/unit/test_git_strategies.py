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

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.tempfile.NamedTemporaryFile")
    @patch("ccg.git_strategies.os.path.exists")
    @patch("ccg.git_strategies.os.unlink")
    def test_edit_success(
        self,
        mock_unlink,
        mock_exists,
        mock_temp_file,
        mock_invalidate,
        mock_run_git,
    ):
        """Test edit successfully amends commit."""
        temp_file_name = "/tmp/test_commit_msg"
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_file.name = temp_file_name
        mock_temp_file.return_value = mock_file

        mock_run_git.return_value = (True, None)
        mock_exists.return_value = True

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature", "Body text")

        assert result is True
        mock_file.write.assert_called_once_with("feat: new feature\n\nBody text")
        mock_run_git.assert_called_once_with(
            ["git", "commit", "--amend", "-F", temp_file_name, "--no-verify"],
            "Failed to amend commit message for 'abc123'",
            "Commit message for 'abc123' updated successfully",
        )
        mock_invalidate.assert_called_once()
        mock_unlink.assert_called_once_with(temp_file_name)

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.tempfile.NamedTemporaryFile")
    @patch("ccg.git_strategies.os.path.exists")
    @patch("ccg.git_strategies.os.unlink")
    def test_edit_without_body(self, mock_unlink, mock_exists, mock_temp_file, mock_run_git):
        """Test edit with only subject line (no body)."""
        temp_file_name = "/tmp/test_commit_msg"
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_file.name = temp_file_name
        mock_temp_file.return_value = mock_file

        mock_run_git.return_value = (True, None)
        mock_exists.return_value = True

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature")

        assert result is True
        mock_file.write.assert_called_once_with("feat: new feature")

    @patch("ccg.git_strategies.tempfile.NamedTemporaryFile")
    def test_edit_temp_file_creation_failure(self, mock_temp_file):
        """Test edit handles temp file creation failure."""
        mock_temp_file.side_effect = IOError("Permission denied")

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature")

        assert result is False

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.tempfile.NamedTemporaryFile")
    @patch("ccg.git_strategies.os.path.exists")
    @patch("ccg.git_strategies.os.unlink")
    def test_edit_git_command_failure(self, mock_unlink, mock_exists, mock_temp_file, mock_run_git):
        """Test edit handles git command failure."""
        temp_file_name = "/tmp/test_commit_msg"
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_file.name = temp_file_name
        mock_temp_file.return_value = mock_file

        mock_run_git.return_value = (False, None)
        mock_exists.return_value = True

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new feature")

        assert result is False
        mock_unlink.assert_called_once_with(temp_file_name)

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.tempfile.NamedTemporaryFile")
    @patch("ccg.git_strategies.os.path.exists")
    @patch("ccg.git_strategies.os.unlink")
    def test_edit_cleanup_on_unlink_failure(
        self,
        mock_unlink,
        mock_exists,
        mock_temp_file,
        mock_invalidate,
        mock_run_git,
    ):
        """Test edit handles cleanup failure gracefully."""
        temp_file_name = "/tmp/test_commit_msg"
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=None)
        mock_file.name = temp_file_name
        mock_temp_file.return_value = mock_file

        mock_run_git.return_value = (True, None)
        mock_exists.return_value = True
        mock_unlink.side_effect = OSError("Cleanup failed")

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

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.Path")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_success(self, mock_spinner, mock_path, mock_invalidate, mock_run_git):
        """Test edit successfully edits old commit."""
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir
        mock_ccg_dir.__truediv__ = MagicMock()

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True

        def ccg_dir_side_effect(name):
            if "commit_message" in name:
                return mock_message_file
            elif "msg_filter" in name:
                return mock_script_file
            return MagicMock()

        mock_ccg_dir.__truediv__.side_effect = ccg_dir_side_effect

        mock_run_git.return_value = (True, "Success")

        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature", "Body text")

        assert result is True
        mock_invalidate.assert_called_once()

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.Path")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_with_initial_commit_flag(
        self, mock_spinner, mock_path, mock_invalidate, mock_run_git
    ):
        """Test edit handles initial commit flag correctly."""
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir
        mock_ccg_dir.__truediv__ = MagicMock()

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True

        def ccg_dir_side_effect(name):
            if "commit_message" in name:
                return mock_message_file
            elif "msg_filter" in name:
                return mock_script_file
            return MagicMock()

        mock_ccg_dir.__truediv__.side_effect = ccg_dir_side_effect

        mock_run_git.return_value = (True, "Success")

        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature", is_initial_commit=True)

        assert result is True

    @patch("ccg.git_strategies.Path")
    def test_edit_ccg_dir_creation_failure(self, mock_path):
        """Test edit handles CCG directory creation failure."""
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir
        mock_ccg_dir.mkdir.side_effect = OSError("Permission denied")

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is False

    @patch("ccg.git_strategies.Path")
    def test_edit_message_file_creation_failure(self, mock_path):
        """Test edit handles message file creation failure."""
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir

        mock_message_file = MagicMock(spec=Path)
        mock_message_file.write_text.side_effect = IOError("Write failed")
        mock_ccg_dir.__truediv__.return_value = mock_message_file

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is False

    @patch("ccg.git_strategies.Path")
    def test_edit_script_file_creation_failure(self, mock_path):
        """Test edit handles script file creation failure."""
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)

        # Message file succeeds, but script file fails
        call_count = [0]

        def side_effect(name):
            if "commit_message" in name:
                return mock_message_file
            elif "msg_filter" in name:
                call_count[0] += 1
                return mock_script_file
            return MagicMock()

        mock_ccg_dir.__truediv__.side_effect = side_effect
        mock_script_file.write_text.side_effect = PermissionError("Permission denied")

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is False

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.Path")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_git_command_failure(self, mock_spinner, mock_path, mock_run_git):
        """Test edit handles git command failure."""
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir
        mock_ccg_dir.__truediv__ = MagicMock()

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True

        def ccg_dir_side_effect(name):
            if "commit_message" in name:
                return mock_message_file
            elif "msg_filter" in name:
                return mock_script_file
            return MagicMock()

        mock_ccg_dir.__truediv__.side_effect = ccg_dir_side_effect

        mock_run_git.return_value = (False, "Error occurred")

        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new feature")

        assert result is False

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.Path")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_cleanup_on_success(self, mock_spinner, mock_path, mock_invalidate, mock_run_git):
        """Test edit cleans up temporary files on success."""
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir
        mock_ccg_dir.__truediv__ = MagicMock()

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True

        def ccg_dir_side_effect(name):
            if "commit_message" in name:
                return mock_message_file
            elif "msg_filter" in name:
                return mock_script_file
            return MagicMock()

        mock_ccg_dir.__truediv__.side_effect = ccg_dir_side_effect

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

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.invalidate_repository_cache")
    @patch("ccg.git_strategies.Path")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_edit_cleanup_failure_handled_gracefully(
        self, mock_spinner, mock_path, mock_invalidate, mock_run_git
    ):
        """Test edit handles cleanup failure gracefully."""
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir
        mock_ccg_dir.__truediv__ = MagicMock()

        mock_message_file = MagicMock(spec=Path)
        mock_script_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_script_file.exists.return_value = True
        mock_message_file.unlink.side_effect = OSError("Cleanup failed")

        def ccg_dir_side_effect(name):
            if "commit_message" in name:
                return mock_message_file
            elif "msg_filter" in name:
                return mock_script_file
            return MagicMock()

        mock_ccg_dir.__truediv__.side_effect = ccg_dir_side_effect

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

        result = edit_commit_with_strategy("abc123", "def456", "feat: new feature", "Body text")

        assert result is True
        mock_filter.can_handle.assert_called_once_with("abc123", "def456")
        mock_filter.edit.assert_called_once_with("abc123", "feat: new feature", "Body text")

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
