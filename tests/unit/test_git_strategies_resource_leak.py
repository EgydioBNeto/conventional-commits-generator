"""Integration tests for resource cleanup in git_strategies.py

These tests validate that temporary files are properly cleaned up even
when errors occur during file operations.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccg.git_strategies import AmendStrategy, FilterBranchStrategy


class TestAmendStrategyResourceCleanup:
    """Test that AmendStrategy properly cleans up temporary files."""

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.Path")
    def test_cleanup_when_create_secure_file_fails(
        self, mock_path_cls, mock_create_secure, mock_run_git
    ):
        """Test no files leaked when create_secure_temp_file fails.

        With the new secure file creation approach, if create_secure_temp_file
        fails, no file should be created (since permissions are set atomically).
        """
        # Mock Path.home() / ".ccg"
        mock_home = MagicMock()
        mock_ccg_dir = MagicMock()
        mock_path_cls.home.return_value = mock_home
        mock_home.__truediv__.return_value = mock_ccg_dir

        # Make create_secure_temp_file fail
        mock_create_secure.side_effect = PermissionError("Cannot create secure file")

        strategy = AmendStrategy()
        result = strategy.edit("abc123", "feat: new message", "Body")

        # Should fail due to permission error
        assert result is False

        # Check that no files leaked in ~/.ccg
        ccg_dir = Path.home() / ".ccg"
        if ccg_dir.exists():
            leaked_files = list(ccg_dir.glob("*abc123*"))
            assert len(leaked_files) == 0, f"Found leaked files: {leaked_files}"

    @patch("ccg.git.run_git_command")
    def test_cleanup_when_git_command_fails(self, mock_run_git):
        """Test temp file is deleted when git command fails."""
        # Git command fails
        mock_run_git.return_value = (False, "Git error")

        # Track temp files
        created_files = []
        original_tempfile = tempfile.NamedTemporaryFile

        def track_tempfile(*args, **kwargs):
            f = original_tempfile(*args, **kwargs)
            created_files.append(f.name)
            return f

        strategy = AmendStrategy()

        with patch("tempfile.NamedTemporaryFile", side_effect=track_tempfile):
            result = strategy.edit("abc123", "feat: new message")

        # Should fail
        assert result is False

        # Temp file should be cleaned up
        for file_path in created_files:
            assert not os.path.exists(
                file_path
            ), f"Temp file leaked after git failure: {file_path}"

    @patch("ccg.git.run_git_command")
    def test_cleanup_on_success(self, mock_run_git):
        """Test temp file is deleted on successful operation."""
        # Git command succeeds
        mock_run_git.return_value = (True, None)

        # Track temp files
        created_files = []
        original_tempfile = tempfile.NamedTemporaryFile

        def track_tempfile(*args, **kwargs):
            f = original_tempfile(*args, **kwargs)
            created_files.append(f.name)
            return f

        strategy = AmendStrategy()

        with patch("tempfile.NamedTemporaryFile", side_effect=track_tempfile):
            result = strategy.edit("abc123", "feat: new message")

        # Should succeed
        assert result is True

        # Temp file should be cleaned up
        for file_path in created_files:
            assert not os.path.exists(
                file_path
            ), f"Temp file leaked after success: {file_path}"


class TestFilterBranchStrategyResourceCleanup:
    """Test that FilterBranchStrategy properly cleans up temporary files."""

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.ProgressSpinner")
    @patch("ccg.git_strategies.create_secure_temp_file")
    def test_cleanup_when_create_secure_fails_on_message_file(
        self, mock_create_secure, mock_spinner, mock_run_git
    ):
        """Test no files leaked when create_secure_temp_file fails."""
        # Setup spinner mock
        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        # Make create_secure_temp_file fail (message file creation)
        mock_create_secure.side_effect = PermissionError("Cannot create secure file")

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc1234", "feat: new message")

        # Should fail
        assert result is False

        # Check that no files leaked in ~/.ccg
        ccg_dir = Path.home() / ".ccg"
        if ccg_dir.exists():
            leaked_files = list(ccg_dir.glob("*abc1234*"))
            assert len(leaked_files) == 0, f"Found leaked files: {leaked_files}"

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.ProgressSpinner")
    @patch("ccg.git_strategies.create_secure_temp_file")
    @patch("ccg.git_strategies.create_executable_temp_file")
    def test_cleanup_when_create_executable_fails_on_script_file(
        self, mock_create_exec, mock_create_secure, mock_spinner, mock_run_git
    ):
        """Test files are deleted when create_executable_temp_file fails."""
        # Setup spinner mock
        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        # Message file succeeds, but executable file fails
        mock_message_file = MagicMock(spec=Path)
        mock_message_file.exists.return_value = True
        mock_create_secure.return_value = mock_message_file
        mock_create_exec.side_effect = PermissionError("Cannot create executable")

        strategy = FilterBranchStrategy()
        result = strategy.edit("abc5678", "feat: new message")

        # Should fail
        assert result is False

        # Message file should be cleaned up in finally block
        mock_message_file.unlink.assert_called_once()

        # Check that no files leaked in ~/.ccg
        ccg_dir = Path.home() / ".ccg"
        if ccg_dir.exists():
            leaked_files = list(ccg_dir.glob("*abc5678*"))
            assert len(leaked_files) == 0, f"Found leaked files: {leaked_files}"

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_cleanup_when_git_command_fails(self, mock_spinner, mock_run_git):
        """Test files are deleted when git command fails."""
        # Setup spinner mock
        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        # Git command fails
        mock_run_git.return_value = (False, "Git error")

        strategy = FilterBranchStrategy()
        result = strategy.edit("def9876", "feat: new message")

        # Should fail
        assert result is False

        # Check that no files leaked in ~/.ccg
        ccg_dir = Path.home() / ".ccg"
        if ccg_dir.exists():
            leaked_files = list(ccg_dir.glob("*def9876*"))
            assert len(leaked_files) == 0, f"Found leaked files: {leaked_files}"

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_cleanup_on_success(self, mock_spinner, mock_run_git):
        """Test files are deleted on successful operation."""
        # Setup spinner mock
        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        # Git command succeeds
        mock_run_git.return_value = (True, "Success")

        strategy = FilterBranchStrategy()
        result = strategy.edit("ghi5432", "feat: new message")

        # Should succeed
        assert result is True

        # Check that no files leaked in ~/.ccg
        ccg_dir = Path.home() / ".ccg"
        if ccg_dir.exists():
            leaked_files = list(ccg_dir.glob("*ghi5432*"))
            assert len(leaked_files) == 0, f"Found leaked files: {leaked_files}"


class TestResourceLeakScenarios:
    """Test various edge cases that could cause resource leaks."""

    @patch("ccg.git.run_git_command")
    def test_amend_multiple_failures_no_leak(self, mock_run_git):
        """Test multiple failed operations don't accumulate temp files."""
        mock_run_git.return_value = (False, "Error")

        strategy = AmendStrategy()

        # Try 5 times
        for i in range(5):
            result = strategy.edit(f"commit{i}", f"Message {i}")
            assert result is False

        # Check that no files leaked in ~/.ccg
        ccg_dir = Path.home() / ".ccg"
        if ccg_dir.exists():
            # Check for any remaining commit message files
            leaked_files = list(ccg_dir.glob("commit_message_amend_commit*.tmp"))
            assert len(leaked_files) == 0, f"Temp files leaked: {leaked_files}"

    @patch("ccg.git.run_git_command")
    @patch("ccg.git_strategies.ProgressSpinner")
    def test_filter_branch_multiple_failures_no_leak(self, mock_spinner, mock_run_git):
        """Test multiple failed filter-branch operations don't leak files."""
        # Setup spinner mock
        mock_spinner_instance = MagicMock()
        mock_spinner_instance.__enter__ = MagicMock(return_value=mock_spinner_instance)
        mock_spinner_instance.__exit__ = MagicMock(return_value=None)
        mock_spinner.return_value = mock_spinner_instance

        # Git fails
        mock_run_git.return_value = (False, "Error")

        strategy = FilterBranchStrategy()

        # Try 3 times with different hashes
        hashes = ["aaa1111", "bbb2222", "ccc3333"]
        for commit_hash in hashes:
            result = strategy.edit(commit_hash, f"Message for {commit_hash}")
            assert result is False

        # Check no leaked files
        ccg_dir = Path.home() / ".ccg"
        if ccg_dir.exists():
            for commit_hash in hashes:
                leaked_files = list(ccg_dir.glob(f"*{commit_hash}*"))
                assert (
                    len(leaked_files) == 0
                ), f"Found leaked files for {commit_hash}: {leaked_files}"
