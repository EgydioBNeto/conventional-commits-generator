"""Git operations for the Conventional Commits Generator."""

import logging
import os
import subprocess
import tempfile
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

from ccg.cache import get_cache, invalidate_repository_cache
from ccg.config import GIT_CONFIG, GIT_MESSAGES
from ccg.platform_utils import (
    get_copy_command_for_rebase,
    get_filter_branch_command,
    get_null_editor_command,
    set_file_permissions_secure,
)
from ccg.progress import ProgressSpinner
from ccg.utils import (
    confirm_user_action,
    print_error,
    print_info,
    print_process,
    print_section,
    print_success,
    print_warning,
    read_input,
)

logger = logging.getLogger("ccg.git")


class GitErrorCategory(Enum):
    """Categories of git errors for better error handling.

    Each category contains a list of error patterns to match against
    git error messages. This allows for more specific and helpful
    error messages to users.

    Attributes:
        PERMISSION: Permission and authorization errors (403, 401)
        NETWORK: Network connectivity issues (connection refused, host unreachable)
        AUTHENTICATION: Authentication and credential errors
        REPOSITORY: Repository not found or access rights issues
    """

    PERMISSION = [
        "permission denied",
        "access denied",
        "403 forbidden",
        "401 unauthorized",
    ]

    NETWORK = [
        "ssh: connect to host",
        "connection refused",
        "network unreachable",
        "could not resolve host",
    ]

    AUTHENTICATION = [
        "authentication failed",
        "terminal prompts disabled",
        "could not read username",
        "invalid credentials",
    ]

    REPOSITORY = [
        "not found",
        "fatal: could not read from remote repository",
        "please make sure you have the correct access rights",
    ]


def categorize_git_error(error_text: str) -> Optional[GitErrorCategory]:
    """Categorize a git error by pattern matching.

    Analyzes git error messages and categorizes them into specific
    error types to provide more targeted troubleshooting guidance.

    Args:
        error_text: The error message from git

    Returns:
        GitErrorCategory if recognized, None otherwise

    Examples:
        >>> categorize_git_error("Permission denied (publickey)")
        <GitErrorCategory.PERMISSION: ...>

        >>> categorize_git_error("ssh: connect to host github.com port 22: Connection refused")
        <GitErrorCategory.NETWORK: ...>

        >>> categorize_git_error("authentication failed")
        <GitErrorCategory.AUTHENTICATION: ...>

        >>> categorize_git_error("repository not found")
        <GitErrorCategory.REPOSITORY: ...>

        >>> categorize_git_error("some other error")
        None

    Note:
        Error matching is case-insensitive. If multiple patterns match,
        the first matching category is returned.
    """
    error_lower = error_text.lower()

    for category in GitErrorCategory:
        if any(pattern in error_lower for pattern in category.value):
            return category

    return None


def _execute_git_command(
    command: List[str], timeout: int
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Execute git command and return (success, stdout, stderr).

    Pure function - no logging, no printing, just execution.
    This is the low-level execution layer that focuses solely on running
    the git command and capturing its output.

    Args:
        command: List of command parts (e.g., ["git", "status", "--porcelain"])
        timeout: Maximum seconds to wait for command

    Returns:
        Tuple of (success: bool, stdout: str or None, stderr: str or None):
        - (True, stdout, None) on success
        - (False, None, error_msg) on timeout
        - (False, stdout, stderr) on process error
        - (False, None, "Git is not installed") if git not found

    Examples:
        >>> _execute_git_command(["git", "status"], 60)
        (True, "# On branch main\\n...", None)

        >>> _execute_git_command(["git", "invalid"], 60)
        (False, "", "git: 'invalid' is not a git command...")

    Note:
        This function has no side effects - it doesn't log, print, or modify state.
        It's designed to be easily testable and composable.
    """
    try:
        # Using list format prevents shell injection
        result = subprocess.run(  # nosec B603
            command, capture_output=True, check=True, text=True, timeout=timeout
        )
        return True, result.stdout.strip(), None

    except subprocess.TimeoutExpired:
        return False, None, f"Command timed out after {timeout} seconds"

    except subprocess.CalledProcessError as error:
        error_stdout = error.stdout if error.stdout else None
        error_stderr = error.stderr if error.stderr else None
        return False, error_stdout, error_stderr

    except FileNotFoundError:
        return False, None, "Git is not installed"


def run_git_command(
    command: List[str],
    error_message: str,
    success_message: Optional[str] = None,
    show_output: bool = False,
    timeout: int = GIT_CONFIG.DEFAULT_TIMEOUT,
) -> Tuple[bool, Optional[str]]:
    """Execute a git command with error handling and output capture.

    Central function for all git operations in CCG. Runs the specified git
    command as a subprocess, handles timeouts, captures output, displays
    success/error messages, and returns results in a consistent format.

    This is the user-facing API that adds logging and user feedback on top of
    the low-level _execute_git_command() function.

    Args:
        command: List of command parts (e.g., ["git", "status", "--porcelain"])
        error_message: Message to display if command fails (empty string to suppress)
        success_message: Optional message to display on success
        show_output: If True, return stdout in the second tuple element
        timeout: Maximum seconds to wait for command (default: 60)

    Returns:
        Tuple of (success: bool, output: str or None):
        - (True, output_string) if show_output=True and success
        - (True, None) if show_output=False and success
        - (False, error_string) if show_output=True and failure
        - (False, None) if show_output=False and failure

    Examples:
        >>> run_git_command(["git", "status"], "Failed to get status")
        (True, None)
        >>> run_git_command(["git", "branch"], "", show_output=True)
        (True, "main\\n* feature\\n")

    Note:
        Special handling for GIT_MESSAGES.PUSH_SUCCESS message - displays
        it in a "Remote Push" section for visual clarity
    """
    logger.debug(f"Executing git command: {' '.join(command)}")

    success, stdout, stderr = _execute_git_command(command, timeout)

    if success:
        logger.debug(f"Git command succeeded: {' '.join(command)}")

        if success_message:
            if success_message == GIT_MESSAGES.PUSH_SUCCESS:
                print_section("Remote Push")
            print_success(success_message)

        return (True, stdout) if show_output else (True, None)

    else:
        if stderr and stderr.startswith(GIT_MESSAGES.TIMEOUT_PREFIX):
            logger.error(f"Git command timed out after {timeout}s: {' '.join(command)}")
            print_error(
                f"Command timed out after {timeout} seconds: {' '.join(command)}"
            )
            return False, stderr

        elif stderr and stderr == GIT_MESSAGES.GIT_NOT_INSTALLED:
            logger.critical("Git executable not found in PATH")
            print_error("Git is not installed. Please install Git and try again.")
            return False, None

        else:
            logger.error(f"Git command failed: {' '.join(command)}")
            if stderr:
                logger.error(f"Git stderr: {stderr[:GIT_CONFIG.MAX_LOG_ERROR_CHARS]}")

            if error_message:
                print_error(error_message)

            if show_output:
                error_text = stderr if stderr else stdout
                return False, error_text
            else:
                if stderr and error_message:
                    print(f"\033[91m{stderr}\033[0m")
                return False, None


def git_add(paths: Optional[List[str]] = None) -> bool:
    """Stage changes for commit using git add.

    Stages files or directories for the next commit. If no paths are provided,
    stages all changes in the current directory (git add .).

    Args:
        paths: Optional list of file/directory paths to stage (defaults to ["."])

    Returns:
        True if all paths staged successfully, False if any path fails

    Note:
        Processes each path individually to provide granular error reporting
    """
    if not paths:
        paths = ["."]

    paths_display = ", ".join(paths)
    print_process(f"Staging changes for {paths_display}")

    for path in paths:
        success, _ = run_git_command(
            ["git", "add", path], f"Error during 'git add' for path '{path}'", None
        )
        if not success:
            return False

    print_success("Changes staged successfully")
    return True


def git_commit(commit_message: str) -> bool:
    """Create a git commit with the specified message.

    Executes git commit with the provided message. Displays process and
    success/error messages to user.

    Args:
        commit_message: Complete commit message including subject and optional body

    Returns:
        True if commit created successfully, False on error

    Note:
        Message should already be in conventional commit format when passed here
    """
    logger.info(
        f"Creating commit with message: {commit_message[:GIT_CONFIG.LOG_PREVIEW_LENGTH]}..."
    )
    print_process("Committing changes...")

    with ProgressSpinner("Creating commit"):
        success, _ = run_git_command(
            ["git", "commit", "-m", commit_message],
            "",
            None,
        )

    if success:
        logger.info("Commit created successfully")
        print_success("New commit successfully created!")
        invalidate_repository_cache()
    else:
        logger.error("Commit creation failed")
        print_error("Error during 'git commit'")

    return success


def get_remote_name() -> Optional[str]:
    """Get the name of the primary git remote (cached).

    Retrieves the first configured remote name (typically 'origin').
    This helper function eliminates code duplication across git operations
    that need to know the remote name. Results are cached to reduce
    redundant git command executions.

    Returns:
        Remote name as string, or None if no remote configured

    Examples:
        >>> get_remote_name()
        'origin'

    Note:
        Returns the first remote in the list. If multiple remotes exist,
        this returns the first one alphabetically.
    """

    def fetch_remote_name() -> Optional[str]:
        success, output = run_git_command(
            ["git", "remote"], "Failed to get remote name", show_output=True
        )

        if not success or not output:
            print_error("No remote repository configured")
            return None

        return str(output.split()[0])

    return get_cache().get_or_fetch("remote_name", fetch_remote_name)


def handle_upstream_error(
    branch_name: str, remote_name: str, error_output: str
) -> bool:
    """Handle git push errors related to missing upstream branch configuration.

    Detects if a push failure is due to missing upstream tracking and prompts
    the user to set upstream and retry the push.

    Args:
        branch_name: Name of the current local branch
        remote_name: Name of the remote repository (usually "origin")
        error_output: stderr/stdout from the failed git push command

    Returns:
        True if user wants to set upstream and retry, False otherwise

    Note:
        Looks for specific error messages about upstream configuration
    """
    if (
        "set the remote as upstream" in error_output
        or "no upstream branch" in error_output
    ):
        print_warning("Upstream not set for this branch")
        print_info(
            f"Suggested command: git push --set-upstream {remote_name} {branch_name}"
        )

        from ccg.utils import RESET, YELLOW, confirm_user_action

        return confirm_user_action(
            f"{YELLOW}Do you want to set upstream and push? (y/n){RESET}",
            success_message=None,
            cancel_message="Push cancelled. Changes remain local only.",
        )
    return False


def git_push(set_upstream: bool = False, force: bool = False) -> bool:
    """Push commits to the remote repository with various strategies.

    Pushes local commits to remote, handling upstream configuration and force
    push scenarios. Automatically detects remote name and current branch.
    Provides intelligent error handling for missing upstream branches.

    Args:
        set_upstream: If True, use --set-upstream to create remote branch
        force: If True, force push (overwrites remote history)

    Returns:
        True if push succeeded, False on error

    Note:
        When both set_upstream and force are True, combines both flags.
        Regular push attempts upstream error recovery automatically.
    """
    logger.info(f"Pushing to remote (set_upstream={set_upstream}, force={force})")
    branch_name = get_current_branch()
    if not branch_name:
        logger.error("Could not determine current branch name")
        print_error("Failed to determine current branch name")
        return False

    remote_name = get_remote_name()
    if not remote_name:
        logger.error("No remote repository configured")
        return False

    if set_upstream:
        command = ["git", "push", "--set-upstream"]
        if force:
            command.append("--force")
        command.extend([remote_name, branch_name])

        with ProgressSpinner(f"Pushing to {remote_name}/{branch_name}"):
            success, _ = run_git_command(
                command,
                "",
                "",
            )

        if success:
            print_success(
                f"Branch '{branch_name}' created on remote and changes pushed successfully!"
            )
        else:
            print_error(
                f"Error setting upstream and pushing to '{remote_name}/{branch_name}'"
            )

        return success
    elif force:
        message = f"Force pushing changes to '{remote_name}/{branch_name}'..."
        success_msg = (
            f"Changes force pushed to '{remote_name}/{branch_name}' successfully!"
        )

        print_process(message)
        with ProgressSpinner(f"Force pushing to {remote_name}/{branch_name}"):
            success, _ = run_git_command(["git", "push", "--force"], "", "")

        if success:
            print_success(success_msg)
        else:
            print_error("Error during force push")

        return success
    else:
        print_process("Pushing changes...")
        with ProgressSpinner(f"Pushing to {remote_name}/{branch_name}"):
            success, error_output = run_git_command(
                ["git", "push"],
                "",
                "",
                show_output=True,
            )

        if success:
            print_section("Remote Push")
            print_success(GIT_MESSAGES.PUSH_SUCCESS)
        else:
            if error_output and handle_upstream_error(
                branch_name, remote_name, error_output
            ):
                return git_push(set_upstream=True)
            print_error("Error during 'git push'")
            if error_output:
                logger.error(f"Git push error output: {error_output}")
                print_error(f"Git error: {error_output.strip()}")
            return False

        return success


def create_tag(
    tag_name: str, message: Optional[str] = None, commit_hash: Optional[str] = None
) -> bool:
    """Create a git tag (lightweight or annotated).

    Creates either a lightweight tag (no message) or an annotated tag (with message)
    at the specified commit or current HEAD if no commit is specified.

    Args:
        tag_name: Name of the tag to create (e.g., "v1.0.0")
        message: Optional tag message (creates annotated tag if provided)
        commit_hash: Optional commit hash to tag (defaults to HEAD if not provided)

    Returns:
        True if tag created successfully, False on error

    Note:
        Annotated tags include metadata (tagger, date) and are recommended for releases
    """
    if commit_hash:
        print_process(f"Creating tag '{tag_name}' at commit {commit_hash[:7]}...")
    else:
        print_process(f"Creating tag '{tag_name}'...")

    cmd = ["git", "tag"]
    if message:
        cmd.extend(["-a", tag_name, "-m", message])
    else:
        cmd.append(tag_name)

    if commit_hash:
        cmd.append(commit_hash)

    success, _ = run_git_command(
        cmd,
        f"Error creating tag '{tag_name}'",
        f"Tag '{tag_name}' created successfully",
    )

    return success


def push_tag(tag_name: str) -> bool:
    """Push a specific tag to the remote repository.

    Pushes a previously created tag to the remote, making it available to
    other repository users.

    Args:
        tag_name: Name of the tag to push

    Returns:
        True if tag pushed successfully, False on error

    Note:
        Tag must already exist locally before pushing
    """
    print_process(f"Pushing tag '{tag_name}' to remote...")

    remote_name = get_remote_name()
    if not remote_name:
        return False

    with ProgressSpinner(f"Pushing tag '{tag_name}' to {remote_name}"):
        success, _ = run_git_command(
            ["git", "push", remote_name, tag_name],
            f"Error pushing tag '{tag_name}' to remote",
            "",
        )

    if success:
        print_success(f"Tag '{tag_name}' pushed to remote successfully")

    return success


def discard_local_changes() -> bool:
    """Discard all local changes and untracked files (destructive operation).

    Performs a complete reset of the working directory by unstaging all changes,
    discarding modifications to tracked files, and removing untracked files/directories.

    Returns:
        True if all changes discarded successfully, False on error

    Note:
        DESTRUCTIVE - This cannot be undone. All uncommitted work will be lost.
        Executes: git reset HEAD, git checkout ., git clean -fd
    """
    print_process("Discarding all local changes...")

    with ProgressSpinner("Resetting working directory"):
        success, _ = run_git_command(
            ["git", "reset", "HEAD"],
            "Error while unstaging changes",
        )

        if not success:
            return False

        success, _ = run_git_command(
            ["git", "checkout", "."],
            "Error while discarding local changes",
        )

        if not success:
            return False

        success, _ = run_git_command(
            ["git", "clean", "-fd"],
            "Error while removing untracked files",
        )

    if success:
        print_success("Removed all untracked files and directories")

    return success


def pull_from_remote() -> bool:
    """Pull latest changes from the remote repository.

    Fetches and merges changes from the remote branch that corresponds to
    the current local branch.

    Returns:
        True if pull succeeded, False on error

    Note:
        Uses 120 second timeout (longer than default) as pulling can be slow
        for large repositories or slow network connections
    """
    print_process("Pulling latest changes from remote...")

    remote_name = get_remote_name()
    if not remote_name:
        return False

    branch_name = get_current_branch()
    if not branch_name:
        print_error("Failed to determine current branch name")
        return False

    with ProgressSpinner(f"Pulling from {remote_name}/{branch_name}"):
        success, _ = run_git_command(
            ["git", "pull", remote_name, branch_name],
            "",
            "",
            timeout=GIT_CONFIG.PULL_TIMEOUT,
        )

    if success:
        print_success(f"Successfully pulled from {remote_name}/{branch_name}")
    else:
        print_error(f"Error pulling from {remote_name}/{branch_name}")

    return success


def get_staged_files() -> List[str]:
    """Get list of files currently staged for commit.

    Retrieves the names of all files that have been staged with git add and
    are ready to be committed.

    Returns:
        List of file paths (relative to repository root), empty list on error

    Note:
        Used by pre-commit hooks to determine which files to check
    """
    success, output = run_git_command(
        ["git", "diff", "--name-only", "--cached"],
        "Failed to get staged files",
        show_output=True,
    )

    if success and output:
        return [file for file in output.split("\n") if file]
    return []


def get_staged_file_changes() -> List[Tuple[str, str]]:
    """Get list of staged files with their status (A, M, D).

    Retrieves the status (Added, Modified, Deleted) and path of all files
    currently staged for commit.

    Returns:
        List of tuples, where each tuple contains (status, file_path).
        Returns an empty list on error or if no files are staged.

    Examples:
        >>> get_staged_file_changes()
        [('A', 'new_file.txt'), ('M', 'modified_file.py'), ('D', 'deleted_file.js')]
    """
    success, output = run_git_command(
        ["git", "diff", "--name-status", "--cached"],
        "Failed to get staged file changes",
        show_output=True,
    )

    if success and output:
        changes = []
        for line in output.split("\n"):
            if line:
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    status, file_path = parts
                    changes.append((status.strip(), file_path.strip()))
        return changes
    return []


def check_is_git_repo() -> bool:
    """Check if current directory is inside a git repository.

    Verifies that git operations can be performed in the current directory
    by checking if it's within a git working tree.

    Returns:
        True if inside a git repository, False otherwise

    Note:
        This is used as a guard check before most git operations
    """
    success, _ = run_git_command(
        ["git", "rev-parse", "--is-inside-work-tree"],
        "Not a git repository",
        show_output=True,
    )
    return success


def check_has_changes(paths: Optional[List[str]] = None) -> bool:
    """Check if there are any uncommitted changes in the working directory.

    Examines the working directory for modified, added, or deleted files.
    Can check entire repository or specific paths.

    Args:
        paths: Optional list of specific paths to check (defaults to entire repository)

    Returns:
        True if changes detected, False if working directory is clean

    Note:
        Uses git status --porcelain for machine-readable output
    """
    if not paths:
        print_process("Checking for changes in the working directory...")
        success, output = run_git_command(
            ["git", "status", "--porcelain"],
            "Failed to check for changes",
            show_output=True,
        )

        if success:
            if not output:
                print_info("No changes detected in the working directory")
                return False
            print_success("Changes detected in the working directory")
            return True
        return False

    paths_display = ", ".join(paths)
    print_process(f"Checking for changes in: {paths_display}...")

    for path in paths:
        success, output = run_git_command(
            ["git", "status", "--porcelain", path],
            f"Failed to check for changes in '{path}'",
            show_output=True,
        )

        if success and output:
            print_success(f"Changes detected in: {path}")
            return True

    print_info(f"No changes detected in the specified path(s): {paths_display}")
    return False


def has_commits_to_push() -> bool:
    """Check if there are local commits that need to be pushed to remote.

    Compares the local branch with its remote tracking branch to determine
    if there are any commits that haven't been pushed yet.

    Returns:
        True if there are commits to push, False if branch is up to date or has no upstream

    Note:
        Returns False if branch has no upstream tracking branch configured
    """
    print_process("Checking for commits to push...")

    # First check if current branch has an upstream
    success, output = run_git_command(
        ["git", "rev-parse", "--abbrev-ref", "@{u}"],
        "Failed to check upstream branch",
        show_output=True,
    )

    if not success or not output:
        print_info("No upstream branch configured")
        return False

    # Count commits ahead of upstream
    success, output = run_git_command(
        ["git", "rev-list", "--count", "@{u}..HEAD"],
        "Failed to count commits ahead",
        show_output=True,
    )

    if success and output:
        commit_count = int(output.strip())
        if commit_count > 0:
            commit_word = "commit" if commit_count == 1 else "commits"
            print_success(f"{commit_count} {commit_word} ready to push")
            return True
        print_info("No commits to push - branch is up to date")
        return False

    return False


def _handle_remote_access_error(remote_name: str, error_output: Optional[str]) -> None:
    """Display appropriate error messages based on remote access failure.

    Uses error categorization to provide specific troubleshooting guidance based
    on the type of error encountered (permission, network, authentication, or repository).

    Args:
        remote_name: Name of the remote repository
        error_output: Error output from git ls-remote command

    Note:
        Provides category-specific error messages with actionable troubleshooting steps
    """
    if not error_output:
        print_error(f"Cannot access remote repository '{remote_name}'")
        return

    error_category = categorize_git_error(error_output)

    if error_category in (GitErrorCategory.PERMISSION, GitErrorCategory.AUTHENTICATION):
        print_error(
            "ACCESS DENIED: You don't have permission to access this repository."
        )
        print_error("Please check:")
        print_error("  • You have push access to this repository")
        print_error("  • The repository URL is correct")
        print_error("  • You're logged in with the correct account")
        print_error("Cannot proceed without repository access. Exiting.")

    elif error_category == GitErrorCategory.NETWORK:
        print_error("NETWORK ERROR: Cannot connect to remote repository")
        print_error("Please check:")
        print_error("  • Your internet connection")
        print_error("  • Firewall settings")
        print_error("  • VPN configuration (if applicable)")

    elif error_category == GitErrorCategory.REPOSITORY:
        print_error(f"REPOSITORY ERROR: '{remote_name}' not found or inaccessible")
        print_error("Please verify:")
        print_error("  • Repository URL is correct")
        print_error("  • Repository exists on remote")
        print_error("  • You have access to the repository")

    else:
        print_error(f"Cannot access remote repository '{remote_name}'")
        print_error("This could be due to network issues or repository configuration.")


def check_remote_access() -> bool:
    """Verify that the remote repository is accessible and user has permissions.

    Performs comprehensive check of remote connectivity and access permissions
    using git ls-remote. Detects and provides helpful error messages for common
    issues like authentication failures, network problems, or missing permissions.

    Returns:
        True if remote is accessible and user has access, False otherwise

    Note:
        Uses 15 second timeout and disables terminal prompts to avoid hanging.
        Provides detailed error messages for different failure scenarios including
        permission denied, network issues, and repository not found.
    """
    print_process("Checking remote repository access...")

    success, output = run_git_command(
        ["git", "remote", "-v"], "Failed to check remote repositories", show_output=True
    )

    if not success or not output:
        print_info("No remote repository configured.")
        return False

    remote_name = output.split()[0] if output else "origin"

    try:
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_ASKPASS"] = "true"

        with ProgressSpinner(f"Checking access to {remote_name}"):
            result = subprocess.run(  # nosec B603
                ["git", "ls-remote", "--exit-code", remote_name],
                capture_output=True,
                text=True,
                timeout=GIT_CONFIG.REMOTE_CHECK_TIMEOUT,
                env=env,
            )

        if result.returncode == 0:
            print_success(f"Remote repository '{remote_name}' is accessible")
            return True

        error_output = result.stderr if result.stderr else result.stdout
        _handle_remote_access_error(remote_name, error_output)
        return False

    except subprocess.TimeoutExpired:
        print_error("Remote repository check timed out")
        print_error("This could indicate network issues or authentication problems.")
        return False
    except (OSError, subprocess.SubprocessError, Exception) as e:
        print_error(f"Failed to check remote repository access: {str(e)}")
        return False


def get_current_branch() -> Optional[str]:
    """Get the name of the current git branch (cached).

    Retrieves the name of the currently checked out branch.
    Results are cached to reduce redundant git command executions.

    Returns:
        Branch name as string, or None if unable to determine (e.g., detached HEAD)

    Note:
        Returns branch name only, not full ref path (e.g., "main" not "refs/heads/main")
    """

    def fetch_branch() -> Optional[str]:
        success, output = run_git_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            "Failed to get current branch name",
            show_output=True,
        )

        if success and output:
            return output
        return None

    return get_cache().get_or_fetch("branch", fetch_branch)


def get_repository_name() -> Optional[str]:
    """Get the name of the current git repository (cached).

    Results are cached to reduce redundant git command executions.

    Returns:
        Repository name or None if unable to determine
    """

    def fetch_repo_name() -> Optional[str]:
        success, output = run_git_command(
            ["git", "rev-parse", "--show-toplevel"],
            "Failed to get repository root",
            show_output=True,
        )

        if success and output:
            return os.path.basename(output)
        return None

    return get_cache().get_or_fetch("repo_name", fetch_repo_name)


def get_repository_root() -> Optional[str]:
    """Get the root directory of the current git repository (cached).

    Results are cached to reduce redundant git command executions.

    Returns:
        Absolute path to repository root or None if unable to determine
    """

    def fetch_repo_root() -> Optional[str]:
        success, output = run_git_command(
            ["git", "rev-parse", "--show-toplevel"],
            "Failed to get repository root",
            show_output=True,
        )

        if success and output:
            return output
        return None

    return get_cache().get_or_fetch("repo_root", fetch_repo_root)


def is_path_in_repository(path: str, repo_root: str) -> bool:
    """Check if a path is within the git repository.

    Args:
        path: Path to check
        repo_root: Root directory of the git repository

    Returns:
        True if path is within repository, False otherwise
    """
    if not repo_root or not path:
        return False

    abs_path = os.path.abspath(path)
    abs_repo_root = os.path.abspath(repo_root)

    try:
        os.path.relpath(abs_path, abs_repo_root)
        return abs_path.startswith(abs_repo_root)
    except ValueError:
        return False


def branch_exists_on_remote(branch_name: str) -> bool:
    """Check if a branch exists on the remote repository.

    Queries the remote repository to determine if the specified branch
    exists there, useful for deciding whether to create upstream or push normally.

    Args:
        branch_name: Name of the branch to check

    Returns:
        True if branch exists on remote, False otherwise

    Note:
        Uses 30 second timeout for ls-remote operation as it requires network access
    """
    remote_name = get_remote_name()
    if not remote_name:
        return False

    with ProgressSpinner(f"Checking if branch '{branch_name}' exists on {remote_name}"):
        success, output = run_git_command(
            ["git", "ls-remote", "--heads", remote_name, branch_name],
            f"Failed to check if branch '{branch_name}' exists on remote",
            show_output=True,
            timeout=GIT_CONFIG.TAG_PUSH_TIMEOUT,
        )

    return success and bool(output)


def get_recent_commits(
    count: Optional[int] = None,
) -> List[Tuple[str, str, str, str, str]]:
    """Retrieve a list of recent commits with their metadata.

    Gets commit history with formatted output including hashes, subject, author,
    and relative date.

    Args:
        count: Optional number of commits to retrieve (None = all commits)

    Returns:
        List of tuples, each containing:
        (full_hash, short_hash, subject, author, relative_date)
        Returns empty list on error

    Examples:
        >>> commits = get_recent_commits(5)
        >>> len(commits)
        5
        >>> commits[0][2]  # Subject of most recent commit
        'feat: add new feature'

    Note:
        Uses custom format string to parse commit data reliably
    """
    commit_log_format = "%H|%h|%s|%an|%ar"
    command = ["git", "log", f"--pretty=format:{commit_log_format}"]
    if count is not None and count > 0:
        command.append(f"-{count}")

    success, output = run_git_command(
        command, f"Failed to retrieve recent commits", show_output=True
    )

    if not success or not output:
        return []

    commits: List[Tuple[str, str, str, str, str]] = []
    for line in output.split("\n"):
        if line:
            parts = line.split("|")
            if len(parts) >= 5:
                full_hash, short_hash, subject, author, date = parts
                commits.append((full_hash, short_hash, subject, author, date))

    return commits


def get_commit_by_hash(
    commit_hash: str,
) -> Optional[Tuple[str, str, str, str, str, str]]:
    """Retrieve detailed information about a specific commit by its hash.

    Fetches comprehensive commit metadata including message, author, and date.
    Accepts both full and partial hashes.

    Args:
        commit_hash: Full or partial commit hash to look up

    Returns:
        Tuple containing (full_hash, short_hash, subject, body, author, date)
        or None if commit not found

    Note:
        Subject and body are separated from the full commit message.
        Body will be empty string if commit has no body.
    """
    success, _ = run_git_command(
        ["git", "rev-parse", "--verify", commit_hash],
        f"Commit '{commit_hash}' not found",
        show_output=True,
    )

    if not success:
        return None

    success, full_hash = run_git_command(
        ["git", "rev-parse", commit_hash],
        f"Failed to get full hash for '{commit_hash}'",
        show_output=True,
    )

    if not success or not full_hash:
        return None

    success, short_hash = run_git_command(
        ["git", "rev-parse", "--short", commit_hash],
        f"Failed to get short hash for '{commit_hash}'",
        show_output=True,
    )

    if not success or not short_hash:
        short_hash = commit_hash[: GIT_CONFIG.SHORT_HASH_LENGTH]

    success, commit_message = run_git_command(
        ["git", "log", "-1", "--pretty=%B", commit_hash],
        f"Failed to get commit message for '{commit_hash}'",
        show_output=True,
    )

    if not success or not commit_message:
        return None

    commit_message_parts = commit_message.strip().split("\n\n", 1)
    subject = commit_message_parts[0].strip()
    body = commit_message_parts[1].strip() if len(commit_message_parts) > 1 else ""

    success, author = run_git_command(
        ["git", "log", "-1", "--pretty=%an", commit_hash],
        f"Failed to get author for '{commit_hash}'",
        show_output=True,
    )

    if not success or not author:
        author = "Unknown"

    success, date = run_git_command(
        ["git", "log", "-1", "--pretty=%ar", commit_hash],
        f"Failed to get date for '{commit_hash}'",
        show_output=True,
    )

    if not success or not date:
        date = "Unknown date"

    return (full_hash, short_hash, subject, body, author, date)


def edit_commit_message(
    commit_hash: str, new_message: str, new_body: Optional[str] = None
) -> bool:
    """Edit a commit message by hash, using appropriate strategy based on position.

    Uses the Strategy Pattern to automatically choose between amend (for latest commit)
    and filter-branch (for older commits). Detects if editing the initial commit.

    Args:
        commit_hash: Full hash of commit to edit
        new_message: New commit subject line
        new_body: Optional new commit body

    Returns:
        True if edit succeeded, False on error

    Note:
        Automatically selects the most efficient editing method using strategies
    """
    from ccg.git_strategies import edit_commit_with_strategy

    success, latest_commit = run_git_command(
        ["git", "rev-parse", "HEAD"],
        "Failed to get latest commit hash",
        show_output=True,
    )

    if not success or not latest_commit:
        return False

    is_initial_commit = False
    if latest_commit != commit_hash:
        success, output = run_git_command(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            "Failed to find initial commit",
            show_output=True,
        )

        if success and output and commit_hash in output:
            is_initial_commit = True
            print_info("Detected that you're editing the initial commit")

    return edit_commit_with_strategy(
        commit_hash=commit_hash,
        latest_commit_hash=latest_commit,
        new_message=new_message,
        new_body=new_body,
        is_initial_commit=is_initial_commit,
    )


def delete_latest_commit() -> bool:
    """Delete the most recent commit using git reset.

    Removes the latest commit while keeping the working directory clean.
    More efficient than rebase for deleting the most recent commit.

    Returns:
        True if commit deleted successfully, False on error

    Note:
        DESTRUCTIVE - Commit is permanently removed from history.
        Uses --hard flag which discards the commit entirely.
    """
    print_process("Deleting latest commit...")
    success, _ = run_git_command(
        ["git", "reset", "--hard", "HEAD~1"],
        "Failed to delete latest commit",
        "Latest commit deleted successfully",
    )
    return success


def create_rebase_script_for_deletion(
    commit_hash: str,
) -> Tuple[bool, Optional[str], List[str]]:
    """Create a rebase script file for deleting a specific commit.

    Generates a git rebase todo script that excludes the target commit,
    effectively removing it from history when the rebase is executed.

    Args:
        commit_hash: Full hash of commit to delete

    Returns:
        Tuple of (success, script_file_path, script_lines):
        - success: True if script created, False on error
        - script_file_path: Path to temporary script file, or None on error
        - script_lines: List of rebase commands, empty on error

    Note:
        Caller is responsible for cleaning up the temporary script file
    """
    success, all_commits = run_git_command(
        ["git", "rev-list", "--reverse", "HEAD"],
        "Failed to get commit history",
        show_output=True,
    )

    if not success:
        return False, None, []

    commits = (
        all_commits.strip().split("\n") if all_commits and all_commits.strip() else []
    )
    rebase_script: List[str] = []
    found_target = False

    for commit in commits:
        if commit == commit_hash:
            found_target = True
            print_info(
                f"Removing commit {commit[:GIT_CONFIG.SHORT_HASH_LENGTH]} from history"
            )
            continue
        else:
            success, subject = run_git_command(
                ["git", "log", "-1", "--format=%s", commit],
                f"Failed to get subject for commit {commit[:GIT_CONFIG.SHORT_HASH_LENGTH]}",
                show_output=True,
            )
            if success and subject:
                rebase_script.append(
                    f"pick {commit[:GIT_CONFIG.SHORT_HASH_LENGTH]} {subject.strip()}"
                )

    if not found_target:
        print_error(
            f"Commit '{commit_hash[:GIT_CONFIG.SHORT_HASH_LENGTH]}' not found in repository history"
        )
        return False, None, []

    script_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("\n".join(rebase_script) + "\n")
            script_file = f.name
        # Set restrictive permissions (cross-platform)
        set_file_permissions_secure(script_file)
    except (IOError, OSError, PermissionError) as e:
        print_error(f"Failed to create temporary rebase script: {str(e)}")
        return False, None, []

    return True, script_file, rebase_script


def delete_old_commit_with_rebase(commit_hash: str) -> bool:
    """Delete an old commit using interactive rebase.

    Removes a commit that is not the latest one by performing an interactive
    rebase with a pre-generated script that excludes the target commit.

    Args:
        commit_hash: Full hash of commit to delete

    Returns:
        True if commit deleted successfully, False on error

    Note:
        REWRITES HISTORY - Changes all descendant commit hashes.
        Uses 120 second timeout for rebase operation.
        Automatically aborts rebase on failure to prevent repository corruption.
        If deleting all commits, creates empty repository with update-ref.
        Cleans up all temporary files (.txt script and .sh script on Windows).
    """
    script_file = None
    temp_script = None
    try:
        success, script_file, rebase_script = create_rebase_script_for_deletion(
            commit_hash
        )
        if not success or not script_file:
            return False

        if not rebase_script:
            print_warning("This would remove all commits. Creating empty repository...")
            success, _ = run_git_command(
                ["git", "update-ref", "-d", "HEAD"],
                f"Failed to create empty repository",
                f"All commits removed - repository is now empty",
            )
            return success

        try:
            env = os.environ.copy()
            # Use cross-platform copy command for GIT_SEQUENCE_EDITOR
            # On Windows, this creates a temporary shell script that must be cleaned up
            copy_command, temp_script = get_copy_command_for_rebase(Path(script_file))
            env["GIT_SEQUENCE_EDITOR"] = copy_command
            # Use cross-platform null editor for GIT_EDITOR
            env["GIT_EDITOR"] = get_null_editor_command()

            with ProgressSpinner("Deleting commit via rebase"):
                result = subprocess.run(  # nosec B603
                    ["git", "rebase", "-i", "--root"],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=GIT_CONFIG.REBASE_TIMEOUT,
                )

            if result.returncode == 0:
                print_success(
                    f"Commit '{commit_hash[:GIT_CONFIG.SHORT_HASH_LENGTH]}' deleted successfully"
                )
                return True
            else:
                # Check if it's a conflict that needs manual resolution
                stderr_lower = result.stderr.lower() if result.stderr else ""
                is_conflict = any(
                    keyword in stderr_lower
                    for keyword in ["conflict", "could not apply", "merge conflict"]
                )

                if is_conflict:
                    # Show clear conflict message
                    print_error("=" * 70)
                    print_error(
                        f"CONFLICT: Cannot delete commit '{commit_hash[:GIT_CONFIG.SHORT_HASH_LENGTH]}' cleanly"
                    )
                    print_error("=" * 70)

                    # Show conflicting files using git status
                    status_cmd = subprocess.run(  # nosec B603
                        ["git", "status", "--short"],
                        capture_output=True,
                        text=True,
                    )

                    if status_cmd.returncode == 0 and status_cmd.stdout:
                        conflict_lines = [
                            line
                            for line in status_cmd.stdout.split("\n")
                            if any(
                                marker in line
                                for marker in ["UU ", "AA ", "DD ", "DU ", "UD "]
                            )
                        ]

                        if conflict_lines:
                            print_error("Conflicting files:")
                            for line in conflict_lines:
                                print_error(f"  {line}")

                    # Clear instructions
                    print_info("TO RESOLVE:")
                    print_info("  1. Open the conflicting files in your editor")
                    print_info("  2. Look for <<<<<<< markers and resolve conflicts")
                    print_info("  3. Save the files")
                    print_info("  4. Stage resolved files: git add <file>")
                    print_info("  5. Press Enter here to continue")
                    print_warning("OR type 'abort' to cancel the deletion")

                    # Wait for user
                    user_choice = (
                        read_input(
                            "Press Enter when conflicts are resolved (or 'abort'): "
                        )
                        .strip()
                        .lower()
                    )

                    if user_choice == "abort":
                        run_git_command(["git", "rebase", "--abort"], "", "")
                        print_info("Deletion cancelled. Repository restored.")
                        return False

                    # Try to continue
                    print_process("Continuing rebase...")
                    cont_cmd = subprocess.run(  # nosec B603
                        ["git", "rebase", "--continue"],
                        capture_output=True,
                        text=True,
                        timeout=GIT_CONFIG.REBASE_TIMEOUT,
                    )

                    if cont_cmd.returncode == 0:
                        print_success(
                            f"Commit '{commit_hash[:GIT_CONFIG.SHORT_HASH_LENGTH]}' deleted successfully!"
                        )
                        return True

                    # Still has problems
                    print_error("Failed to continue. Details:")
                    if cont_cmd.stdout:
                        for line in cont_cmd.stdout.strip().split("\n"):
                            if line.strip():
                                print_error(line)
                    if cont_cmd.stderr:
                        for line in cont_cmd.stderr.strip().split("\n"):
                            if line.strip():
                                print_error(line)

                    # Check for remaining conflicts
                    recheck_status = subprocess.run(  # nosec B603
                        ["git", "status", "--short"],
                        capture_output=True,
                        text=True,
                    )

                    if recheck_status.returncode == 0:
                        remaining = [
                            line
                            for line in recheck_status.stdout.split("\n")
                            if any(marker in line for marker in ["UU ", "AA ", "DD "])
                        ]

                        if remaining:
                            print_error("Still has conflicts in:")
                            for line in remaining:
                                print_error(f"  {line}")
                            print_error(
                                "All conflicts must be resolved before continuing."
                            )

                    print_error("Aborting rebase and restoring repository...")
                    run_git_command(["git", "rebase", "--abort"], "", "")
                    print_info("Repository restored to original state.")
                    return False
                else:
                    print_error(
                        f"Failed to delete commit '{commit_hash[:GIT_CONFIG.SHORT_HASH_LENGTH]}'"
                    )
                    if result.stderr:
                        print_error("Error details:")
                        for line in result.stderr.strip().split("\n"):
                            print(line)
                    run_git_command(["git", "rebase", "--abort"], "", "")
                    return False

        except subprocess.TimeoutExpired:
            print_error("Rebase operation timed out")
            run_git_command(["git", "rebase", "--abort"], "", "")
            return False
        except (OSError, subprocess.SubprocessError, Exception) as e:
            print_error(f"Error during rebase: {str(e)}")
            run_git_command(["git", "rebase", "--abort"], "", "")
            return False
    finally:
        # Clean up script file (.txt)
        if script_file:
            try:
                if os.path.exists(script_file):
                    os.unlink(script_file)
                    logger.debug(f"Deleted temporary rebase script: {script_file}")
            except Exception as e:
                logger.warning(f"Failed to delete script file {script_file}: {e}")

        # Clean up temp script (.sh) - Windows only
        if temp_script:
            try:
                # temp_script is a Path object, convert to string for os.path.exists
                temp_script_str = str(temp_script)
                if os.path.exists(temp_script_str):
                    os.unlink(temp_script_str)
                    logger.debug(f"Deleted temporary script: {temp_script_str}")
            except Exception as e:
                logger.warning(f"Failed to delete temp script {temp_script}: {e}")


def delete_commit(commit_hash: str) -> bool:
    """Delete a commit by hash, using appropriate method based on position.

    Intelligently chooses between reset (for latest commit) and rebase
    (for older commits). Verifies commit exists before attempting deletion.

    Args:
        commit_hash: Full or partial hash of commit to delete

    Returns:
        True if deletion succeeded, False on error

    Note:
        DESTRUCTIVE - Commit is permanently removed from history.
        Automatically selects the most efficient deletion method.
    """
    success, _ = run_git_command(
        ["git", "cat-file", "-e", commit_hash],
        f"Commit '{commit_hash}' not found or not accessible",
        show_output=True,
    )

    if not success:
        return False

    success, latest_commit = run_git_command(
        ["git", "rev-parse", "HEAD"],
        "Failed to get latest commit hash",
        show_output=True,
    )

    if not success or not latest_commit:
        return False

    is_latest = latest_commit.strip() == commit_hash

    if is_latest:
        return delete_latest_commit()
    else:
        return delete_old_commit_with_rebase(commit_hash)


def run_pre_commit_hooks(staged_files: List[str]) -> bool:
    """Execute pre-commit hooks on specified staged files.

    Runs the pre-commit framework's hooks on the provided file list to
    validate code quality before committing.

    Args:
        staged_files: List of file paths to check with pre-commit

    Returns:
        True if all hooks passed, False if any hook failed or on error

    Note:
        Uses 120 second timeout as some hooks (linters, formatters) can be slow.
        Displays hook output to user for debugging failed checks.
    """
    try:
        with ProgressSpinner("Running pre-commit hooks"):
            result = subprocess.run(  # nosec B603
                ["pre-commit", "run", "--files"] + staged_files,
                capture_output=True,
                text=True,
                timeout=GIT_CONFIG.PRE_COMMIT_TIMEOUT,
            )

        if result.returncode != 0:
            print_error("Some pre-commit checks failed:")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"\033[91m{result.stderr}\033[0m")
            print_warning(
                "Please fix the issues reported by pre-commit and run ccg again."
            )
            return False

        print_success("All pre-commit checks passed successfully")
        return True
    except subprocess.TimeoutExpired:
        print_error("Pre-commit checks timed out after 120 seconds")
        print_warning("Please fix any potential issues and run ccg again.")
        return False
    except subprocess.CalledProcessError as e:
        print_error("Error running pre-commit:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(f"\033[91m{e.stderr}\033[0m")
        print_warning(
            "Please ensure pre-commit is configured correctly and run ccg again."
        )
        return False
    except (OSError, subprocess.SubprocessError, Exception) as e:
        print_error(f"Unexpected error running pre-commit checks: {str(e)}")
        print_warning("Please fix the issues and run ccg again.")
        return False


def check_and_install_pre_commit() -> bool:
    """Check for pre-commit configuration and run hooks if present.

    Detects if pre-commit is configured, verifies it's installed, installs
    hooks if needed, and runs all hooks on staged files.

    Returns:
        True if no config exists, or if pre-commit installed and all hooks passed
        False if pre-commit not installed or hooks failed

    Note:
        Gracefully skips if no .pre-commit-config.yaml exists.
        Provides helpful installation instructions if pre-commit not found.
    """
    try:
        if not os.path.exists(".pre-commit-config.yaml"):
            print_info("No pre-commit configuration found. Skipping pre-commit checks.")
            return True

        try:
            subprocess.run(  # nosec B603
                ["pre-commit", "--version"],
                capture_output=True,
                check=True,
                text=True,
                timeout=GIT_CONFIG.STATUS_CHECK_TIMEOUT,
            )
            pre_commit_installed = True
        except FileNotFoundError:
            pre_commit_installed = False
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pre_commit_installed = True

        if not pre_commit_installed:
            print_warning("pre-commit is configured but not installed.")
            print_info("Run 'pip install pre-commit' to install it.")
            print_info(
                "After installing, run 'pre-commit install' to set up the hooks."
            )
            return False

        print_process("Setting up pre-commit hooks...")
        hooks_installed, _ = run_git_command(
            ["pre-commit", "install"],
            "Failed to install pre-commit hooks",
            "Pre-commit hooks installed successfully",
        )

        if not hooks_installed:
            return False

        print_process("Running pre-commit checks on staged files...")
        staged_files = get_staged_files()

        if staged_files:
            return run_pre_commit_hooks(staged_files)

        return True

    except (OSError, subprocess.SubprocessError, FileNotFoundError, Exception) as e:
        print_error(f"Unexpected error during pre-commit checks: {str(e)}")
        return False
