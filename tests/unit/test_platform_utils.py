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
    def test_handles_permission_error(
        self, mock_chmod: Mock, mock_logger: Mock
    ) -> None:
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
        """Should return 'cp' command on Unix systems and no temp file."""
        from ccg.platform_utils import get_copy_command_for_rebase
        import shlex

        script_file = Path("/tmp/rebase_script.txt")
        result, temp_file = get_copy_command_for_rebase(script_file)

        # Path should be quoted for security
        expected = f"cp {shlex.quote(str(script_file))}"
        assert result == expected
        assert temp_file is None  # No temp file on Unix

    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_creates_shell_script_on_windows(self) -> None:
        """Should create .sh script on Windows for Git Bash compatibility."""
        from ccg.platform_utils import get_copy_command_for_rebase
        import shlex

        # Create a mock Path object
        mock_script_file = MagicMock(spec=Path)
        mock_script_file.stem = "rebase_script"
        mock_script_file.__str__ = MagicMock(return_value="C:\\tmp\\rebase_script.txt")
        mock_parent = MagicMock()
        mock_script_file.parent = mock_parent
        mock_shell_file = MagicMock()
        mock_shell_file.__str__ = MagicMock(return_value="C:\\tmp\\rebase_script_copy.sh")
        mock_parent.__truediv__.return_value = mock_shell_file

        result, temp_file = get_copy_command_for_rebase(mock_script_file)

        # Should create shell script
        mock_shell_file.write_text.assert_called_once()
        # Should return sh command with quoted script path
        assert "sh " in result
        assert shlex.quote(str(mock_shell_file)) in result
        # Should also return temp file path for cleanup
        assert temp_file == mock_shell_file

    @patch("ccg.platform_utils.logger")
    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_handles_shell_script_creation_error(self, mock_logger: Mock) -> None:
        """Should handle errors when creating Windows shell script."""
        from ccg.platform_utils import get_copy_command_for_rebase

        # Create a mock Path object that raises error on write
        mock_script_file = MagicMock(spec=Path)
        mock_script_file.stem = "rebase_script"
        mock_script_file.__str__ = MagicMock(return_value="C:\\tmp\\rebase_script.txt")
        mock_parent = MagicMock()
        mock_script_file.parent = mock_parent
        mock_shell_file = MagicMock()
        mock_parent.__truediv__.return_value = mock_shell_file
        mock_shell_file.write_text.side_effect = IOError("Disk full")

        result, temp_file = get_copy_command_for_rebase(mock_script_file)

        # Should log error and return fallback command
        assert mock_logger.error.called
        assert "copy" in result.lower()
        # No temp file since creation failed
        assert temp_file is None


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
        import shlex

        script_file = Path("/tmp/filter_script.py")
        result = get_filter_branch_command(script_file)

        # Both paths should be quoted for security
        expected = f"{shlex.quote(sys.executable)} {shlex.quote(str(script_file))}"
        assert result == expected

    def test_works_with_windows_paths(self) -> None:
        """Should work correctly with Windows-style paths."""
        from ccg.platform_utils import get_filter_branch_command

        script_file = Path("C:\\temp\\filter_script.py")
        result = get_filter_branch_command(script_file)

        # Should use sys.executable regardless of platform
        assert sys.executable in result
        assert str(script_file) in result


class TestCreateSecureTempFile:
    """Tests for create_secure_temp_file function."""

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.os.umask")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_creates_file_with_secure_permissions_unix(
        self, mock_umask: Mock, mock_chmod: Mock
    ) -> None:
        """Should set restrictive umask before creating file on Unix."""
        import tempfile

        from ccg.platform_utils import create_secure_temp_file

        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            filename = "test_secure.tmp"
            content = "sensitive data"

            # Mock umask returns
            mock_umask.return_value = 0o022  # Simulated old umask

            result = create_secure_temp_file(directory, filename, content)

            # Should set restrictive umask before file creation
            assert mock_umask.call_count == 2  # Once to set, once to restore
            mock_umask.assert_any_call(0o077)  # Set restrictive umask
            mock_umask.assert_any_call(0o022)  # Restore old umask

            # Should double-check permissions with chmod
            mock_chmod.assert_called_once_with(result, 0o600)

            # Verify file was created with correct content
            assert result.exists()
            assert result.read_text() == content

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_creates_file_on_windows(self, mock_chmod: Mock) -> None:
        """Should create file with Windows permissions."""
        import tempfile

        from ccg.platform_utils import create_secure_temp_file

        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            filename = "test_secure.tmp"
            content = "sensitive data"

            result = create_secure_temp_file(directory, filename, content)

            # Should set Windows permissions
            mock_chmod.assert_called_once_with(result, stat.S_IWRITE | stat.S_IREAD)

            # Verify file was created with correct content
            assert result.exists()
            assert result.read_text() == content

    @patch("ccg.platform_utils.os.umask")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_handles_file_creation_error_unix(self, mock_umask: Mock) -> None:
        """Should restore umask even when file creation fails on Unix."""
        from ccg.platform_utils import create_secure_temp_file

        directory = Path("/nonexistent")
        filename = "test.tmp"
        content = "data"

        mock_umask.return_value = 0o022

        with pytest.raises(OSError):
            create_secure_temp_file(directory, filename, content)

        # Should restore umask even on error
        assert mock_umask.call_count == 2
        mock_umask.assert_any_call(0o077)  # Set restrictive
        mock_umask.assert_any_call(0o022)  # Restore

    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_handles_file_creation_error_windows(self) -> None:
        """Should raise error when file creation fails on Windows."""
        from ccg.platform_utils import create_secure_temp_file

        directory = Path("/nonexistent")
        filename = "test.tmp"
        content = "data"

        with pytest.raises((OSError, IOError, PermissionError)):
            create_secure_temp_file(directory, filename, content)


class TestCreateExecutableTempFile:
    """Tests for create_executable_temp_file function."""

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.os.umask")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_creates_executable_file_unix(
        self, mock_umask: Mock, mock_chmod: Mock
    ) -> None:
        """Should create file with executable permissions on Unix."""
        import tempfile

        from ccg.platform_utils import create_executable_temp_file

        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            filename = "test_script.py"
            content = "#!/usr/bin/env python3\\nprint('hello')"

            mock_umask.return_value = 0o022

            result = create_executable_temp_file(directory, filename, content)

            # Should set restrictive umask before file creation
            assert mock_umask.call_count == 2
            mock_umask.assert_any_call(0o077)  # Set restrictive umask
            mock_umask.assert_any_call(0o022)  # Restore old umask

            # Should set executable permissions (0o700 = rwx------)
            mock_chmod.assert_called_once_with(result, 0o700)

            # Verify file was created with correct content
            assert result.exists()
            assert result.read_text() == content

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_creates_file_on_windows_no_executable(self, mock_chmod: Mock) -> None:
        """Should create file on Windows without executable bit."""
        import tempfile

        from ccg.platform_utils import create_executable_temp_file

        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)
            filename = "test_script.py"
            content = "print('hello')"

            result = create_executable_temp_file(directory, filename, content)

            # Should set Windows permissions (read/write, no executable needed)
            mock_chmod.assert_called_once_with(result, stat.S_IWRITE | stat.S_IREAD)

            # Verify file was created with correct content
            assert result.exists()
            assert result.read_text() == content

    @patch("ccg.platform_utils.os.umask")
    @patch("ccg.platform_utils.sys.platform", "linux")
    def test_restores_umask_on_error(self, mock_umask: Mock) -> None:
        """Should restore umask even when file creation fails."""
        from ccg.platform_utils import create_executable_temp_file

        directory = Path("/nonexistent")
        filename = "test.py"
        content = "print('test')"

        mock_umask.return_value = 0o022

        with pytest.raises(OSError):
            create_executable_temp_file(directory, filename, content)

        # Should restore umask even on error
        assert mock_umask.call_count == 2
        mock_umask.assert_any_call(0o077)
        mock_umask.assert_any_call(0o022)

    @patch("ccg.platform_utils.os.chmod")
    @patch("ccg.platform_utils.sys.platform", "win32")
    def test_handles_windows_file_creation_error(self, mock_chmod: Mock) -> None:
        """Should raise error when file creation fails on Windows."""
        from ccg.platform_utils import create_executable_temp_file

        directory = Path("/nonexistent_dir")
        filename = "test.py"
        content = "print('test')"

        # File creation will fail due to nonexistent directory
        with pytest.raises((OSError, IOError, PermissionError, FileNotFoundError)):
            create_executable_temp_file(directory, filename, content)
