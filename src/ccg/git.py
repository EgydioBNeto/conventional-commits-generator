"""Git operations for the Conventional Commits Generator."""

import subprocess
from typing import List, Optional, Tuple, Any, Dict

from ccg.utils import print_error, print_process, print_success, print_info, print_warning, print_section


def run_git_command(command: List[str], error_message: str, success_message: Optional[str] = None,
                   show_output: bool = False) -> Tuple[bool, Any]:
    """Run a git command and handle errors consistently.

    Args:
        command: The git command to run as a list of strings
        error_message: Message to display on error
        success_message: Message to display on success (optional)
        show_output: Whether to return the command output

    Returns:
        Tuple[bool, Any]: Success status and command output if show_output is True
                         or error output if failure and show_output is True
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True
        )

        if success_message:
            if success_message == "Changes pushed successfully!":
                print_section("Remote Push")
            print_success(success_message)

        if show_output:
            return True, result.stdout.strip()
        return True, None

    except subprocess.CalledProcessError as error:
        print_error(error_message)
        # When text=True is used, stderr is already a string, no need to decode
        if show_output:
            # Return the error output (stderr preferably, stdout as fallback)
            error_text = error.stderr if error.stderr else error.stdout
            return False, error_text
        else:
            if error.stderr:
                print(f"\033[91m{error.stderr}\033[0m")
            return False, None

    except FileNotFoundError:
        print_error("Git is not installed. Please install Git and try again.")
        return False, None


def git_add() -> bool:
    """Run 'git add' to stage changes.

    Returns:
        bool: True if successful, False otherwise
    """
    print_process("Staging changes with git...")
    success, _ = run_git_command(
        ["git", "add", "."],
        "Error during 'git add'",
        "Changes staged successfully"
    )
    return success


def git_commit(commit_message: str) -> bool:
    """Run 'git commit' with the provided message.

    Args:
        commit_message: The commit message to use

    Returns:
        bool: True if successful, False otherwise
    """
    print_process("Committing changes...")
    success, _ = run_git_command(
        ["git", "commit", "-m", commit_message],
        "Error during 'git commit'",
        "New commit successfully created!"
    )
    return success


def git_push(set_upstream: bool = False, force: bool = False) -> bool:
    """Run 'git push' to push changes.

    Args:
        set_upstream: Whether to set the upstream branch
        force: Whether to force push changes

    Returns:
        bool: True if successful, False otherwise
    """

    if set_upstream:
        # Get current branch name
        branch_name = get_current_branch()
        if not branch_name:
            print_error("Failed to determine current branch name")
            return False

        # Get remote name (usually origin)
        success, remote_output = run_git_command(
            ["git", "remote"],
            "Failed to get remote name",
            show_output=True
        )

        if not success or not remote_output:
            print_error("No remote repository configured")
            return False

        remote_name = remote_output.split()[0]  # Get first remote

        # Push with --set-upstream (and force if requested)
        command = ["git", "push", "--set-upstream"]
        if force:
            command.append("--force")
        command.extend([remote_name, branch_name])

        success, _ = run_git_command(
            command,
            f"Error setting upstream and pushing to '{remote_name}/{branch_name}'",
            f"Branch '{branch_name}' created on remote and changes pushed successfully!"
        )
        return success
    elif force:
        # Get remote name and branch for better error message
        branch_name = get_current_branch()
        success, remote_output = run_git_command(
            ["git", "remote"],
            "Failed to get remote name",
            show_output=True
        )

        if success and remote_output and branch_name:
            remote_name = remote_output.split()[0]  # Get first remote
            message = f"Force pushing changes to '{remote_name}/{branch_name}'..."
            success_msg = f"Changes force pushed to '{remote_name}/{branch_name}' successfully!"
        else:
            message = "Force pushing changes to remote..."
            success_msg = "Changes force pushed successfully!"

        # Force push
        print_process(message)
        success, _ = run_git_command(
            ["git", "push", "--force"],
            "Error during force push",
            success_msg
        )
        return success
    else:
        # Regular push
        branch_name = get_current_branch()
        if not branch_name:
            print_error("Failed to determine current branch name")
            return False

        # Get remote name (usually origin)
        success, remote_output = run_git_command(
            ["git", "remote"],
            "Failed to get remote name",
            show_output=True
        )

        if not success or not remote_output:
            print_error("No remote repository configured")
            return False

        remote_name = remote_output.split()[0]  # Get first remote

        # Try regular push first
        success, error_output = run_git_command(
            ["git", "push"],
            "Error during 'git push'",
            "Changes pushed successfully!",
            show_output=True
        )

        # If push failed, check if it's due to upstream not being set
        if not success and error_output:
            if "set the remote as upstream" in error_output or "no upstream branch" in error_output:
                print_warning("Upstream not set for this branch")
                print_info(f"Suggested command: git push --set-upstream {remote_name} {branch_name}")

                # Ask if user wants to set upstream
                while True:
                    from ccg.utils import read_input, YELLOW, RESET
                    confirm = read_input(
                        f"{YELLOW}Do you want to set upstream and push? (y/n){RESET}"
                    ).lower()

                    if not confirm:
                        print_warning("Please enter 'y' or 'n'")
                        continue

                    if confirm in ("y", "yes"):
                        return git_push(set_upstream=True)
                    elif confirm in ("n", "no"):
                        print_info("Push cancelled. Changes remain local only.")
                        return False

                    print_error("Invalid choice. Please enter 'y' or 'n'.")

        print()
        return success


def create_tag(tag_name: str, message: Optional[str] = None) -> bool:
    """Create a new Git tag.

    Args:
        tag_name: The name of the tag to create
        message: Optional message for annotated tag

    Returns:
        bool: True if successful, False otherwise
    """
    print_process(f"Creating tag '{tag_name}'...")

    if message:
        # Create an annotated tag with a message
        success, _ = run_git_command(
            ["git", "tag", "-a", tag_name, "-m", message],
            f"Error creating tag '{tag_name}'",
            f"Tag '{tag_name}' created successfully"
        )
    else:
        # Create a lightweight tag
        success, _ = run_git_command(
            ["git", "tag", tag_name],
            f"Error creating tag '{tag_name}'",
            f"Tag '{tag_name}' created successfully"
        )

    return success


def push_tag(tag_name: str) -> bool:
    """Push a Git tag to the remote.

    Args:
        tag_name: The name of the tag to push

    Returns:
        bool: True if successful, False otherwise
    """
    print_process(f"Pushing tag '{tag_name}' to remote...")

    # Get the remote name (usually origin)
    success, output = run_git_command(
        ["git", "remote"],
        "Failed to get remote name",
        show_output=True
    )

    if not success or not output:
        print_error("No remote repository configured")
        return False

    remote_name = output.split()[0]  # Get first remote

    # Push the tag
    success, _ = run_git_command(
        ["git", "push", remote_name, tag_name],
        f"Error pushing tag '{tag_name}' to remote",
        f"Tag '{tag_name}' pushed to remote successfully"
    )

    return success


def discard_local_changes() -> bool:
    """Discard all local changes.

    Returns:
        bool: True if successful, False otherwise
    """
    print_process("Discarding all local changes...")

    # Reset any staged changes
    success, _ = run_git_command(
        ["git", "reset", "HEAD"],
        "Error while unstaging changes",
        "Unstaged all changes successfully"
    )

    if not success:
        return False

    # Discard all local changes
    success, _ = run_git_command(
        ["git", "checkout", "."],
        "Error while discarding local changes",
        "Discarded all tracked file changes"
    )

    if not success:
        return False

    # Clean untracked files
    success, _ = run_git_command(
        ["git", "clean", "-fd"],
        "Error while removing untracked files",
        "Removed all untracked files and directories"
    )

    return success


def pull_from_remote() -> bool:
    """Pull latest changes from remote repository.

    Returns:
        bool: True if successful, False otherwise
    """
    print_process("Pulling latest changes from remote...")

    # Get the remote name (usually origin)
    success, output = run_git_command(
        ["git", "remote"],
        "Failed to get remote name",
        show_output=True
    )

    if not success or not output:
        print_error("No remote repository configured")
        return False

    remote_name = output.split()[0]  # Get first remote

    # Get current branch
    branch_name = get_current_branch()
    if not branch_name:
        print_error("Failed to determine current branch name")
        return False

    # Pull latest changes
    success, _ = run_git_command(
        ["git", "pull", remote_name, branch_name],
        f"Error pulling from {remote_name}/{branch_name}",
        f"Successfully pulled latest changes from {remote_name}/{branch_name}"
    )

    return success


def get_staged_files() -> List[str]:
    """Get the list of staged files.

    Returns:
        List[str]: The list of staged files
    """
    success, output = run_git_command(
        ["git", "diff", "--name-only", "--cached"],
        "Failed to get staged files",
        show_output=True
    )

    if success and output:
        return [file for file in output.split("\n") if file]
    return []


def check_is_git_repo() -> bool:
    """Check if the current directory is a git repository.

    Returns:
        bool: True if it's a git repository, False otherwise
    """
    success, _ = run_git_command(
        ["git", "rev-parse", "--is-inside-work-tree"],
        "Not a git repository",
        show_output=True
    )
    return success


def check_has_changes() -> bool:
    """Check if there are changes to commit.

    Returns:
        bool: True if there are changes, False otherwise
    """
    print_process("Checking for changes...")

    # First check unstaged changes
    success, output = run_git_command(
        ["git", "status", "--porcelain"],
        "Failed to check for changes",
        show_output=True
    )

    if success:
        if not output:
            print_info("No changes detected in the working directory.")
            return False
        return True

    return False


def check_remote_access() -> bool:
    """Check if there's access to the remote repository.

    Returns:
        bool: True if remote is accessible, False otherwise
    """
    print_process("Checking remote repository access...")

    # First check if remote is configured
    success, output = run_git_command(
        ["git", "remote", "-v"],
        "Failed to check remote repositories",
        show_output=True
    )

    if not success or not output:
        print_info("No remote repository configured.")
        return False

    # Get the name of the first remote (usually 'origin')
    remote_name = output.split()[0] if output else "origin"

    # Check if we have access to the remote
    success, _ = run_git_command(
        ["git", "ls-remote", "--exit-code", remote_name],
        f"Cannot access remote repository '{remote_name}'",
        f"Remote repository '{remote_name}' is accessible",
        show_output=True
    )

    return success


def get_current_branch() -> Optional[str]:
    """Get the name of the current branch.

    Returns:
        Optional[str]: Name of the current branch, or None if not found
    """
    success, output = run_git_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        "Failed to get current branch name",
        show_output=True
    )

    if success and output:
        return output
    return None


def branch_exists_on_remote(branch_name: str) -> bool:
    """Check if a branch exists on the remote repository.

    Args:
        branch_name: The name of the branch to check

    Returns:
        bool: True if the branch exists on the remote, False otherwise
    """
    # Get the remote name (usually origin)
    success, output = run_git_command(
        ["git", "remote"],
        "Failed to get remote name",
        show_output=True
    )

    if not success or not output:
        return False

    remote_name = output.split()[0]  # Get first remote

    # Check if branch exists on remote
    success, output = run_git_command(
        ["git", "ls-remote", "--heads", remote_name, branch_name],
        f"Failed to check if branch '{branch_name}' exists on remote",
        show_output=True
    )

    # If command succeeded and there is output, the branch exists
    return success and bool(output)


def get_recent_commits(count: int = 5) -> List[Tuple[str, str, str, str, str]]:
    """Get a list of recent commits.

    Args:
        count: Number of commits to retrieve

    Returns:
        List[Tuple[str, str, str, str, str]]: List of (full_hash, short_hash, subject, author, date) tuples
    """
    # Format: hash, subject, author, date
    format_str = "%H|%h|%s|%an|%ar"

    success, output = run_git_command(
        ["git", "log", f"-{count}", f"--pretty=format:{format_str}"],
        f"Failed to retrieve recent commits",
        show_output=True
    )

    if not success or not output:
        return []

    commits = []
    for line in output.split("\n"):
        if line:
            parts = line.split("|")
            if len(parts) >= 5:
                # Return full hash, short hash, subject, author, date
                full_hash = parts[0]
                short_hash = parts[1]
                subject = parts[2]
                author = parts[3]
                date = parts[4]
                commits.append((full_hash, short_hash, subject, author, date))

    return commits


def get_commit_by_hash(commit_hash: str) -> Optional[Tuple[str, str, str, str, str, str]]:
    """Get details of a specific commit by its hash.

    Args:
        commit_hash: Hash of the commit to retrieve

    Returns:
        Optional[Tuple[str, str, str, str, str, str]]:
            (full_hash, short_hash, subject, body, author, date) or None if not found
    """
    # Check if the commit exists
    success, _ = run_git_command(
        ["git", "rev-parse", "--verify", commit_hash],
        f"Commit '{commit_hash}' not found",
        show_output=True
    )

    if not success:
        return None

    # Get the full hash
    success, full_hash = run_git_command(
        ["git", "rev-parse", commit_hash],
        f"Failed to get full hash for '{commit_hash}'",
        show_output=True
    )

    if not success or not full_hash:
        return None

    # Get the short hash
    success, short_hash = run_git_command(
        ["git", "rev-parse", "--short", commit_hash],
        f"Failed to get short hash for '{commit_hash}'",
        show_output=True
    )

    if not success or not short_hash:
        short_hash = commit_hash[:7]  # Fallback to first 7 characters

    # Get commit details
    success, commit_message = run_git_command(
        ["git", "log", "-1", "--pretty=%B", commit_hash],
        f"Failed to get commit message for '{commit_hash}'",
        show_output=True
    )

    if not success or not commit_message:
        return None

    # Split into subject and body
    message_parts = commit_message.strip().split("\n\n", 1)
    subject = message_parts[0].strip()
    body = message_parts[1].strip() if len(message_parts) > 1 else ""

    # Get author and date
    success, author = run_git_command(
        ["git", "log", "-1", "--pretty=%an", commit_hash],
        f"Failed to get author for '{commit_hash}'",
        show_output=True
    )

    if not success or not author:
        author = "Unknown"

    success, date = run_git_command(
        ["git", "log", "-1", "--pretty=%ar", commit_hash],
        f"Failed to get date for '{commit_hash}'",
        show_output=True
    )

    if not success or not date:
        date = "Unknown date"

    return (full_hash, short_hash, subject, body, author, date)


def edit_commit_message(commit_hash: str, new_message: str) -> bool:
    """Edit the message of a specific commit.

    Args:
        commit_hash: Hash of the commit to edit
        new_message: New commit message

    Returns:
        bool: True if successful, False otherwise
    """
    # Check if this is the most recent commit
    success, latest_commit = run_git_command(
        ["git", "rev-parse", "HEAD"],
        "Failed to get latest commit hash",
        show_output=True
    )

    if not success:
        return False

    is_latest = latest_commit == commit_hash

    if is_latest:
        # For the most recent commit, we can use --amend
        try:
            # Write the new message to a temporary file
            with open(".git/COMMIT_EDITMSG", "w") as f:
                f.write(new_message)
        except Exception as e:
            print_error(f"Failed to create temporary commit message file: {str(e)}")
            return False

        # Amend the commit message
        success, _ = run_git_command(
            ["git", "commit", "--amend", "-F", ".git/COMMIT_EDITMSG", "--no-verify"],
            f"Failed to amend commit message for '{commit_hash[:7]}'",
            f"Commit message for '{commit_hash[:7]}' updated successfully"
        )

        return success
    else:
        # For older commits, we use filter-branch which is more reliable for editing old commits
        # First, check if this is the initial commit
        is_initial_commit = False
        success, output = run_git_command(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            "Failed to find initial commit",
            show_output=True
        )

        if success and output and commit_hash in output:
            is_initial_commit = True
            print_info("Detected that you're editing the initial commit")

        # Escape single quotes in the message to prevent issues with the shell command
        escaped_message = new_message.replace("'", "'\\''")

        # Create the filter-branch command
        command = [
            "git",
            "filter-branch",
            "--force",
            "--msg-filter",
            f"if [ \"$(git rev-parse --short $GIT_COMMIT)\" = \"{commit_hash[:7]}\" ]; then echo '{escaped_message}'; else cat; fi"
        ]

        if is_initial_commit:
            command.append("--")
            command.append("--all")
        else:
            command.append(f"{commit_hash}^..HEAD")

        print_process(f"Updating commit message for '{commit_hash[:7]}'...")
        print_info("This may take a moment for repositories with many commits...")

        success, output = run_git_command(
            command,
            f"Failed to edit commit message for '{commit_hash[:7]}'",
            f"Commit message for '{commit_hash[:7]}' updated successfully",
            show_output=True
        )

        if not success:
            print_error("Error details:")
            print(output)
            return False

        return True


def check_and_install_pre_commit() -> bool:
    """Check for pre-commit config and install hooks if needed.

    Returns:
        bool: True if pre-commit checks pass or are not needed, False otherwise
    """
    try:
        # First check if .pre-commit-config.yaml exists
        try:
            with open(".pre-commit-config.yaml", "r"):
                pass
        except FileNotFoundError:
            # No pre-commit config found, that's okay
            print_info("No pre-commit configuration found. Skipping pre-commit checks.")
            return True

        # Check if pre-commit is installed
        pre_commit_installed, _ = run_git_command(
            ["pre-commit", "--version"],
            "pre-commit command not found",
            show_output=True
        )

        if not pre_commit_installed:
            print_warning("pre-commit is configured but not installed.")
            print_info("Run 'pip install pre-commit' to install it.")
            print_info("After installing, run 'pre-commit install' to set up the hooks.")
            return False

        # Install pre-commit hooks
        print_process("Setting up pre-commit hooks...")
        hooks_installed, _ = run_git_command(
            ["pre-commit", "install"],
            "Failed to install pre-commit hooks",
            "Pre-commit hooks installed successfully"
        )

        if not hooks_installed:
            return False

        # Run pre-commit against staged files
        print_process("Running pre-commit checks on staged files...")
        staged_files = get_staged_files()

        # Only run pre-commit if there are staged files
        if staged_files:
            # For pre-commit, we'll run it directly to capture the full output
            try:
                result = subprocess.run(
                    ["pre-commit", "run", "--files"] + staged_files,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print_error("Some pre-commit checks failed:")
                    # Print the complete output to help with debugging
                    if result.stdout:
                        print(result.stdout)
                    if result.stderr:
                        print(f"\033[91m{result.stderr}\033[0m")
                    return False

                print_success("All pre-commit checks passed successfully")
            except subprocess.CalledProcessError as e:
                print_error("Error running pre-commit:")
                if e.stdout:
                    print(e.stdout)
                if e.stderr:
                    print(f"\033[91m{e.stderr}\033[0m")
                return False
            except Exception as e:
                print_error(f"Unexpected error running pre-commit: {str(e)}")
                return False

        return True

    except Exception as e:
        print_error(f"Unexpected error during pre-commit checks: {str(e)}")
        return False
