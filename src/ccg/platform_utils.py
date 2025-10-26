"""Cross-platform utilities for file operations and permissions.

This module provides platform-aware functions that work correctly on both
Unix-like systems (Linux, macOS) and Windows. It handles differences in
file permissions, command availability, and path handling.
"""

import logging
import os
import shlex
import stat
import sys
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger("ccg.platform_utils")


def ensure_ccg_directory() -> Optional[Path]:
    """Ensure the CCG temporary directory exists in the user's home directory.

    Creates ~/.ccg directory with appropriate permissions if it doesn't exist.
    This directory is used for temporary files during git operations (commit
    messages, rebase scripts, filter-branch scripts).

    Returns:
        Path to the CCG directory (~/.ccg) if successful, None on error

    Note:
        - Creates directory with default permissions (usually 0o755)
        - Returns existing directory if already present
        - Logs errors but doesn't raise exceptions

    Example:
        >>> ccg_dir = ensure_ccg_directory()
        >>> if ccg_dir:
        ...     temp_file = ccg_dir / "commit_message.tmp"
    """
    ccg_dir = Path.home() / ".ccg"
    try:
        ccg_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"CCG directory ready: {ccg_dir}")
        return ccg_dir
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to create CCG directory: {str(e)}")
        return None


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
            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
            logger.debug(f"Set Windows permissions (read/write) on {file_path}")
        else:
            os.chmod(file_path, 0o600)
            logger.debug(f"Set Unix permissions (0o600) on {file_path}")
    except (OSError, PermissionError) as e:
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
            os.chmod(file_path, 0o755)  # nosec B103
            logger.debug(f"Set Unix executable permissions (0o755) on {file_path}")
        else:
            logger.debug(f"Skipped executable permissions on Windows for {file_path}")
    except (OSError, PermissionError) as e:
        logger.warning(f"Could not set executable permissions on {file_path}: {e}")


def get_copy_command_for_rebase(script_file: Path) -> tuple[str, Optional[Path]]:
    """Get the appropriate copy command for git rebase on the current platform.

    Git's GIT_SEQUENCE_EDITOR needs a command that copies a file. This function
    returns a platform-appropriate command string and optionally a path to a
    temporary file that should be cleaned up after use.

    Args:
        script_file: Path to the rebase script file to copy

    Returns:
        Tuple of (command_string, temp_file_path):
        - command_string: Command to use for GIT_SEQUENCE_EDITOR
        - temp_file_path: Path to temporary .bat file (Windows only), or None (Unix)

    Security:
        Uses shlex.quote() on Unix to prevent command injection from malicious paths.
        On Windows, sanitizes paths by removing double quotes to prevent string escape.

    Note:
        On Unix: Uses 'cp' command with properly quoted path, no temp file created
        On Windows: Creates a temporary batch file that performs the copy
        IMPORTANT: Caller must delete the temp file (if not None) after use!

    Example:
        >>> script = Path("/tmp/rebase_script.txt")
        >>> cmd, temp_file = get_copy_command_for_rebase(script)
        # Unix: ("cp '/tmp/rebase_script.txt'", None)
        # Windows: ("C:\\path\\to\\file_copy.bat", Path("C:\\path\\to\\file_copy.bat"))
    """
    if sys.platform != "win32":
        escaped_path = shlex.quote(str(script_file))
        return f"cp {escaped_path}", None
    else:
        safe_path = str(script_file).replace('"', "")
        batch_content = f'@echo off\ncopy /Y "{safe_path}" %1\n'

        batch_file = script_file.parent / f"{script_file.stem}_copy.bat"
        try:
            batch_file.write_text(batch_content, encoding="utf-8")
            logger.debug(f"Created Windows batch file for copy: {batch_file}")
            return str(batch_file), batch_file
        except (IOError, OSError) as e:
            logger.error(f"Failed to create Windows batch file: {e}")
            return f'copy /Y "{safe_path}"', None


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
        return "true"
    else:
        return "cmd /c exit 0"


def create_secure_temp_file(
    directory: Path,
    filename: str,
    content: str,
) -> Path:
    """Create a temporary file with secure permissions from the start.

    This function prevents information disclosure by setting restrictive permissions
    BEFORE creating the file, eliminating the security window that exists when
    creating a file and then adjusting permissions afterward.

    Args:
        directory: Directory to create file in
        filename: Name of the file to create
        content: Content to write to the file

    Returns:
        Path to the created file with secure permissions

    Security:
        On Unix/Linux/macOS: Sets umask 0o077 before creation, resulting in 0o600
        permissions (owner read/write only, no access for group/others).
        On Windows: Permissions are set after creation using stat flags (best effort).

    Note:
        The umask approach is the most secure way to create files on Unix systems,
        as it ensures the file never exists with insecure permissions, even
        momentarily. Windows has limited support for Unix-style permissions.

    Example:
        >>> temp_file = create_secure_temp_file(
        ...     Path("/tmp"),
        ...     "commit_message.tmp",
        ...     "feat: add secure file creation"
        ... )
        # Unix: File created with -rw------- (0o600)
        # Windows: File created with owner read/write
    """
    file_path: Path = directory / filename

    if sys.platform == "win32":
        # Windows: Create file normally, then set permissions
        # Windows doesn't support umask in a meaningful way
        try:
            file_path.write_text(content, encoding="utf-8")
            # Set Windows permissions (best effort)
            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
            logger.debug(f"Created secure file with Windows permissions: {file_path}")
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Failed to create secure file: {e}")
            raise
    else:
        original_umask: int = os.umask(0o077)

        try:
            file_path.write_text(content, encoding="utf-8")
            os.chmod(file_path, 0o600)
            logger.debug(
                f"Created secure file with Unix permissions (0o600): {file_path}"
            )
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Failed to create secure file: {e}")
            raise
        finally:
            os.umask(original_umask)

    return file_path


def create_executable_temp_file(
    directory: Path,
    filename: str,
    content: str,
) -> Path:
    """Create a temporary executable file with secure permissions from the start.

    This function prevents information disclosure by setting restrictive permissions
    BEFORE creating the file. The file is created with owner-only execute permissions.

    Args:
        directory: Directory to create file in
        filename: Name of the file to create
        content: Content to write to the file (typically a script)

    Returns:
        Path to the created executable file

    Security:
        On Unix/Linux/macOS: Sets umask 0o077 before creation, then adds execute
        bit, resulting in 0o700 permissions (owner rwx only).
        On Windows: No special handling needed (scripts execute via python.exe).

    Note:
        On Windows, executable permissions are not relevant for Python scripts.
        Scripts are executed by calling `python script.py`, not by marking the
        file as executable.

    Example:
        >>> script = create_executable_temp_file(
        ...     Path("/tmp"),
        ...     "filter.py",
        ...     "#!/usr/bin/env python3\\nprint('hello')"
        ... )
        # Unix: File created with -rwx------ (0o700)
        # Windows: File created with owner read/write
    """
    file_path: Path = directory / filename

    if sys.platform == "win32":
        # Windows: Create file normally (no executable bit needed)
        try:
            file_path.write_text(content, encoding="utf-8")
            # Set Windows permissions (best effort)
            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
            logger.debug(
                f"Created executable file with Windows permissions: {file_path}"
            )
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Failed to create executable file: {e}")
            raise
    else:
        # Unix/Linux/macOS: Set restrictive umask BEFORE creating file
        original_umask: int = os.umask(0o077)  # Only owner can read/write

        try:
            # File is created with secure permissions from the start
            file_path.write_text(content, encoding="utf-8")

            # Add execute permission for owner (0o700 = rwx------)
            os.chmod(file_path, 0o700)
            logger.debug(
                f"Created executable file with Unix permissions (0o700): {file_path}"
            )
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Failed to create executable file: {e}")
            raise
        finally:
            # Always restore original umask
            os.umask(original_umask)

    return file_path


def get_filter_branch_command(script_file: Path) -> str:
    """Get the appropriate msg-filter command for git filter-branch.

    Git filter-branch needs to invoke the Python script. To ensure reliability
    across all platforms and shell environments, we explicitly invoke Python.

    Args:
        script_file: Path to the filter script (.py file)

    Returns:
        Command string to use for --msg-filter argument

    Security:
        Uses shlex.quote() to properly escape both the Python interpreter path
        and script path, preventing command injection vulnerabilities.

    Note:
        Uses sys.executable to invoke the same Python interpreter that's
        currently running, ensuring compatibility across different environments.

    Example:
        >>> script = Path("/tmp/filter.py")
        >>> cmd = get_filter_branch_command(script)
        # Returns: "'/path/to/python' '/tmp/filter.py'"
    """
    # Use sys.executable to invoke the same Python interpreter
    # This is more reliable than relying on shebangs, especially in
    # complex environments like tox, virtualenvs, or conda
    # Use shlex.quote() to prevent command injection from malicious paths
    escaped_python = shlex.quote(sys.executable)
    escaped_script = shlex.quote(str(script_file))
    return f"{escaped_python} {escaped_script}"
