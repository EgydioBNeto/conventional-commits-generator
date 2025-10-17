"""Tests for platform_utils module - cross-platform file operations."""

import os
import stat
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestSetFilePermissionsSecure:
    """Tests for set_file_permissions_secure function."""

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_sets_unix_permissions(self, mock_chmod: Mock) -> None:
        """Should set 0o600 permissions on Unix systems."""
        from ccg.platform_utils import set_file_permissions_secure

        test_path = "/tmp/test_file.txt"
        set_file_permissions_secure(test_path)

        mock_chmod.assert_called_once_with(test_path, 0o600)

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_sets_windows_permissions(self, mock_chmod: Mock) -> None:
        """Should set S_IWRITE | S_IREAD permissions on Windows."""
        from ccg.platform_utils import set_file_permissions_secure

        test_path = "C:\\temp\\test_file.txt"
        set_file_permissions_secure(test_path)

        mock_chmod.assert_called_once_with(test_path, stat.S_IWRITE | stat.S_IREAD)

    @patch("ccg.platform_utils.logger")
    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_handles_permission_error(self, mock_chmod: Mock, mock_logger: Mock) -> None:
        """Should log warning on permission error but not raise."""
        from ccg.platform_utils import set_file_permissions_secure

        test_path = "/tmp/test_file.txt"
        mock_chmod.side_effect = PermissionError("Access denied")

        # Should not raise exception
        set_file_permissions_secure(test_path)

        # Should log warning
        assert mock_logger.warning.called

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_accepts_path_object(self, mock_chmod: Mock) -> None:
        """Should accept Path object in addition to string."""
        from ccg.platform_utils import set_file_permissions_secure

        test_path = Path("/tmp/test_file.txt")
        set_file_permissions_secure(test_path)

        mock_chmod.assert_called_once_with(test_path, 0o600)


class TestSetFilePermissionsExecutable:
    """Tests for set_file_permissions_executable function."""

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_sets_unix_executable_permissions(self, mock_chmod: Mock) -> None:
        """Should set 0o755 permissions on Unix systems."""
        from ccg.platform_utils import set_file_permissions_executable

        test_path = "/tmp/test_script.py"
        set_file_permissions_executable(test_path)

        mock_chmod.assert_called_once_with(test_path, 0o755)

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_skips_windows_executable_permissions(self, mock_chmod: Mock) -> None:
        """Should skip chmod on Windows (no-op)."""
        from ccg.platform_utils import set_file_permissions_executable

        test_path = "C:\\temp\\test_script.py"
        set_file_permissions_executable(test_path)

        # Should not call chmod on Windows
        mock_chmod.assert_not_called()

    @patch("ccg.platform_utils.logger")
    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_handles_os_error(self, mock_chmod: Mock, mock_logger: Mock) -> None:
        """Should log warning on OS error but not raise."""
        from ccg.platform_utils import set_file_permissions_executable

        test_path = "/tmp/test_script.py"
        mock_chmod.side_effect = OSError("File system error")

        # Should not raise exception
        set_file_permissions_executable(test_path)

        # Should log warning
        assert mock_logger.warning.called


class TestGetCopyCommandForRebase:
    """Tests for get_copy_command_for_rebase function."""

    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_returns_cp_command_on_unix(self) -> None:
        """Should return 'cp' command on Unix systems."""
        from ccg.platform_utils import get_copy_command_for_rebase

        script_file = Path("/tmp/rebase_script.txt")
        result = get_copy_command_for_rebase(script_file)

        assert result == f"cp {script_file}"

    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_creates_batch_file_on_windows(self) -> None:
        """Should create .bat file on Windows and return its path."""
        from ccg.platform_utils import get_copy_command_for_rebase

        # Create a mock Path object
        mock_script_file = MagicMock(spec=Path)
        mock_script_file.stem = "rebase_script"
        mock_parent = MagicMock()
        mock_script_file.parent = mock_parent
        mock_batch_file = MagicMock()
        mock_parent.__truediv__.return_value = mock_batch_file

        result = get_copy_command_for_rebase(mock_script_file)

        # Should create batch file
        mock_batch_file.write_text.assert_called_once()
        # Should return path to batch file
        assert result == str(mock_batch_file)

    @patch("ccg.platform_utils.logger")
    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_handles_batch_file_creation_error(self, mock_logger: Mock) -> None:
        """Should handle errors when creating Windows batch file."""
        from ccg.platform_utils import get_copy_command_for_rebase

        # Create a mock Path object that raises error on write
        mock_script_file = MagicMock(spec=Path)
        mock_script_file.stem = "rebase_script"
        mock_parent = MagicMock()
        mock_script_file.parent = mock_parent
        mock_batch_file = MagicMock()
        mock_parent.__truediv__.return_value = mock_batch_file
        mock_batch_file.write_text.side_effect = IOError("Disk full")

        result = get_copy_command_for_rebase(mock_script_file)

        # Should log error and return fallback command
        assert mock_logger.error.called
        assert "copy" in result.lower()


class TestGetNullEditorCommand:
    """Tests for get_null_editor_command function."""

    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_returns_true_on_unix(self) -> None:
        """Should return 'true' command on Unix systems."""
        from ccg.platform_utils import get_null_editor_command

        result = get_null_editor_command()

        assert result == "true"

    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_returns_cmd_exit_on_windows(self) -> None:
        """Should return 'cmd /c exit 0' on Windows."""
        from ccg.platform_utils import get_null_editor_command

        result = get_null_editor_command()

        assert result == "cmd /c exit 0"


class TestGetFilterBranchCommand:
    """Tests for get_filter_branch_command function."""

    def test_returns_python_executable_with_script_path(self) -> None:
        """Should return sys.executable with script path for cross-platform reliability."""
        from ccg.platform_utils import get_filter_branch_command

        script_file = Path("/tmp/filter_script.py")
        result = get_filter_branch_command(script_file)

        # Should use sys.executable to invoke Python
        assert sys.executable in result
        assert str(script_file) in result
        assert result == f"{sys.executable} {script_file}"

    def test_works_with_windows_paths(self) -> None:
        """Should work correctly with Windows-style paths."""
        from ccg.platform_utils import get_filter_branch_command

        script_file = Path("C:\\temp\\filter_script.py")
        result = get_filter_branch_command(script_file)

        # Should use sys.executable regardless of platform
        assert sys.executable in result
        assert str(script_file) in result
