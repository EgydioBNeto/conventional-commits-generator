"""Git operations for the Conventional Commits Generator."""

import os
import subprocess
import tempfile
from typing import Any, List, Optional, Tuple

from ccg.utils import (
    print_error,
    print_info,
    print_process,
    print_section,
    print_success,
    print_warning,
)

DEFAULT_GIT_TIMEOUT = 60


def run_git_command(
    command: List[str],
    error_message: str,
    success_message: Optional[str] = None,
    show_output: bool = False,
    timeout: int = DEFAULT_GIT_TIMEOUT,
) -> Tuple[bool, Any]:
    try:
        result = subprocess.run(
            command, capture_output=True, check=True, text=True, timeout=timeout
        )

        if success_message:
            if success_message == "Changes pushed successfully!":
                print_section("Remote Push")
            print_success(success_message)

        if show_output:
            return True, result.stdout.strip()
        return True, None

    except subprocess.TimeoutExpired:
        print_error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        return False, f"Command timed out after {timeout} seconds"
    except subprocess.CalledProcessError as error:
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
        print_error("Git is not installed. Please install Git and try again.")
        return False, None


def git_add(paths: Optional[List[str]] = None) -> bool:
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
    print_process("Committing changes...")
    success, _ = run_git_command(
        ["git", "commit", "-m", commit_message],
        "Error during 'git commit'",
        "New commit successfully created!",
    )
    return success


def handle_upstream_error(branch_name: str, remote_name: str, error_output: str) -> bool:
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
    branch_name = get_current_branch()
    if not branch_name:
        print_error("Failed to determine current branch name")
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
        print_process("Pushing changes...")
        success, error_output = run_git_command(
            ["git", "push"],
            "Error during 'git push'",
            "Changes pushed successfully!",
            show_output=True,
        )

        if not success and error_output:
            if handle_upstream_error(branch_name, remote_name, error_output):
                return git_push(set_upstream=True)
            return False

        return success


def create_tag(tag_name: str, message: Optional[str] = None) -> bool:
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


def get_staged_files() -> List[str]:
    success, output = run_git_command(
        ["git", "diff", "--name-only", "--cached"], "Failed to get staged files", show_output=True
    )

    if success and output:
        return [file for file in output.split("\n") if file]
    return []


def check_is_git_repo() -> bool:
    success, _ = run_git_command(
        ["git", "rev-parse", "--is-inside-work-tree"], "Not a git repository", show_output=True
    )
    return success


def check_has_changes(paths: Optional[List[str]] = None) -> bool:
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
    success, output = run_git_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        "Failed to get current branch name",
        show_output=True,
    )

    if success and output:
        return output
    return None


def get_repository_name() -> Optional[str]:
    """Get the name of the current git repository.

    Returns:
        Repository name or None if unable to determine
    """
    success, output = run_git_command(
        ["git", "rev-parse", "--show-toplevel"],
        "Failed to get repository root",
        show_output=True,
    )

    if success and output:
        return os.path.basename(output)
    return None


def get_repository_root() -> Optional[str]:
    """Get the root directory of the current git repository.

    Returns:
        Absolute path to repository root or None if unable to determine
    """
    success, output = run_git_command(
        ["git", "rev-parse", "--show-toplevel"],
        "Failed to get repository root",
        show_output=True,
    )

    if success and output:
        return output
    return None


def is_path_in_repository(path: str, repo_root: str) -> bool:
    """Check if a path is within the git repository.

    Args:
        path: Path to check
        repo_root: Root directory of the git repository

    Returns:
        True if path is within repository, False otherwise
    """
    abs_path = os.path.abspath(path)
    abs_repo_root = os.path.abspath(repo_root)

    try:
        # Check if path is relative to repo_root
        os.path.relpath(abs_path, abs_repo_root)
        # Check if the path actually starts with repo_root
        return abs_path.startswith(abs_repo_root)
    except ValueError:
        # On Windows, relpath raises ValueError if paths are on different drives
        return False


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


def delete_latest_commit() -> bool:
    print_process("Deleting latest commit...")
    success, _ = run_git_command(
        ["git", "reset", "--hard", "HEAD~1"],
        "Failed to delete latest commit",
        "Latest commit deleted successfully",
    )
    return success


def create_rebase_script_for_deletion(commit_hash: str) -> Tuple[bool, Optional[str], List[str]]:
    success, all_commits = run_git_command(
        ["git", "rev-list", "--reverse", "HEAD"], "Failed to get commit history", show_output=True
    )

    if not success:
        return False, None, []

    commits = all_commits.strip().split("\n") if all_commits.strip() else []
    rebase_script = []
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
    except Exception as e:
        print_error(f"Failed to create temporary rebase script: {str(e)}")
        return False, None, []

    return True, script_file, rebase_script


def delete_old_commit_with_rebase(commit_hash: str) -> bool:
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
        except Exception as e:
            print_error(f"Error during rebase: {str(e)}")
            run_git_command(["git", "rebase", "--abort"], "", "")
            return False
    finally:
        if script_file and os.path.exists(script_file):
            try:
                os.unlink(script_file)
            except Exception:
                pass

    return False


def delete_commit(commit_hash: str) -> bool:
    success, _ = run_git_command(
        ["git", "cat-file", "-e", commit_hash],
        f"Commit '{commit_hash}' not found or not accessible",
        show_output=True,
    )

    if not success:
        return False

    success, latest_commit = run_git_command(
        ["git", "rev-parse", "HEAD"], "Failed to get latest commit hash", show_output=True
    )

    if not success:
        return False

    is_latest = latest_commit.strip() == commit_hash

    if is_latest:
        return delete_latest_commit()
    else:
        return delete_old_commit_with_rebase(commit_hash)


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
