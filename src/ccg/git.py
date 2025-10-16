"""Git operations for the Conventional Commits Generator."""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from ccg.cache import get_cache, invalidate_repository_cache
from ccg.config import GIT_CONFIG
from ccg.progress import ProgressSpinner
from ccg.utils import (
    print_error,
    print_info,
    print_process,
    print_section,
    print_success,
    print_warning,
)

logger = logging.getLogger("ccg.git")


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
        Special handling for "Changes pushed successfully!" message - displays
        it in a "Remote Push" section for visual clarity
    """
    logger.debug(f"Executing git command: {' '.join(command)}")

    try:
        result = subprocess.run(
            command, capture_output=True, check=True, text=True, timeout=timeout
        )

        logger.debug(f"Git command succeeded: {' '.join(command)}")
        if success_message:
            if success_message == "Changes pushed successfully!":
                print_section("Remote Push")
                print_success(success_message)
            else:
                print_success(success_message)
        if show_output:
            return True, result.stdout.strip()
        return True, None

    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out after {timeout}s: {' '.join(command)}")
        print_error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        return False, f"Command timed out after {timeout} seconds"
    except subprocess.CalledProcessError as error:
        logger.error(f"Git command failed (exit {error.returncode}): {' '.join(command)}")
        if error.stderr:
            logger.error(f"Git stderr: {error.stderr[:500]}")  # Log first 500 chars
        if error_message:
            print_error(error_message)
        if show_output:
            error_text = error.stderr if error.stderr else error.stdout
            return False, error_text
        else:
            if error.stderr and error_message:
                print(f"\033[91m{error.stderr}\033[0m")
            return False, None
    except FileNotFoundError:
        logger.critical("Git executable not found in PATH")
        print_error("Git is not installed. Please install Git and try again.")
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

    path_str = ", ".join(paths)
    print_process(f"Staging changes for {path_str}")

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
    logger.info(f"Creating commit with message: {commit_message[:80]}...")
    print_process("Committing changes...")

    with ProgressSpinner("Creating commit"):
        success, _ = run_git_command(
            ["git", "commit", "-m", commit_message],
            "Error during 'git commit'",
            None,  # Don't print success message inside spinner
        )

    if success:
        logger.info("Commit created successfully")
        print_success("New commit successfully created!")
        invalidate_repository_cache()
    else:
        logger.error("Commit creation failed")

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


def handle_upstream_error(branch_name: str, remote_name: str, error_output: str) -> bool:
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
    if "set the remote as upstream" in error_output or "no upstream branch" in error_output:
        print_warning("Upstream not set for this branch")
        print_info(f"Suggested command: git push --set-upstream {remote_name} {branch_name}")

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
                f"Error setting upstream and pushing to '{remote_name}/{branch_name}'",
                None,  # Don't print success message inside spinner
            )

        if success:
            print_success(
                f"Branch '{branch_name}' created on remote and changes pushed successfully!"
            )

        return success
    elif force:
        message = f"Force pushing changes to '{remote_name}/{branch_name}'..."
        success_msg = f"Changes force pushed to '{remote_name}/{branch_name}' successfully!"

        print_process(message)
        with ProgressSpinner(f"Force pushing to {remote_name}/{branch_name}"):
            success, _ = run_git_command(
                ["git", "push", "--force"], "Error during force push", None
            )

        if success:
            print_success(success_msg)

        return success
    else:
        print_process("Pushing changes...")
        with ProgressSpinner(f"Pushing to {remote_name}/{branch_name}"):
            success, error_output = run_git_command(
                ["git", "push"],
                "Error during 'git push'",
                None,  # Don't print success message inside spinner
                show_output=True,
            )

        # Print success message after spinner has stopped
        if success:
            print_section("Remote Push")
            print_success("Changes pushed successfully!")

        if not success and error_output:
            if handle_upstream_error(branch_name, remote_name, error_output):
                return git_push(set_upstream=True)
            return False

        return success


def create_tag(tag_name: str, message: Optional[str] = None) -> bool:
    """Create a git tag (lightweight or annotated).

    Creates either a lightweight tag (no message) or an annotated tag (with message)
    at the current HEAD commit.

    Args:
        tag_name: Name of the tag to create (e.g., "v1.0.0")
        message: Optional tag message (creates annotated tag if provided)

    Returns:
        True if tag created successfully, False on error

    Note:
        Annotated tags include metadata (tagger, date) and are recommended for releases
    """
    print_process(f"Creating tag '{tag_name}'...")

    if message:
        success, _ = run_git_command(
            ["git", "tag", "-a", tag_name, "-m", message],
            f"Error creating tag '{tag_name}'",
            f"Tag '{tag_name}' created successfully",
        )
    else:
        success, _ = run_git_command(
            ["git", "tag", tag_name],
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

    success, _ = run_git_command(
        ["git", "push", remote_name, tag_name],
        f"Error pushing tag '{tag_name}' to remote",
        f"Tag '{tag_name}' pushed to remote successfully",
    )

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
        "Removed all untracked files and directories",
    )

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
            f"Error pulling from {remote_name}/{branch_name}",
            timeout=120,
        )

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

    path_str = ", ".join(paths)
    print_process(f"Checking for changes in: {path_str}...")

    for path in paths:
        success, output = run_git_command(
            ["git", "status", "--porcelain", path],
            f"Failed to check for changes in '{path}'",
            show_output=True,
        )

        if success and output:
            print_success(f"Changes detected in: {path}")
            return True

    print_info(f"No changes detected in the specified path(s): {path_str}")
    return False


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

        result = subprocess.run(
            ["git", "ls-remote", "--exit-code", remote_name],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )

        if result.returncode == 0:
            print_success(f"Remote repository '{remote_name}' is accessible")
            return True
        else:
            error_output = result.stderr if result.stderr else result.stdout
            if error_output:
                error_text = error_output.lower()
                permission_indicators = [
                    "permission denied",
                    "access denied",
                    "authentication failed",
                    "fatal: could not read from remote repository",
                    "please make sure you have the correct access rights",
                    "repository not found",
                    "403 forbidden",
                    "401 unauthorized",
                    "ssh: connect to host",
                    "connection refused",
                    "terminal prompts disabled",
                    "could not read username",
                ]

                if any(indicator in error_text for indicator in permission_indicators):
                    print_error(
                        "ACCESS DENIED: You don't have permission to access this repository."
                    )
                    print_error("Please check:")
                    print_error("   You have push access to this repository")
                    print_error("   The repository URL is correct")
                    print_error("   You're logged in with the correct account")
                    print_error("Cannot proceed without repository access. Exiting.")
                    return False
                else:
                    print_error(f"Cannot access remote repository '{remote_name}'")
                    print_error("This could be due to network issues or repository configuration.")
                    return False
            else:
                print_error(f"Cannot access remote repository '{remote_name}'")
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

    success, output = run_git_command(
        ["git", "ls-remote", "--heads", remote_name, branch_name],
        f"Failed to check if branch '{branch_name}' exists on remote",
        show_output=True,
        timeout=30,
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
    format_str = "%H|%h|%s|%an|%ar"
    command = ["git", "log", f"--pretty=format:{format_str}"]
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
        short_hash = commit_hash[:7]

    success, commit_message = run_git_command(
        ["git", "log", "-1", "--pretty=%B", commit_hash],
        f"Failed to get commit message for '{commit_hash}'",
        show_output=True,
    )

    if not success or not commit_message:
        return None

    message_parts = commit_message.strip().split("\n\n", 1)
    subject = message_parts[0].strip()
    body = message_parts[1].strip() if len(message_parts) > 1 else ""

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


def edit_latest_commit_with_amend(
    commit_hash: str, new_message: str, new_body: Optional[str] = None
) -> bool:
    """Edit the most recent commit using git commit --amend.

    Modifies the latest commit's message while preserving its changes.
    More efficient than filter-branch for editing the most recent commit.

    Args:
        commit_hash: Hash of commit to edit (for verification/display)
        new_message: New commit subject line
        new_body: Optional new commit body

    Returns:
        True if commit amended successfully, False on error

    Note:
        Uses --no-verify to bypass pre-commit hooks as the changes are
        already committed. Creates temporary file for commit message.
    """
    full_commit_message = new_message
    if new_body:
        full_commit_message += f"\n\n{new_body}"

    temp_file = None
    try:
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(full_commit_message)
                temp_file = f.name
        except (IOError, OSError, PermissionError) as e:
            print_error(f"Failed to create temporary commit message file: {str(e)}")
            return False

        success, _ = run_git_command(
            ["git", "commit", "--amend", "-F", temp_file, "--no-verify"],
            f"Failed to amend commit message for '{commit_hash[:7]}'",
            f"Commit message for '{commit_hash[:7]}' updated successfully",
        )

        if success:
            invalidate_repository_cache()

        return success
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception:
                pass


def edit_old_commit_with_filter_branch(
    commit_hash: str,
    new_message: str,
    new_body: Optional[str] = None,
    is_initial_commit: bool = False,
) -> bool:
    """Edit an old commit using git filter-branch.

    Rewrites git history to modify a commit that is not the latest one.
    This is more complex and time-consuming than amending.

    Args:
        commit_hash: Full hash of commit to edit
        new_message: New commit subject line
        new_body: Optional new commit body
        is_initial_commit: If True, use --all flag for initial commit

    Returns:
        True if commit edited successfully, False on error

    Note:
        REWRITES HISTORY - Changes all descendant commit hashes.
        Uses 300 second (5 minute) timeout for large repositories.
        Uses temporary files in ~/.ccg/ directory for secure message handling.
    """
    full_commit_message = new_message
    if new_body:
        full_commit_message += f"\n\n{new_body}"

    # Create CCG directory in user's home (same location as logs)
    ccg_dir = Path.home() / ".ccg"
    try:
        ccg_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to create CCG directory: {str(e)}")
        print_error(f"Failed to create directory {ccg_dir}: {str(e)}")
        return False

    message_file = None
    script_file = None
    try:
        # Create temporary file for commit message in ~/.ccg/
        try:
            message_file = ccg_dir / f"commit_message_{commit_hash[:7]}.tmp"
            message_file.write_text(full_commit_message, encoding="utf-8")
            logger.debug(f"Created message file: {message_file}")
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Failed to create message file: {str(e)}")
            print_error(f"Failed to create temporary message file: {str(e)}")
            return False

        # Create Python script that reads from message file
        # This avoids shell injection by not interpolating user content
        # Python is cross-platform and already a dependency of CCG
        import sys as _sys

        script_content = f"""#!/usr/bin/env python3
import subprocess
import sys

# Get current commit hash being processed by filter-branch
result = subprocess.run(
    ["git", "rev-parse", "--short", "HEAD"],
    capture_output=True,
    text=True
)
current_hash = result.stdout.strip()

# If this is the target commit, use new message from file
if current_hash == "{commit_hash[:7]}":
    with open(r"{message_file}", "r", encoding="utf-8") as f:
        sys.stdout.write(f.read())
else:
    # Otherwise, preserve original message from stdin
    sys.stdout.write(sys.stdin.read())
"""

        try:
            script_file = ccg_dir / f"msg_filter_{commit_hash[:7]}.py"
            script_file.write_text(script_content, encoding="utf-8")
            script_file.chmod(0o755)  # Make script executable
            logger.debug(f"Created Python script file: {script_file}")
        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Failed to create Python script file: {str(e)}")
            print_error(f"Failed to create temporary Python script file: {str(e)}")
            return False

        command = [
            "git",
            "filter-branch",
            "--force",
            "--msg-filter",
            str(script_file),
        ]

        if is_initial_commit:
            command.extend(["--", "--all"])
        else:
            command.append(f"{commit_hash}^..HEAD")

        print_process(f"Updating commit message for '{commit_hash[:7]}'...")
        print_info("This may take a moment for repositories with many commits...")

        with ProgressSpinner("Rewriting git history"):
            success, output = run_git_command(
                command,
                f"Failed to edit commit message for '{commit_hash[:7]}'",
                f"Commit message for '{commit_hash[:7]}' updated successfully",
                show_output=True,
                timeout=300,
            )

        if not success:
            print_error("Error details:")
            print(output)
            return False

        invalidate_repository_cache()
        return True

    finally:
        # Clean up temporary files
        for temp_file in [message_file, script_file]:
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {temp_file}: {str(e)}")


def edit_commit_message(commit_hash: str, new_message: str, new_body: Optional[str] = None) -> bool:
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

    commits = all_commits.strip().split("\n") if all_commits and all_commits.strip() else []
    rebase_script: List[str] = []
    found_target = False

    for commit in commits:
        if commit == commit_hash:
            found_target = True
            print_info(f"Removing commit {commit[:7]} from history")
            continue
        else:
            success, subject = run_git_command(
                ["git", "log", "-1", "--format=%s", commit],
                f"Failed to get subject for commit {commit[:7]}",
                show_output=True,
            )
            if success and subject:
                rebase_script.append(f"pick {commit[:7]} {subject.strip()}")

    if not found_target:
        print_error(f"Commit '{commit_hash[:7]}' not found in repository history")
        return False, None, []

    script_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("\n".join(rebase_script) + "\n")
            script_file = f.name
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
    """
    script_file = None
    try:
        success, script_file, rebase_script = create_rebase_script_for_deletion(commit_hash)
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
            env["GIT_SEQUENCE_EDITOR"] = f"cp {script_file}"
            env["GIT_EDITOR"] = "true"

            with ProgressSpinner("Deleting commit via rebase"):
                result = subprocess.run(
                    ["git", "rebase", "-i", "--root"],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

            if result.returncode == 0:
                print_success(f"Commit '{commit_hash[:7]}' deleted successfully")
                return True
            else:
                print_error(f"Failed to delete commit '{commit_hash[:7]}'")
                if result.stderr:
                    print(f"\033[91m{result.stderr}\033[0m")
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
        if script_file and os.path.exists(script_file):
            try:
                os.unlink(script_file)
            except Exception:
                pass

    return False  # pragma: no cover


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
            result = subprocess.run(
                ["pre-commit", "run", "--files"] + staged_files,
                capture_output=True,
                text=True,
                timeout=120,
            )

        if result.returncode != 0:
            print_error("Some pre-commit checks failed:")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"\033[91m{result.stderr}\033[0m")
            print_warning("Please fix the issues reported by pre-commit and run ccg again.")
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
        print_warning("Please ensure pre-commit is configured correctly and run ccg again.")
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
            subprocess.run(
                ["pre-commit", "--version"],
                capture_output=True,
                check=True,
                text=True,
                timeout=10,
            )
            pre_commit_installed = True
        except FileNotFoundError:
            pre_commit_installed = False
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pre_commit_installed = True

        if not pre_commit_installed:
            print_warning("pre-commit is configured but not installed.")
            print_info("Run 'pip install pre-commit' to install it.")
            print_info("After installing, run 'pre-commit install' to set up the hooks.")
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
