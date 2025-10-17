"""Cross-platform utilities for file operations and permissions.

This module provides platform-aware functions that work correctly on both
Unix-like systems (Linux, macOS) and Windows. It handles differences in
file permissions, command availability, and path handling.
"""

import logging
import os
import stat
import sys
from pathlib import Path
from typing import Union

logger = logging.getLogger("ccg.platform_utils")


def set_file_permissions_secure(file_path: Union[str, Path]) -> None:
    """Set restrictive permissions on a file in a cross-platform way.

    On Unix/Linux/macOS: Sets 0o600 (owner read/write only, no access for group/others)
    On Windows: Sets read/write for owner only (uses stat.S_IREAD | stat.S_IWRITE)

    This function is best-effort and will not fail the operation if permissions
    cannot be set. It logs warnings on failure but continues execution.

    Args:
        file_path: Path to file to secure (string or Path object)

    Note:
        Windows has limited support for Unix-style permissions. The function uses
        basic stat flags (S_IREAD, S_IWRITE) which provide minimal security but
        ensure cross-platform compatibility.

    Example:
        >>> temp_file = "/tmp/sensitive_data.txt"
        >>> set_file_permissions_secure(temp_file)
        # Unix: -rw------- (0o600)
        # Windows: Read/write for owner
    """
    try:
        if sys.platform == "win32":
            # Windows: Use basic stat flags (limited but works)
            # S_IWRITE allows owner to write, S_IREAD allows owner to read
            # Windows doesn't support group/other permissions like Unix
            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
            logger.debug(f"Set Windows permissions (read/write) on {file_path}")
        else:
            # Unix/Linux/Mac: Use full permission bits
            # 0o600 = rw------- (owner read/write, no group/other access)
            os.chmod(file_path, 0o600)
            logger.debug(f"Set Unix permissions (0o600) on {file_path}")
    except (OSError, PermissionError) as e:
        # Non-critical: log but don't fail the operation
        # File permissions are a security enhancement, not a requirement
        logger.warning(f"Could not set secure permissions on {file_path}: {e}")


def set_file_permissions_executable(file_path: Union[str, Path]) -> None:
    """Set executable permissions on a file in a cross-platform way.

    On Unix/Linux/macOS: Sets 0o755 (owner rwx, group rx, others rx)
    On Windows: No action needed (.py files execute via python interpreter)

    This function is best-effort and will not fail the operation if permissions
    cannot be set. It logs warnings on failure but continues execution.

    Args:
        file_path: Path to file to make executable (string or Path object)

    Note:
        On Windows, executable permissions are not relevant for Python scripts.
        Scripts are executed by calling `python script.py`, not by marking the
        file as executable. The shebang (#!) is also ignored on Windows.

    Example:
        >>> script_file = "/tmp/script.py"
        >>> set_file_permissions_executable(script_file)
        # Unix: -rwxr-xr-x (0o755)
        # Windows: No action (relies on file association)
    """
    try:
        if sys.platform != "win32":
            # Unix/Linux/Mac: Make executable
            # 0o755 = rwxr-xr-x (owner rwx, group rx, others rx)
            os.chmod(file_path, 0o755)
            logger.debug(f"Set Unix executable permissions (0o755) on {file_path}")
        else:
            # Windows: No action needed - .py files execute via python interpreter
            # File associations handle execution (e.g., .py -> python.exe)
            logger.debug(f"Skipped executable permissions on Windows for {file_path}")
    except (OSError, PermissionError) as e:
        # Non-critical: log but don't fail the operation
        logger.warning(f"Could not set executable permissions on {file_path}: {e}")


def get_copy_command_for_rebase(script_file: Path) -> str:
    """Get the appropriate copy command for git rebase on the current platform.

    Git's GIT_SEQUENCE_EDITOR needs a command that copies a file. This function
    returns a platform-appropriate command string.

    Args:
        script_file: Path to the rebase script file to copy

    Returns:
        Command string to use for GIT_SEQUENCE_EDITOR

    Note:
        On Unix: Uses 'cp' command
        On Windows: Creates a temporary batch file that performs the copy

    Example:
        >>> script = Path("/tmp/rebase_script.txt")
        >>> cmd = get_copy_command_for_rebase(script)
        # Unix: "cp /tmp/rebase_script.txt"
        # Windows: path to temporary .bat file
    """
    if sys.platform != "win32":
        # Unix/Linux/Mac: Use standard cp command
        return f"cp {script_file}"
    else:
        # Windows: Create a batch file to perform the copy
        # %1 is the first argument passed by git (destination file)
        batch_content = f'@echo off\ncopy /Y "{script_file}" %1\n'

        # Create batch file in same directory as script
        batch_file = script_file.parent / f"{script_file.stem}_copy.bat"
        try:
            batch_file.write_text(batch_content, encoding="utf-8")
            logger.debug(f"Created Windows batch file for copy: {batch_file}")
            return str(batch_file)
        except (IOError, OSError) as e:
            logger.error(f"Failed to create Windows batch file: {e}")
            # Fallback: try to use copy command directly (may not work in all shells)
            return f'copy /Y "{script_file}"'


def get_null_editor_command() -> str:
    """Get a platform-appropriate command that does nothing and returns success.

    Git's GIT_EDITOR sometimes needs to be set to a no-op command. This function
    returns a command that exits successfully without doing anything.

    Returns:
        Command string that returns exit code 0 without side effects

    Note:
        On Unix: Uses 'true' command (always returns 0)
        On Windows: Uses 'cmd /c exit 0'

    Example:
        >>> null_cmd = get_null_editor_command()
        # Unix: "true"
        # Windows: "cmd /c exit 0"
    """
    if sys.platform != "win32":
        # Unix/Linux/Mac: 'true' always exits with status 0
        return "true"
    else:
        # Windows: Use cmd to exit with code 0
        # /c means execute command and then terminate
        return "cmd /c exit 0"


def get_filter_branch_command(script_file: Path) -> str:
    """Get the appropriate msg-filter command for git filter-branch.

    Git filter-branch needs to invoke the Python script. To ensure reliability
    across all platforms and shell environments, we explicitly invoke Python.

    Args:
        script_file: Path to the filter script (.py file)

    Returns:
        Command string to use for --msg-filter argument

    Note:
        Uses sys.executable to invoke the same Python interpreter that's
        currently running, ensuring compatibility across different environments.

    Example:
        >>> script = Path("/tmp/filter.py")
        >>> cmd = get_filter_branch_command(script)
        # Returns: "/path/to/python /tmp/filter.py"
    """
    # Use sys.executable to invoke the same Python interpreter
    # This is more reliable than relying on shebangs, especially in
    # complex environments like tox, virtualenvs, or conda
    return f"{sys.executable} {script_file}"
