"""Security tests for platform_utils.py

These tests validate that platform utilities properly prevent command injection
vulnerabilities by escaping special shell characters in file paths.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from ccg.platform_utils import (
    ensure_ccg_directory,
    get_copy_command_for_rebase,
    get_filter_branch_command,
)


class TestCommandInjectionPrevention:
    """Test that platform utilities prevent command injection attacks."""

    @pytest.mark.parametrize(
        "malicious_path,description",
        [
            ("/tmp/file; rm -rf /", "Semicolon injection"),
            ("/tmp/file && echo pwned", "AND operator injection"),
            ("/tmp/file || echo pwned", "OR operator injection"),
            ("/tmp/file | cat /etc/passwd", "Pipe injection"),
            ("/tmp/file`whoami`", "Backtick injection"),
            ("/tmp/file$(whoami)", "Command substitution"),
            ("/tmp/file\nrm -rf /", "Newline injection"),
            ("/tmp/file;echo attack", "Semicolon without space"),
            ("/tmp/file&echo attack", "Ampersand without space"),
            ("/tmp/file>evil.txt", "Redirection operator"),
            ("/tmp/file<evil.txt", "Input redirection"),
            ("/tmp/file*", "Glob pattern"),
            ("/tmp/file?", "Glob single char"),
            ("/tmp/file[0-9]", "Glob range"),
            ("/tmp/file\techo attack", "Tab injection"),
            ("/tmp/file$PATH", "Variable expansion"),
            ("/tmp/file~", "Tilde expansion"),
        ],
    )
    def test_copy_command_prevents_injection(self, malicious_path, description):
        """Test that malicious paths are properly escaped in copy command.

        This validates that get_copy_command_for_rebase() properly escapes
        special shell characters to prevent command injection.

        The key insight: shlex.quote() wraps the ENTIRE path in single quotes,
        which prevents the shell from interpreting ANY special characters inside.
        E.g., "/tmp/file; rm -rf /" becomes "'/tmp/file; rm -rf /'"
        """
        path = Path(malicious_path)

        # Test Unix behavior (where the vulnerability was)
        with patch("sys.platform", "linux"):
            command, temp_file = get_copy_command_for_rebase(path)

            # Command should use shlex.quote() which wraps in single quotes
            # The entire malicious path should be inside quotes
            assert (
                "'" in command
            ), f"{description} not prevented (no quotes found): {command}"

            # Verify the malicious path is wrapped in quotes
            # Extract the part after "cp "
            if command.startswith("cp "):
                quoted_part = command[3:]  # Remove "cp "
                # The quoted part should start with a quote
                assert quoted_part.startswith("'") or quoted_part.startswith(
                    '"'
                ), f"{description} - path not quoted: {command}"

            # Unix should not create temp files
            assert temp_file is None

    @pytest.mark.parametrize(
        "malicious_path,description",
        [
            ("/tmp/file; rm -rf /", "Semicolon injection"),
            ("/tmp/file && echo pwned", "AND operator injection"),
            ("/tmp/file | cat /etc/passwd", "Pipe injection"),
            ("/tmp/file`whoami`", "Backtick injection"),
            ("/tmp/file$(whoami)", "Command substitution"),
        ],
    )
    def test_filter_branch_command_prevents_injection(
        self, malicious_path, description
    ):
        """Test that malicious paths are properly escaped in filter-branch command.

        This validates that get_filter_branch_command() properly escapes
        both the Python interpreter path and script path.

        shlex.quote() wraps paths in single quotes, neutralizing all special characters.
        """
        script_path = Path(malicious_path)

        command = get_filter_branch_command(script_path)

        # The command should contain quotes to protect against injection
        assert (
            "'" in command
        ), f"{description} not prevented (no quotes found): {command}"

        # The script path should be quoted
        # Check if the malicious part appears within quotes in the command
        # Use str(script_path) because Path() normalizes separators (/ -> \ on Windows)
        normalized_path = str(script_path).rstrip("/").rstrip("\\")
        in_single_quotes = (
            f"'{normalized_path}" in command
            and "'" in command[command.index(normalized_path) :]
        )
        in_double_quotes = f'"{normalized_path}"' in command
        assert (
            in_single_quotes or in_double_quotes
        ), f"{description} not prevented - path not quoted: {command}"

    def test_copy_command_with_spaces(self):
        """Test that paths with spaces are properly quoted."""
        path = Path("/tmp/file with spaces.txt")

        with patch("sys.platform", "linux"):
            command, temp_file = get_copy_command_for_rebase(path)

            # Should contain quotes around the path
            assert (
                "'" in command or '"' in command or "\\ " in command
            ), f"Spaces not properly handled: {command}"

            # Unix should not create temp files
            assert temp_file is None

    def test_filter_branch_command_with_spaces(self):
        """Test that filter-branch command handles spaces correctly."""
        script = Path("/tmp/my script.py")

        command = get_filter_branch_command(script)

        # The script path should be quoted to handle spaces
        assert (
            "'" in command or '"' in command or "\\ " in command
        ), f"Spaces not properly handled: {command}"

    def test_copy_command_normal_path(self):
        """Test that normal paths work correctly."""
        path = Path("/tmp/normal_file.txt")

        with patch("sys.platform", "linux"):
            command, temp_file = get_copy_command_for_rebase(path)

            # Should contain 'cp' and the path
            assert "cp" in command
            assert "normal_file.txt" in command

            # Unix should not create temp files
            assert temp_file is None

    def test_filter_branch_command_normal_path(self):
        """Test that filter-branch command works with normal paths."""
        script = Path("/tmp/filter.py")

        command = get_filter_branch_command(script)

        # Should contain python executable and script path
        assert "python" in command or sys.executable in command
        assert "filter.py" in command

    @patch("sys.platform", "win32")
    def test_copy_command_windows_quote_sanitization(self):
        """Test that Windows command properly quotes paths in shell scripts.

        On Windows, Git Bash is used, so we create .sh shell scripts instead
        of batch files. Paths should be properly quoted using shlex.quote().
        """
        import os
        import tempfile

        # Create a temporary directory to test
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a path with a safe name (no actual quotes in filesystem)
            script_file = Path(tmpdir) / "test_script.txt"
            script_file.write_text("test")

            # Simulate a malicious path with quotes (in the Path object, not filesystem)
            # This tests the sanitization logic
            malicious_path_str = str(script_file).replace(
                "test_script", 'file"with"quotes'
            )
            malicious_path = Path(malicious_path_str)

            command, temp_file = get_copy_command_for_rebase(malicious_path)

            # On Windows, should create a .sh file or use cp command
            assert (
                ".sh" in command or "cp" in command
            ), f"Windows should create .sh or use cp: {command}"

            # The actual shell script should be created - let's verify it uses proper quoting
            if ".sh" in command:
                # Verify the shell script was created
                shell_file_path = Path(command.replace("sh ", "").strip("'\""))
                if shell_file_path.exists():
                    shell_content = shell_file_path.read_text()
                    # Should use cp command and have proper quoting
                    assert "cp" in shell_content, f"Shell script should use cp: {shell_content}"
                    assert "#!/bin/sh" in shell_content, f"Missing shebang: {shell_content}"
                    # Cleanup
                    try:
                        shell_file_path.unlink()
                    except:
                        pass

                # Windows should return the temp file path for cleanup
                assert temp_file is not None

    def test_very_long_malicious_path(self):
        """Test that very long malicious paths are handled."""
        # Create a path with multiple injection attempts
        malicious_path = "/tmp/file;rm -rf /&&echo pwned|cat /etc/passwd`whoami`$(ls)"

        path = Path(malicious_path)

        with patch("sys.platform", "linux"):
            command, temp_file = get_copy_command_for_rebase(path)

            # All dangerous characters should be neutralized
            # shlex.quote() should wrap the entire thing in single quotes
            assert (
                "'" in command
            ), f"Long malicious path not properly escaped: {command}"

            # Unix should not create temp files
            assert temp_file is None

    def test_unicode_in_paths(self):
        """Test that Unicode characters in paths are handled correctly."""
        path = Path("/tmp/файл.txt")  # Russian: file.txt

        with patch("sys.platform", "linux"):
            command, temp_file = get_copy_command_for_rebase(path)

            # Should handle Unicode without errors
            assert "cp" in command
            assert "файл" in command or "'" in command

            # Unix should not create temp files
            assert temp_file is None

    def test_empty_path_component(self):
        """Test handling of unusual path structures."""
        path = Path("/tmp//double//slash.txt")

        with patch("sys.platform", "linux"):
            command, temp_file = get_copy_command_for_rebase(path)

            # Should handle without errors
            assert "cp" in command

            # Unix should not create temp files
            assert temp_file is None


class TestRealWorldScenarios:
    """Test real-world scenarios that could occur in production."""

    def test_git_rebase_realistic_path(self):
        """Test with realistic git rebase script path."""
        # Git typically creates files in .git/rebase-merge/
        path = Path("/home/user/repo/.git/rebase-merge/git-rebase-todo")

        with patch("sys.platform", "linux"):
            command, temp_file = get_copy_command_for_rebase(path)

            # Should work correctly with normal git paths
            assert "cp" in command
            assert "git-rebase-todo" in command

            # Unix should not create temp files
            assert temp_file is None

    def test_filter_branch_in_temp_directory(self):
        """Test filter-branch with temp directory paths."""
        script = Path("/tmp/ccg_filter_abc123.py")

        command = get_filter_branch_command(script)

        # Should work correctly
        assert "python" in command or sys.executable in command
        assert "ccg_filter" in command

    def test_path_with_git_special_characters(self):
        """Test paths that git might interpret specially."""
        # Git uses ^ for parent commit references, @ for HEAD shortcuts
        path = Path("/tmp/commit^parent@HEAD.txt")

        with patch("sys.platform", "linux"):
            command, temp_file = get_copy_command_for_rebase(path)

            # These characters should be properly escaped
            assert "'" in command or "\\" in command

            # Unix should not create temp files
            assert temp_file is None

    @patch("sys.platform", "win32")
    def test_windows_shell_script_creation(self):
        """Test that Windows creates shell scripts correctly for Git Bash."""
        import os

        path = Path("C:\\Users\\test\\script.txt")

        command, temp_file = get_copy_command_for_rebase(path)

        try:
            # On Windows, should return a path to a .sh file or use cp command
            assert ".sh" in command or "cp" in command

            # Windows should return temp file path for cleanup (if .sh was created)
            if ".sh" in command:
                assert temp_file is not None
        finally:
            # Cleanup: delete the .sh file if it was created
            if temp_file:
                try:
                    shell_file_path = str(temp_file)
                    if os.path.exists(shell_file_path):
                        os.unlink(shell_file_path)
                except Exception:
                    pass  # Ignore cleanup errors

    def test_python_executable_with_spaces(self):
        """Test when Python executable path contains spaces."""
        script = Path("/tmp/filter.py")

        # Simulate Python in "Program Files" on Windows
        with patch("sys.executable", "C:\\Program Files\\Python\\python.exe"):
            command = get_filter_branch_command(script)

            # Python path should be quoted
            assert "'" in command or '"' in command or "\\" in command


class TestEnsureCCGDirectory:
    """Test ensure_ccg_directory function."""

    @patch("ccg.platform_utils.Path.home")
    def test_creates_directory_successfully(self, mock_home):
        """Test that directory is created successfully."""
        from pathlib import Path as RealPath
        from unittest.mock import MagicMock

        mock_home_path = MagicMock()
        mock_ccg_dir = MagicMock(spec=RealPath)
        mock_home.return_value = mock_home_path
        mock_home_path.__truediv__.return_value = mock_ccg_dir

        result = ensure_ccg_directory()

        mock_ccg_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert result == mock_ccg_dir

    @patch("ccg.platform_utils.Path.home")
    def test_returns_none_on_oserror(self, mock_home):
        """Test that None is returned when OSError occurs."""
        from pathlib import Path as RealPath
        from unittest.mock import MagicMock

        mock_home_path = MagicMock()
        mock_ccg_dir = MagicMock(spec=RealPath)
        mock_home.return_value = mock_home_path
        mock_home_path.__truediv__.return_value = mock_ccg_dir
        mock_ccg_dir.mkdir.side_effect = OSError("Permission denied")

        result = ensure_ccg_directory()

        assert result is None

    @patch("ccg.platform_utils.Path.home")
    def test_returns_none_on_permission_error(self, mock_home):
        """Test that None is returned when PermissionError occurs."""
        from pathlib import Path as RealPath
        from unittest.mock import MagicMock

        mock_home_path = MagicMock()
        mock_ccg_dir = MagicMock(spec=RealPath)
        mock_home.return_value = mock_home_path
        mock_home_path.__truediv__.return_value = mock_ccg_dir
        mock_ccg_dir.mkdir.side_effect = PermissionError("Access denied")

        result = ensure_ccg_directory()

        assert result is None
