"""Git operations for the Conventional Commits Generator."""

import os
import subprocess
import tempfile
from typing import Any, List, Optional, Tuple, Union

from ..common.config import COLORS, DEFAULT_GIT_TIMEOUT, ERROR_MESSAGES, SUCCESS_MESSAGES
from ..ui.display import (
    print_error,
    print_info,
    print_process,
    print_section,
    print_success,
    print_warning,
)


def run_git_command(
    command: List[str],
    error_message: str,
    success_message: Optional[str] = None,
    show_output: bool = False,
    timeout: int = DEFAULT_GIT_TIMEOUT,
) -> Tuple[bool, Union[str, None]]:
    """
    Execute a git command within the CCG workflow context.

    Provides centralized git command execution with consistent error handling,
    timeout management, and output formatting for the conventional commits workflow.

    Args:
        command: Git command as list (e.g., ["git", "status", "--porcelain"])
        error_message: Message to display on command failure
        success_message: Optional message to display on success
        show_output: Whether to return command output
        timeout: Command timeout in seconds (default from config)

    Returns:
        Tuple of (success_boolean, output_string_or_None)

    Example:
        success, output = run_git_command(
            ["git", "commit", "-m", "feat: add feature"],
            "Failed to create commit",
            "Commit created successfully"
        )
    """
    try:
        result = subprocess.run(
            command, capture_output=True, check=True, text=True, timeout=timeout
        )

        if success_message:
            if success_message == SUCCESS_MESSAGES["CHANGES_PUSHED"]:
                print_section("Remote Push")
            print_success(success_message)

        if show_output:
            return True, result.stdout.strip()
        return True, None

    except subprocess.TimeoutExpired:
        error_msg = ERROR_MESSAGES["COMMAND_TIMEOUT"].format(
            timeout=timeout, command=" ".join(command)
        )
        print_error(error_msg)
        return False, error_msg
    except subprocess.CalledProcessError as error:
        if error_message:
            print_error(error_message)
        if show_output:
            error_text = error.stderr if error.stderr else error.stdout
            return False, error_text
        else:
            if error.stderr and error_message:
                print(f"{COLORS['RED']}{error.stderr}{COLORS['RESET']}")
            return False, None
    except FileNotFoundError:
        print_error(ERROR_MESSAGES["GIT_NOT_INSTALLED"])
        return False, None


def git_add(paths: Optional[List[str]] = None) -> bool:
    """
    Stage files for conventional commit workflow.

    Stages specified files or all changes for the conventional commit process.
    Provides feedback on what files are being staged and handles errors gracefully.

    Args:
        paths: Files/directories to stage. Defaults to ["."] for all changes.
               Can include specific files like ["src/main.py", "docs/"]

    Returns:
        True if all files staged successfully, False if any staging fails

    Example:
        git_add(["src/feature.py"])  # Stage specific file
        git_add()  # Stage all changes
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

    print_success(SUCCESS_MESSAGES["CHANGES_STAGED"])
    return True


def git_commit(commit_message: str) -> bool:
    """
    Create a git commit with a conventional commit message.

    Creates a commit using the provided conventional commit message,
    handling the commit creation process within the CCG workflow.

    Args:
        commit_message: Formatted conventional commit message
                       (e.g., "feat(auth): add OAuth support")

    Returns:
        True if commit created successfully, False otherwise

    Example:
        success = git_commit("fix(ui): resolve button alignment issue")
    """
    print_process("Committing changes...")
    success, _ = run_git_command(
        ["git", "commit", "-m", commit_message],
        "Error during 'git commit'",
        SUCCESS_MESSAGES["COMMIT_CREATED"],
    )
    return success


def handle_upstream_error(branch_name: str, remote_name: str, error_output: str) -> bool:
    """Handle upstream branch errors."""
    if "set the remote as upstream" in error_output or "no upstream branch" in error_output:
        print_warning("Upstream not set for this branch")
        print_info(f"Suggested command: git push --set-upstream {remote_name} {branch_name}")

        from ..ui.input import confirm_user_action

        return confirm_user_action(
            f"{COLORS['YELLOW']}Do you want to set upstream and push? [Y/n]{COLORS['RESET']}",
            success_message=None,
            cancel_message="Push cancelled. Changes remain local only.",
        )
    return False


def git_push(set_upstream: bool = False, force: bool = False) -> bool:
    """Push changes to remote repository."""
    branch_name = get_current_branch()
    if not branch_name:
        print_error("Failed to determine current branch name")
        return False

    # Special handling for detached HEAD
    if branch_name.startswith("HEAD-"):
        print_error("Cannot push from detached HEAD state.")
        print_info("Please create and checkout a branch first: git checkout -b <branch-name>")
        return False

    success, remote_output = run_git_command(
        ["git", "remote"], "Failed to get remote name", show_output=True
    )

    if not success or not remote_output:
        print_error("No remote repository configured")
        return False

    remote_name = remote_output.split()[0]

    if set_upstream:
        command = ["git", "push", "--set-upstream"]
        if force:
            command.append("--force")
        command.extend([remote_name, branch_name])

        success, _ = run_git_command(
            command,
            f"Error setting upstream and pushing to '{remote_name}/{branch_name}'",
            f"Branch '{branch_name}' created on remote and changes pushed successfully!",
        )
        return success
    elif force:
        message = f"Force pushing changes to '{remote_name}/{branch_name}'..."
        success_msg = f"Changes force pushed to '{remote_name}/{branch_name}' successfully!"

        print_process(message)
        success, _ = run_git_command(
            ["git", "push", "--force"], "Error during force push", success_msg
        )
        return success
    else:
        success, error_output = run_git_command(
            ["git", "push"],
            "Error during 'git push'",
            SUCCESS_MESSAGES["CHANGES_PUSHED"],
            show_output=True,
        )

        if not success and error_output:
            if handle_upstream_error(branch_name, remote_name, error_output):
                return git_push(set_upstream=True)
            return False

        return success


def create_tag(tag_name: str, message: Optional[str] = None) -> bool:
    """Create a git tag."""
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
    """Push a tag to remote repository."""
    print_process(f"Pushing tag '{tag_name}' to remote...")

    success, output = run_git_command(
        ["git", "remote"], "Failed to get remote name", show_output=True
    )

    if not success or not output:
        print_error("No remote repository configured")
        return False

    remote_name = output.split()[0]

    success, _ = run_git_command(
        ["git", "push", remote_name, tag_name],
        f"Error pushing tag '{tag_name}' to remote",
        f"Tag '{tag_name}' pushed to remote successfully",
    )

    return success


def discard_local_changes() -> bool:
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
    print_process("Pulling latest changes from remote...")

    success, output = run_git_command(
        ["git", "remote"], "Failed to get remote name", show_output=True
    )

    if not success or not output:
        print_error("No remote repository configured")
        return False

    remote_name = output.split()[0]
    branch_name = get_current_branch()
    if not branch_name:
        print_error("Failed to determine current branch name")
        return False

    success, _ = run_git_command(
        ["git", "pull", remote_name, branch_name],
        f"Error pulling from {remote_name}/{branch_name}",
        timeout=120,
    )

    return success


def fetch_and_pull_all() -> bool:
    """Fetch and pull all changes from remote repository."""
    print_section("Git Pull")

    # Get remote name safely
    success, remote_output = run_git_command(
        ["git", "remote"], "Failed to get remote repository name", show_output=True, timeout=30
    )
    if not success or not remote_output.strip():
        print_error("No remote repository configured")
        return False
    remote_name = remote_output.strip().split()[0]

    print_process(f"Fetching all changes from remote '{remote_name}'...")

    # First, try to fetch. If it fails due to tag conflicts, we'll handle it
    success, fetch_output = run_git_command(
        ["git", "fetch", "--all", "--tags", "--prune"],
        "Failed to fetch from remote",
        show_output=True,
        timeout=180,
    )

    if success and "would clobber existing tag" not in fetch_output:
        print_success(f"Successfully fetched all changes from '{remote_name}'")
    else:
        # Check if it's specifically a tag conflict issue
        if "would clobber existing tag" in fetch_output:
            print_warning("Tag conflicts detected. Resolving by removing local conflicting tags...")

            # Extract conflicting tag names from error output
            import re

            tag_conflicts = re.findall(
                r"! \[rejected\]\s+(\S+)\s+-> \S+\s+\(would clobber existing tag\)", fetch_output
            )

            if tag_conflicts:
                for tag in tag_conflicts:
                    print_process(f"Removing conflicting local tag '{tag}'...")
                    tag_success, _ = run_git_command(
                        ["git", "tag", "-d", tag],
                        f"Failed to remove tag '{tag}'",
                        f"Removed conflicting local tag '{tag}'",
                    )
                    if not tag_success:
                        print_warning(f"Could not remove tag '{tag}' (it may not exist locally)")

                    # Retry fetch after removing conflicting tags
                    print_process("Retrying fetch after resolving tag conflicts...")
                    retry_success, retry_output = run_git_command(
                        ["git", "fetch", "--all", "--tags", "--prune"],
                        "Still failed to fetch after resolving tag conflicts",
                        f"Successfully fetched all changes from '{remote_name}'",
                        show_output=True,
                        timeout=180,
                    )

                    if not retry_success:
                        return False
                else:
                    print_error("Could not identify specific conflicting tags")
                    return False
        else:
            print_error(f"Error fetching from remote '{remote_name}'")
            return False

    # Get current branch
    branch_name = get_current_branch()
    if not branch_name:
        print_error("Failed to determine current branch name")
        return False

    # Check if current branch exists on remote
    if not branch_exists_on_remote(branch_name):
        print_warning(f"Branch '{branch_name}' does not exist on remote '{remote_name}'")
        print_info("Fetch completed, but no pull was performed for local-only branch")
        return True

    # Pull current branch
    print_process(f"Pulling latest changes for branch '{branch_name}'...")
    success, _ = run_git_command(
        ["git", "pull", remote_name, branch_name],
        f"Error pulling branch '{branch_name}' from '{remote_name}'",
        f"Successfully pulled latest changes for branch '{branch_name}'",
        timeout=120,
    )

    return success


def get_staged_files() -> List[str]:
    success, output = run_git_command(
        ["git", "diff", "--name-only", "--cached"], "Failed to get staged files", show_output=True
    )

    if success and output:
        return [file for file in output.split("\n") if file]
    return []


def check_is_git_repo() -> bool:
    """
    Verify that current directory is within a git repository.

    Essential validation for CCG operations to ensure git commands
    will work properly. Used before attempting any git operations.

    Returns:
        True if inside a git repository, False otherwise

    Example:
        if not check_is_git_repo():
            print("Error: Not a git repository")
            return
    """
    success, _ = run_git_command(
        ["git", "rev-parse", "--is-inside-work-tree"], "Not a git repository", show_output=True
    )
    return success


def check_has_changes(paths: Optional[List[str]] = None) -> bool:
    """
    Check if there are uncommitted changes in the working directory.

    Verifies if there are changes available to commit, either in specific
    paths or across the entire repository. Essential for the CCG workflow
    to determine if a commit operation should proceed.

    Args:
        paths: Optional list of specific paths to check for changes.
               If None, checks entire working directory.

    Returns:
        True if changes are detected, False if working directory is clean

    Example:
        has_changes = check_has_changes(["src/", "docs/"])  # Check specific paths
        has_changes = check_has_changes()  # Check all changes
    """
    if not paths:
        print_process("Checking for changes in the working directory...")
        success, output = run_git_command(
            ["git", "status", "--porcelain"], "Failed to check for changes", show_output=True
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
    """
    Validate access to git remote repository for push operations.

    Checks if the user has proper authentication and network access
    to push commits to the remote repository. Critical for CCG push workflow
    to provide early feedback about connectivity issues.

    Returns:
        True if remote is accessible and user has push permissions,
        False if authentication fails or network issues exist

    Features:
        - Tests actual remote connectivity
        - Validates push permissions
        - Provides specific error messages for common issues
        - Handles various authentication methods (SSH, HTTPS, token)

    Example:
        if not check_remote_access():
            print("Cannot push to remote repository")
            return False
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
                    print()
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
    except Exception as e:
        print_error(f"Failed to check remote repository access: {str(e)}")
        return False


def get_current_branch() -> Optional[str]:
    # Try to get the actual branch name first
    success, output = run_git_command(
        ["git", "branch", "--show-current"],
        "Failed to get current branch name",
        show_output=True,
    )

    if success and output and output.strip():
        return output.strip()

    # Fallback to rev-parse method
    success, output = run_git_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        "Failed to get current branch name",
        show_output=True,
    )

    if success and output:
        branch_name = output.strip()
        # If we're in detached HEAD, we need to handle it differently for push
        if branch_name == "HEAD":
            # Get the commit hash for detached HEAD
            success, commit_hash = run_git_command(
                ["git", "rev-parse", "--short", "HEAD"],
                "Failed to get commit hash",
                show_output=True,
            )
            if success and commit_hash:
                return f"HEAD-{commit_hash.strip()}"
        return branch_name
    return None


def get_repository_name() -> Optional[str]:
    success, output = run_git_command(
        ["git", "rev-parse", "--show-toplevel"],
        "Failed to get repository root",
        show_output=True,
    )

    if success and output:
        import os

        return os.path.basename(output.strip())
    return None


def branch_exists_on_remote(branch_name: str) -> bool:
    success, output = run_git_command(
        ["git", "remote"], "Failed to get remote name", show_output=True
    )

    if not success or not output:
        return False

    remote_name = output.split()[0]

    success, output = run_git_command(
        ["git", "ls-remote", "--heads", remote_name, branch_name],
        f"Failed to check if branch '{branch_name}' exists on remote",
        show_output=True,
        timeout=30,
    )

    return success and bool(output)


def get_recent_commits(count: Optional[int] = None) -> List[Tuple[str, str, str, str, str]]:
    format_str = "%H|%h|%s|%an|%ar"
    command = ["git", "log", f"--pretty=format:{format_str}"]
    if count is not None and count > 0:
        command.append(f"-{count}")

    success, output = run_git_command(
        command, f"Failed to retrieve recent commits", show_output=True
    )

    if not success or not output:
        return []

    commits = []
    for line in output.split("\n"):
        if line:
            parts = line.split("|")
            if len(parts) >= 5:
                full_hash, short_hash, subject, author, date = parts
                commits.append((full_hash, short_hash, subject, author, date))

    return commits


def get_commit_by_hash(commit_hash: str) -> Optional[Tuple[str, str, str, str, str, str]]:
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
    full_commit_message = new_message
    if new_body:
        full_commit_message += f"\n\n{new_body}"

    try:
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(full_commit_message)
                temp_file = f.name
        except Exception as e:
            print_error(f"Failed to create temporary commit message file: {str(e)}")
            return False

        success, _ = run_git_command(
            ["git", "commit", "--amend", "-F", temp_file, "--no-verify"],
            f"Failed to amend commit message for '{commit_hash[:7]}'",
            f"Commit message for '{commit_hash[:7]}' updated successfully",
        )

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
    full_commit_message = new_message
    if new_body:
        full_commit_message += f"\n\n{new_body}"

    escaped_message = full_commit_message.replace("'", "'\\''")

    command = [
        "git",
        "filter-branch",
        "--force",
        "--msg-filter",
        f'if [ "$(git rev-parse --short $GIT_COMMIT)" = "{commit_hash[:7]}" ]; then echo \'{escaped_message}\'; else cat; fi',
    ]

    if is_initial_commit:
        command.extend(["--", "--all"])
    else:
        command.append(f"{commit_hash}^..HEAD")

    print_process(f"Updating commit message for '{commit_hash[:7]}'...")
    print_info("This may take a moment for repositories with many commits...")

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

    return True


def edit_commit_message(commit_hash: str, new_message: str, new_body: Optional[str] = None) -> bool:
    success, latest_commit = run_git_command(
        ["git", "rev-parse", "HEAD"], "Failed to get latest commit hash", show_output=True
    )

    if not success:
        return False

    is_latest = latest_commit == commit_hash

    if is_latest:
        return edit_latest_commit_with_amend(commit_hash, new_message, new_body)
    else:
        is_initial_commit = False
        success, output = run_git_command(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            "Failed to find initial commit",
            show_output=True,
        )

        if success and output and commit_hash in output:
            is_initial_commit = True
            print_info("Detected that you're editing the initial commit")

        return edit_old_commit_with_filter_branch(
            commit_hash, new_message, new_body, is_initial_commit
        )


def run_pre_commit_hooks(staged_files: List[str]) -> bool:
    try:
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
    except Exception as e:
        print_error(f"Unexpected error running pre-commit checks: {str(e)}")
        print_warning("Please fix the issues and run ccg again.")
        return False


def check_and_install_pre_commit() -> bool:
    try:
        if not os.path.exists(".pre-commit-config.yaml"):
            print_info("No pre-commit configuration found. Skipping pre-commit checks.")
            return True

        pre_commit_installed, _ = run_git_command(
            ["pre-commit", "--version"], "pre-commit command not found", show_output=True
        )

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

    except Exception as e:
        print_error(f"Unexpected error during pre-commit checks: {str(e)}")
        return False


def is_git_repository() -> bool:
    """Check if current directory is a git repository."""
    success, _ = run_git_command(
        ["git", "rev-parse", "--git-dir"],
        "Not a git repository",
        show_output=False,
    )
    return success


def get_git_root() -> Optional[str]:
    """Get the root directory of the git repository."""
    success, output = run_git_command(
        ["git", "rev-parse", "--show-toplevel"],
        "Failed to get git root",
        show_output=False,
    )
    return output.strip() if success and output else None


def show_working_directory_status() -> bool:
    """Show current working directory status with enhanced information and colors."""
    from ..ui.display import print_section

    # Get repository info
    branch_name = get_current_branch()
    if branch_name:
        if branch_name.startswith("HEAD-"):
            print_warning(f"Detached HEAD at {branch_name}")
        else:
            print_success(f"Current branch: {COLORS['BOLD']}{branch_name}{COLORS['RESET']}")

    # Check if branch exists on remote
    if branch_name and not branch_name.startswith("HEAD-"):
        if branch_exists_on_remote(branch_name):
            print_info(f"Branch exists on remote")
        else:
            print_warning(f"Branch not pushed to remote yet")

    print_process("Checking working directory changes...")

    success, output = run_git_command(
        ["git", "status", "--porcelain"],
        "Failed to get working directory status",
        show_output=True,
    )

    if not success:
        return False

    if not output:
        print_success("Working directory is clean - no changes")
        return True

    # Parse and categorize changes
    staged_files = []
    modified_files = []
    untracked_files = []
    deleted_files = []
    renamed_files = []

    lines = output.split("\n")
    for line in lines:
        if not line.strip():
            continue

        status = line[:2] if len(line) >= 2 else "  "
        filename = line[3:] if len(line) > 3 else ""

        if status[0] == "A" or status[1] == "A":
            staged_files.append((filename, "A"))
        elif status[0] == "M" or status[1] == "M":
            if status[0] == "M":
                staged_files.append((filename, "M"))
            else:
                modified_files.append(filename)
        elif status[0] == "D" or status[1] == "D":
            deleted_files.append(filename)
        elif status[0] == "R":
            renamed_files.append(filename)
        elif status == "??":
            untracked_files.append(filename)
        else:
            # Other changes (conflicts, etc.)
            modified_files.append(filename)

    # Display categorized changes with colors and icons
    total_changes = (
        len(staged_files)
        + len(modified_files)
        + len(untracked_files)
        + len(deleted_files)
        + len(renamed_files)
    )
    print()

    if staged_files:
        print(
            f"  {COLORS['GREEN']}{COLORS['BOLD']}Staged changes {COLORS['WHITE']}({len(staged_files)}):{COLORS['RESET']}"
        )
        for filename, change_type in staged_files:
            action = "modified" if change_type == "M" else "new file"
            print(f"    {COLORS['GREEN']} {filename} {COLORS['WHITE']}({action}){COLORS['RESET']}")
        print()

    if modified_files:
        print(
            f"  {COLORS['YELLOW']}{COLORS['BOLD']} Modified files {COLORS['WHITE']}({len(modified_files)}):{COLORS['RESET']}"
        )
        for filename in modified_files:
            print(f"    {COLORS['YELLOW']} {filename}{COLORS['RESET']}")
        print()

    if deleted_files:
        print(
            f"  {COLORS['RED']}{COLORS['BOLD']}Deleted files {COLORS['WHITE']}({len(deleted_files)}):{COLORS['RESET']}"
        )
        for filename in deleted_files:
            print(f"    {COLORS['RED']} {filename}{COLORS['RESET']}")
        print()

    if renamed_files:
        print(
            f"  {COLORS['BLUE']}{COLORS['BOLD']}Renamed files {COLORS['WHITE']}({len(renamed_files)}):{COLORS['RESET']}"
        )
        for filename in renamed_files:
            print(f"    {COLORS['BLUE']} {filename}{COLORS['RESET']}")
        print()

    if untracked_files:
        print(
            f"  {COLORS['MAGENTA']}{COLORS['BOLD']}Untracked files {COLORS['WHITE']}({len(untracked_files)}):{COLORS['RESET']}"
        )
        for filename in untracked_files:
            print(f"    {COLORS['MAGENTA']} {filename}{COLORS['RESET']}")
        print()

    return True


def show_diff_between_commits(commit1: str, commit2: str) -> bool:
    """Show diff between two commits."""
    print_process(f"Comparing commits {commit1[:7]} and {commit2[:7]}...")

    success, stat_output = run_git_command(
        ["git", "diff", "--stat", commit1, commit2],
        f"Failed to show diff statistics between {commit1[:7]} and {commit2[:7]}",
        show_output=True,
    )

    if not success:
        return False

    if stat_output:
        print(stat_output)

    print()
    print_process("Detailed diff:")

    success, diff_output = run_git_command(
        ["git", "diff", "--color=always", commit1, commit2],
        f"Failed to show detailed diff between {commit1[:7]} and {commit2[:7]}",
        show_output=True,
    )

    if success and diff_output:
        print(diff_output)

    return success


def show_enhanced_diff_between_commits(commit1: str, commit2: str) -> bool:
    """Show enhanced diff between two commits with interactive file selection."""
    from ..common.config import COLORS
    from ..ui.input import read_input

    # Get list of changed files with status and stats
    success, files_output = run_git_command(
        ["git", "diff", "--name-status", commit1, commit2],
        f"Failed to show changed files",
        show_output=True,
    )

    if not success or not files_output:
        return False

    # Get file statistics for insertions/deletions
    success, stat_output = run_git_command(
        ["git", "diff", "--numstat", commit1, commit2],
        f"Failed to show file statistics",
        show_output=True,
    )

    # Parse file stats
    file_stats = {}
    if success and stat_output:
        for line in stat_output.split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 3:
                    added, deleted, filename = parts[0], parts[1], parts[2]
                    file_stats[filename] = (added, deleted)

    def display_file_selection():
        # Parse changed files and create combined report
        changed_files = []
        print_process("Files Changed Report:")

        for i, line in enumerate(files_output.split("\n"), 1):
            if line.strip():
                status = line[0]

                # Handle different status formats
                if status == "R":  # Renamed file format: R<percentage>\told_file\tnew_file
                    # Find the first tab to separate status from filenames
                    tab_pos = line.find("\t")
                    if tab_pos != -1:
                        remaining = line[tab_pos + 1 :]
                        if "\t" in remaining:
                            old_file, new_file = remaining.split("\t", 1)
                            filename = f"{old_file} → {new_file}"
                        else:
                            filename = remaining
                    else:
                        filename = line[1:].strip()
                elif status == "C":  # Copied file format similar to renamed
                    tab_pos = line.find("\t")
                    if tab_pos != -1:
                        remaining = line[tab_pos + 1 :]
                        if "\t" in remaining:
                            old_file, new_file = remaining.split("\t", 1)
                            filename = f"{old_file} → {new_file}"
                        else:
                            filename = remaining
                    else:
                        filename = line[1:].strip()
                else:
                    # Regular file change format: <status>\t<filename>
                    tab_pos = line.find("\t")
                    if tab_pos != -1:
                        filename = line[tab_pos + 1 :]
                    else:
                        filename = line[1:].strip()

                changed_files.append((status, filename))

                # Add stats if available (for new filename if renamed)
                stats_info = ""
                # For renamed files, check stats with the new filename (after →)
                lookup_filename = filename
                if "→" in filename:
                    lookup_filename = filename.split("→")[1].strip()

                if lookup_filename in file_stats:
                    added, deleted = file_stats[lookup_filename]
                    if added != "-" and deleted != "-":
                        stats_info = f" (+{added}-{deleted})"

                print(f"   {i}. {filename}{stats_info}")

        print()
        options_text = f"1-{len(changed_files)} (specific file), 'q' (quit)"
        print_info(f"Select: {options_text}")
        return changed_files

    files_viewed = 0

    while True:
        changed_files = display_file_selection()
        options_text = f"1-{len(changed_files)} (specific file), 'q' (quit)"

        choice = read_input(
            f"{COLORS['YELLOW']}Select option{COLORS['RESET']}",
            max_length=10,
        )

        if choice.lower() in ("q", "quit", "exit"):
            print_info("Diff viewing completed")
            print("\nExiting. Goodbye!")
            return True

        if choice.isdigit() and 1 <= int(choice) <= len(changed_files):
            file_idx = int(choice) - 1
            status, filename = changed_files[file_idx]

            print_process(f"Showing changes in: {filename}")

            # For renamed/copied files, we need to handle them differently
            if status in ["R", "C"] and "→" in filename:
                # For renamed files, extract the new filename
                new_filename = filename.split("→")[1].strip()
                success, file_diff = run_git_command(
                    ["git", "diff", "--color=always", commit1, commit2, "--", new_filename],
                    f"Failed to show diff for {filename}",
                    show_output=True,
                )
            else:
                # Regular file change
                success, file_diff = run_git_command(
                    ["git", "diff", "--color=always", commit1, commit2, "--", filename],
                    f"Failed to show diff for {filename}",
                    show_output=True,
                )

            if success and file_diff:
                print(file_diff)
            elif success:
                print_info("No changes to display for this file")

            print()
            files_viewed += 1

            # After viewing any file, ask if user wants to continue
            from ..ui.input import confirm_user_action

            continue_viewing = confirm_user_action(
                f"{COLORS['YELLOW']}Do you want to continue viewing more files? [Y/n]{COLORS['RESET']}",
                success_message=None,
                cancel_message="File viewing completed",
            )
            if not continue_viewing:
                return True

            continue

        print_error(f"Invalid choice. Please enter: {options_text}")

    return True


def show_diff_commit_vs_working(commit_hash: str) -> bool:
    """Show diff between a commit and working directory."""
    print_process(f"Comparing commit {commit_hash[:7]} with working directory...")

    success, stat_output = run_git_command(
        ["git", "diff", "--stat", commit_hash],
        f"Failed to show diff statistics between {commit_hash[:7]} and working directory",
        show_output=True,
    )

    if not success:
        return False

    if stat_output:
        print(stat_output)

    print()
    print_process("Detailed diff:")

    success, diff_output = run_git_command(
        ["git", "diff", "--color=always", commit_hash],
        f"Failed to show detailed diff between {commit_hash[:7]} and working directory",
        show_output=True,
    )

    if success and diff_output:
        print(diff_output)

    return success


def show_local_changes_interactive() -> bool:
    """Show local changes with interactive file selection."""
    from ..common.config import COLORS
    from ..ui.input import read_input

    # Get list of changed files with status and stats
    success, files_output = run_git_command(
        ["git", "status", "--porcelain"],
        f"Failed to show local changes",
        show_output=True,
    )

    if not success or not files_output:
        print_info("No local changes found")
        return True

    # Get file statistics for insertions/deletions
    success, stat_output = run_git_command(
        ["git", "diff", "--numstat", "HEAD"],
        f"Failed to show file statistics",
        show_output=True,
    )

    # Parse file stats
    file_stats = {}
    if success and stat_output:
        for line in stat_output.split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 3:
                    added, deleted, filename = parts[0], parts[1], parts[2]
                    file_stats[filename] = (added, deleted)

    def display_local_file_selection():
        # Parse changed files and create report
        changed_files = []
        print_process("Local Changes Report:")

        for i, line in enumerate(files_output.split("\n"), 1):
            if line.strip():
                status = line[0] if len(line) > 0 else " "
                status2 = line[1] if len(line) > 1 else " "
                filename = line[2:].strip()
                changed_files.append((status, status2, filename))

                # Map git status codes to readable format
                if status == "M" or status2 == "M":
                    status_icon = "Modified"
                elif status == "A":
                    status_icon = "Added (staged)"
                elif status2 == "A":
                    status_icon = "Added"
                elif status == "D":
                    status_icon = "Deleted (staged)"
                elif status2 == "D":
                    status_icon = "Deleted"
                elif status == "?":
                    status_icon = "Untracked"
                else:
                    status_icon = f"{status}{status2}"

                # Add stats if available
                stats_info = ""
                if filename in file_stats:
                    added, deleted = file_stats[filename]
                    if added != "-" and deleted != "-":
                        stats_info = f" (+{added}/-{deleted})"

                print(f"   {i}. {status_icon}: {filename}{stats_info}")

        print()
        options_text = f"1-{len(changed_files)} (specific file), 'q' (quit)"
        print_info(f"Select: {options_text}")
        return changed_files

    files_viewed = 0

    while True:
        changed_files = display_local_file_selection()
        options_text = f"1-{len(changed_files)} (specific file), 'q' (quit)"

        choice = read_input(
            f"{COLORS['YELLOW']}Select option{COLORS['RESET']}",
            max_length=10,
        )

        if choice.lower() in ("q", "quit", "exit"):
            print_info("Local changes viewing completed")
            return True

        if choice.isdigit() and 1 <= int(choice) <= len(changed_files):
            file_idx = int(choice) - 1
            status, status2, filename = changed_files[file_idx]

            print_process(f"Showing local changes in: {filename}")

            # Show diff for the specific file
            success, file_diff = run_git_command(
                ["git", "diff", "--color=always", "HEAD", "--", filename],
                f"Failed to show diff for {filename}",
                show_output=True,
            )

            if success and file_diff:
                print(file_diff)
            elif success:
                print_info("No changes to display for this file")

            print()
            files_viewed += 1

            # After viewing any file, ask if user wants to continue
            from ..ui.input import confirm_user_action

            continue_viewing = confirm_user_action(
                f"{COLORS['YELLOW']}Do you want to continue viewing more files? [Y/n]{COLORS['RESET']}",
                success_message=None,
                cancel_message="File viewing completed",
            )
            if not continue_viewing:
                return True

            continue

        print_error(f"Invalid choice. Please enter: {options_text}")

    return True


def show_commit_diff(commit_hash: str) -> bool:
    """Show what changed in a specific commit."""
    print_process(f"Showing changes introduced by commit {commit_hash[:7]}...")

    success, stat_output = run_git_command(
        ["git", "show", "--stat", commit_hash],
        f"Failed to show commit statistics for {commit_hash[:7]}",
        show_output=True,
    )

    if not success:
        return False

    if stat_output:
        print(stat_output)

    print()
    print_process("Detailed changes:")

    success, diff_output = run_git_command(
        ["git", "show", "--color=always", commit_hash],
        f"Failed to show detailed changes for {commit_hash[:7]}",
        show_output=True,
    )

    if success and diff_output:
        print(diff_output)

    return success
