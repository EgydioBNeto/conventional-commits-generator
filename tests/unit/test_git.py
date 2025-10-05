"""Unit tests for git.py module."""

import subprocess
from unittest.mock import Mock, patch

from ccg.git import check_has_changes, check_is_git_repo, git_add, git_commit, run_git_command


class TestRunGitCommand:
    """Tests for run_git_command function."""

    @patch("subprocess.run")
    def test_successful_command(self, mock_run: Mock) -> None:
        """Should execute command successfully."""
        mock_run.return_value = Mock(returncode=0, stdout="success output", stderr="")

        success, output = run_git_command(["git", "status"], "Error message", show_output=True)

        assert success is True
        assert output == "success output"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_successful_command_no_output(self, mock_run: Mock) -> None:
        """Should execute command without returning output."""
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")

        success, output = run_git_command(["git", "status"], "Error message", show_output=False)

        assert success is True
        assert output is None

    @patch("subprocess.run")
    def test_command_with_success_message(self, mock_run: Mock) -> None:
        """Should display success message when provided."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        success, _ = run_git_command(["git", "commit", "-m", "test"], "Error message", "Success!")

        assert success is True

    @patch("subprocess.run")
    def test_command_failure(self, mock_run: Mock) -> None:
        """Should handle command failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "invalid"], stderr="error occurred"
        )

        success, _ = run_git_command(["git", "invalid"], "Error message")

        assert success is False

    @patch("subprocess.run")
    def test_timeout_error(self, mock_run: Mock) -> None:
        """Should handle timeout correctly."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["git", "status"], timeout=60)

        success, error = run_git_command(["git", "status"], "Timeout error", timeout=60)

        assert success is False

    @patch("subprocess.run")
    def test_called_process_error(self, mock_run: Mock) -> None:
        """Should handle process error."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "status"], stderr="error message"
        )

        success, _ = run_git_command(["git", "status"], "Process error")

        assert success is False

    @patch("subprocess.run")
    def test_file_not_found_error(self, mock_run: Mock) -> None:
        """Should handle file not found (git not installed)."""
        mock_run.side_effect = FileNotFoundError()

        success, _ = run_git_command(["git", "status"], "Git not found")

        assert success is False

    @patch("subprocess.run")
    def test_custom_timeout(self, mock_run: Mock) -> None:
        """Should respect custom timeout."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        run_git_command(["git", "push"], "Error", timeout=180)

        # Check that timeout parameter was passed
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["timeout"] == 180


class TestGitAdd:
    """Tests for git_add function."""

    @patch("ccg.git.run_git_command")
    def test_add_all_files(self, mock_run: Mock) -> None:
        """Should add all files when paths=None."""
        mock_run.return_value = (True, None)

        result = git_add(paths=None)

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "add", "."], "Error during 'git add' for path '.'", None
        )

    @patch("ccg.git.run_git_command")
    def test_add_specific_paths(self, mock_run: Mock) -> None:
        """Should add specific paths."""
        mock_run.return_value = (True, None)

        result = git_add(paths=["src/", "tests/"])

        assert result is True
        assert mock_run.call_count == 2

        # Check calls were made for each path
        calls = mock_run.call_args_list
        assert calls[0][0][0] == ["git", "add", "src/"]
        assert calls[1][0][0] == ["git", "add", "tests/"]

    @patch("ccg.git.run_git_command")
    def test_add_single_file(self, mock_run: Mock) -> None:
        """Should add single file."""
        mock_run.return_value = (True, None)

        result = git_add(paths=["README.md"])

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "add", "README.md"],
            "Error during 'git add' for path 'README.md'",
            None,
        )

    @patch("ccg.git.run_git_command")
    def test_add_failure(self, mock_run: Mock) -> None:
        """Should return False on failure."""
        mock_run.return_value = (False, "Error")

        result = git_add(paths=None)

        assert result is False


class TestGitCommit:
    """Tests for git_commit function."""

    @patch("ccg.git.run_git_command")
    def test_successful_commit(self, mock_run: Mock) -> None:
        """Should create commit successfully."""
        mock_run.return_value = (True, None)

        result = git_commit("feat: test commit")

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "commit", "-m", "feat: test commit"],
            "Error during 'git commit'",
            "New commit successfully created!",
        )

    @patch("ccg.git.run_git_command")
    def test_commit_with_body(self, mock_run: Mock) -> None:
        """Should handle commit with message and body."""
        mock_run.return_value = (True, None)

        message = "feat: new feature\n\nDetailed description"
        result = git_commit(message)

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "git"
        assert call_args[1] == "commit"

    @patch("ccg.git.run_git_command")
    def test_commit_failure(self, mock_run: Mock) -> None:
        """Should return False on failure."""
        mock_run.return_value = (False, "Error")

        result = git_commit("feat: test")

        assert result is False


class TestCheckIsGitRepo:
    """Tests for check_is_git_repo function."""

    @patch("ccg.git.run_git_command")
    def test_is_git_repo(self, mock_run: Mock) -> None:
        """Should return True if in git repo."""
        mock_run.return_value = (True, None)

        result = check_is_git_repo()

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--is-inside-work-tree"],
            "Not a git repository",
            show_output=True,
        )

    @patch("ccg.git.run_git_command")
    def test_not_git_repo(self, mock_run: Mock) -> None:
        """Should return False if not in git repo."""
        mock_run.return_value = (False, "Error")

        result = check_is_git_repo()

        assert result is False


class TestCheckHasChanges:
    """Tests for check_has_changes function."""

    @patch("ccg.git.run_git_command")
    def test_has_changes(self, mock_run: Mock) -> None:
        """Should return True if there are changes."""
        mock_run.return_value = (True, "modified files")

        result = check_has_changes()

        assert result is True

    @patch("ccg.git.run_git_command")
    def test_has_changes_with_paths(self, mock_run: Mock) -> None:
        """Should check for changes in specific paths."""
        mock_run.return_value = (True, "changes")

        result = check_has_changes(paths=["src/"])

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "src/" in call_args

    @patch("ccg.git.run_git_command")
    def test_no_changes(self, mock_run: Mock) -> None:
        """Should return False if no changes."""
        mock_run.return_value = (True, "")

        result = check_has_changes()

        assert result is False


# ============================================================================
# Additional Git Functions Tests
# ============================================================================


class TestGitPush:
    """Tests for git_push function."""

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_success(self, mock_run: Mock, mock_branch: Mock) -> None:
        """Should push successfully."""
        from ccg.git import git_push

        mock_branch.return_value = "main"
        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (True, None),  # git push
        ]

        result = git_push()

        assert result is True

    @patch("ccg.git.get_current_branch")
    def test_push_no_branch(self, mock_branch: Mock) -> None:
        """Should fail if cannot determine branch."""
        from ccg.git import git_push

        mock_branch.return_value = None

        result = git_push()

        assert result is False

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_no_remote(self, mock_run: Mock, mock_branch: Mock) -> None:
        """Should fail if no remote configured."""
        from ccg.git import git_push

        mock_branch.return_value = "main"
        mock_run.return_value = (False, None)

        result = git_push()

        assert result is False

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_with_set_upstream(self, mock_run: Mock, mock_branch: Mock) -> None:
        """Should push with --set-upstream flag."""
        from ccg.git import git_push

        mock_branch.return_value = "feature"
        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (True, None),  # git push --set-upstream
        ]

        result = git_push(set_upstream=True)

        assert result is True
        assert mock_run.call_count == 2
        push_call = mock_run.call_args_list[1]
        assert "--set-upstream" in push_call[0][0]

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_with_force(self, mock_run: Mock, mock_branch: Mock) -> None:
        """Should push with --force flag."""
        from ccg.git import git_push

        mock_branch.return_value = "main"
        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (True, None),  # git push --force
        ]

        result = git_push(force=True)

        assert result is True

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_with_upstream_and_force(self, mock_run: Mock, mock_branch: Mock) -> None:
        """Should push with both --set-upstream and --force."""
        from ccg.git import git_push

        mock_branch.return_value = "feature"
        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (True, None),  # git push --set-upstream --force
        ]

        result = git_push(set_upstream=True, force=True)

        assert result is True
        push_call = mock_run.call_args_list[1]
        assert "--set-upstream" in push_call[0][0]
        assert "--force" in push_call[0][0]

    @patch("ccg.utils.confirm_user_action")
    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_handles_upstream_error(
        self, mock_run: Mock, mock_branch: Mock, mock_confirm: Mock
    ) -> None:
        """Should handle upstream error and retry."""
        from ccg.git import git_push

        mock_branch.return_value = "feature"
        mock_confirm.return_value = True
        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (False, "no upstream branch"),  # git push fails
            (True, "origin"),  # git remote (retry)
            (True, None),  # git push --set-upstream
        ]

        # First call fails, then recursively calls with set_upstream=True
        git_push()

        assert mock_confirm.call_count == 1


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    @patch("ccg.git.run_git_command")
    def test_get_branch_success(self, mock_run: Mock) -> None:
        """Should return current branch name."""
        from ccg.git import get_current_branch

        mock_run.return_value = (True, "main")

        result = get_current_branch()

        assert result == "main"

    @patch("ccg.git.run_git_command")
    def test_get_branch_failure(self, mock_run: Mock) -> None:
        """Should return None on failure."""
        from ccg.git import get_current_branch

        mock_run.return_value = (False, None)

        result = get_current_branch()

        assert result is None


class TestCreateTag:
    """Tests for create_tag function."""

    @patch("ccg.git.run_git_command")
    def test_create_lightweight_tag(self, mock_run: Mock) -> None:
        """Should create lightweight tag."""
        from ccg.git import create_tag

        mock_run.return_value = (True, None)

        result = create_tag("v1.0.0")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["git", "tag", "v1.0.0"]

    @patch("ccg.git.run_git_command")
    def test_create_annotated_tag(self, mock_run: Mock) -> None:
        """Should create annotated tag with message."""
        from ccg.git import create_tag

        mock_run.return_value = (True, None)

        result = create_tag("v1.0.0", "Release version 1.0.0")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert call_args[0:2] == ["git", "tag"]
        assert "-a" in call_args
        assert "-m" in call_args


class TestPushTag:
    """Tests for push_tag function."""

    @patch("ccg.git.run_git_command")
    def test_push_tag_success(self, mock_run: Mock) -> None:
        """Should push tag successfully."""
        from ccg.git import push_tag

        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (True, None),  # git push tag
        ]

        result = push_tag("v1.0.0")

        assert result is True

    @patch("ccg.git.run_git_command")
    def test_push_tag_no_remote(self, mock_run: Mock) -> None:
        """Should fail if no remote configured."""
        from ccg.git import push_tag

        mock_run.return_value = (False, None)

        result = push_tag("v1.0.0")

        assert result is False


class TestDiscardLocalChanges:
    """Tests for discard_local_changes function."""

    @patch("ccg.git.run_git_command")
    def test_discard_all_changes(self, mock_run: Mock) -> None:
        """Should discard all local changes."""
        from ccg.git import discard_local_changes

        mock_run.return_value = (True, None)

        result = discard_local_changes()

        assert result is True
        assert mock_run.call_count == 3
        calls = [call[0][0] for call in mock_run.call_args_list]
        assert calls[0] == ["git", "reset", "HEAD"]
        assert calls[1] == ["git", "checkout", "."]
        assert calls[2] == ["git", "clean", "-fd"]

    @patch("ccg.git.run_git_command")
    def test_discard_fails_on_reset(self, mock_run: Mock) -> None:
        """Should return False if reset fails."""
        from ccg.git import discard_local_changes

        mock_run.return_value = (False, None)

        result = discard_local_changes()

        assert result is False


class TestPullFromRemote:
    """Tests for pull_from_remote function."""

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_pull_success(self, mock_run: Mock, mock_branch: Mock) -> None:
        """Should pull successfully."""
        from ccg.git import pull_from_remote

        mock_branch.return_value = "main"
        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (True, None),  # git pull
        ]

        result = pull_from_remote()

        assert result is True

    @patch("ccg.git.run_git_command")
    def test_pull_no_remote(self, mock_run: Mock) -> None:
        """Should fail if no remote configured."""
        from ccg.git import pull_from_remote

        mock_run.return_value = (False, None)

        result = pull_from_remote()

        assert result is False


class TestGetStagedFiles:
    """Tests for get_staged_files function."""

    @patch("ccg.git.run_git_command")
    def test_get_staged_files_success(self, mock_run: Mock) -> None:
        """Should return list of staged files."""
        from ccg.git import get_staged_files

        mock_run.return_value = (True, "src/file1.py\nsrc/file2.py\nREADME.md")

        result = get_staged_files()

        assert result == ["src/file1.py", "src/file2.py", "README.md"]

    @patch("ccg.git.run_git_command")
    def test_get_staged_files_empty(self, mock_run: Mock) -> None:
        """Should return empty list if no staged files."""
        from ccg.git import get_staged_files

        mock_run.return_value = (True, "")

        result = get_staged_files()

        assert result == []

    @patch("ccg.git.run_git_command")
    def test_get_staged_files_failure(self, mock_run: Mock) -> None:
        """Should return empty list on failure."""
        from ccg.git import get_staged_files

        mock_run.return_value = (False, None)

        result = get_staged_files()

        assert result == []


class TestGetRepositoryName:
    """Tests for get_repository_name function."""

    @patch("ccg.git.run_git_command")
    def test_get_repository_name(self, mock_run: Mock) -> None:
        """Should return repository name."""
        from ccg.git import get_repository_name

        mock_run.return_value = (True, "/home/user/projects/my-repo")

        result = get_repository_name()

        assert result == "my-repo"

    @patch("ccg.git.run_git_command")
    def test_get_repository_name_failure(self, mock_run: Mock) -> None:
        """Should return None on failure."""
        from ccg.git import get_repository_name

        mock_run.return_value = (False, None)

        result = get_repository_name()

        assert result is None


class TestGetRepositoryRoot:
    """Tests for get_repository_root function."""

    @patch("ccg.git.run_git_command")
    def test_get_repository_root(self, mock_run: Mock) -> None:
        """Should return repository root path."""
        from ccg.git import get_repository_root

        mock_run.return_value = (True, "/home/user/projects/my-repo")

        result = get_repository_root()

        assert result == "/home/user/projects/my-repo"


class TestIsPathInRepository:
    """Tests for is_path_in_repository function."""

    def test_path_inside_repo(self) -> None:
        """Should return True for path inside repository."""
        from ccg.git import is_path_in_repository

        result = is_path_in_repository("/home/user/repo/src", "/home/user/repo")

        assert result is True

    def test_path_outside_repo(self) -> None:
        """Should return False for path outside repository."""
        from ccg.git import is_path_in_repository

        result = is_path_in_repository("/home/other/file", "/home/user/repo")

        assert result is False


class TestBranchExistsOnRemote:
    """Tests for branch_exists_on_remote function."""

    @patch("ccg.git.run_git_command")
    def test_branch_exists(self, mock_run: Mock) -> None:
        """Should return True if branch exists on remote."""
        from ccg.git import branch_exists_on_remote

        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (True, "refs/heads/main"),  # git ls-remote
        ]

        result = branch_exists_on_remote("main")

        assert result is True

    @patch("ccg.git.run_git_command")
    def test_branch_not_exists(self, mock_run: Mock) -> None:
        """Should return False if branch doesn't exist."""
        from ccg.git import branch_exists_on_remote

        mock_run.side_effect = [
            (True, "origin"),
            (True, ""),  # Empty output means branch doesn't exist
        ]

        result = branch_exists_on_remote("nonexistent")

        assert result is False


class TestGetRecentCommits:
    """Tests for get_recent_commits function."""

    @patch("ccg.git.run_git_command")
    def test_get_recent_commits(self, mock_run: Mock) -> None:
        """Should return list of recent commits."""
        from ccg.git import get_recent_commits

        mock_run.return_value = (
            True,
            "abc123|abc|feat: add feature|John Doe|2 hours ago\n"
            "def456|def|fix: bug fix|Jane Smith|1 day ago",
        )

        result = get_recent_commits(2)

        assert len(result) == 2
        assert result[0] == ("abc123", "abc", "feat: add feature", "John Doe", "2 hours ago")
        assert result[1] == ("def456", "def", "fix: bug fix", "Jane Smith", "1 day ago")

    @patch("ccg.git.run_git_command")
    def test_get_recent_commits_empty(self, mock_run: Mock) -> None:
        """Should return empty list if no commits."""
        from ccg.git import get_recent_commits

        mock_run.return_value = (True, "")

        result = get_recent_commits()

        assert result == []


class TestGetCommitByHash:
    """Tests for get_commit_by_hash function."""

    @patch("ccg.git.run_git_command")
    def test_get_commit_with_body(self, mock_run: Mock) -> None:
        """Should return commit details with body."""
        from ccg.git import get_commit_by_hash

        mock_run.side_effect = [
            (True, None),  # verify
            (True, "abc123full"),  # full hash
            (True, "abc123"),  # short hash
            (True, "feat: add feature\n\nDetailed description"),  # message
            (True, "John Doe"),  # author
            (True, "2 hours ago"),  # date
        ]

        result = get_commit_by_hash("abc123")

        assert result is not None
        assert result[0] == "abc123full"
        assert result[2] == "feat: add feature"
        assert result[3] == "Detailed description"

    @patch("ccg.git.run_git_command")
    def test_get_commit_not_found(self, mock_run: Mock) -> None:
        """Should return None if commit not found."""
        from ccg.git import get_commit_by_hash

        mock_run.return_value = (False, None)

        result = get_commit_by_hash("invalid")

        assert result is None


class TestEditCommitMessage:
    """Tests for edit_commit_message function."""

    @patch("ccg.git.edit_latest_commit_with_amend")
    @patch("ccg.git.run_git_command")
    def test_edit_latest_commit(self, mock_run: Mock, mock_amend: Mock) -> None:
        """Should use amend for latest commit."""
        from ccg.git import edit_commit_message

        mock_run.return_value = (True, "abc123")
        mock_amend.return_value = True

        result = edit_commit_message("abc123", "new: message")

        assert result is True
        mock_amend.assert_called_once()

    @patch("ccg.git.edit_old_commit_with_filter_branch")
    @patch("ccg.git.run_git_command")
    def test_edit_old_commit(self, mock_run: Mock, mock_filter: Mock) -> None:
        """Should use filter-branch for old commit."""
        from ccg.git import edit_commit_message

        mock_run.side_effect = [
            (True, "def456"),  # latest commit (different)
            (True, ""),  # not initial commit
        ]
        mock_filter.return_value = True

        result = edit_commit_message("abc123", "new: message")

        assert result is True
        mock_filter.assert_called_once()


class TestDeleteCommit:
    """Tests for delete_commit function."""

    @patch("ccg.git.delete_latest_commit")
    @patch("ccg.git.run_git_command")
    def test_delete_latest_commit(self, mock_run: Mock, mock_delete: Mock) -> None:
        """Should use reset for latest commit."""
        from ccg.git import delete_commit

        mock_run.side_effect = [
            (True, None),  # verify commit exists
            (True, "abc123"),  # get latest commit
        ]
        mock_delete.return_value = True

        result = delete_commit("abc123")

        assert result is True
        mock_delete.assert_called_once()

    @patch("ccg.git.delete_old_commit_with_rebase")
    @patch("ccg.git.run_git_command")
    def test_delete_old_commit(self, mock_run: Mock, mock_rebase: Mock) -> None:
        """Should use rebase for old commit."""
        from ccg.git import delete_commit

        mock_run.side_effect = [
            (True, None),  # verify
            (True, "def456"),  # latest (different)
        ]
        mock_rebase.return_value = True

        result = delete_commit("abc123")

        assert result is True
        mock_rebase.assert_called_once()


class TestPreCommitHooks:
    """Tests for pre-commit hooks functions."""

    @patch("subprocess.run")
    def test_run_pre_commit_hooks_success(self, mock_run: Mock) -> None:
        """Should run pre-commit hooks successfully."""
        from ccg.git import run_pre_commit_hooks

        mock_run.return_value = Mock(returncode=0, stdout="All passed", stderr="")

        result = run_pre_commit_hooks(["src/file.py"])

        assert result is True

    @patch("subprocess.run")
    def test_run_pre_commit_hooks_failure(self, mock_run: Mock) -> None:
        """Should return False if hooks fail."""
        from ccg.git import run_pre_commit_hooks

        mock_run.return_value = Mock(returncode=1, stdout="Failed", stderr="")

        result = run_pre_commit_hooks(["src/file.py"])

        assert result is False

    @patch("subprocess.run")
    def test_run_pre_commit_hooks_timeout(self, mock_run: Mock) -> None:
        """Should handle timeout."""
        from ccg.git import run_pre_commit_hooks

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["pre-commit"], timeout=120)

        result = run_pre_commit_hooks(["src/file.py"])

        assert result is False

    @patch("os.path.exists")
    def test_check_and_install_pre_commit_no_config(self, mock_exists: Mock) -> None:
        """Should skip if no config exists."""
        from ccg.git import check_and_install_pre_commit

        mock_exists.return_value = False

        result = check_and_install_pre_commit()

        assert result is True

    @patch("ccg.git.get_staged_files")
    @patch("ccg.git.run_pre_commit_hooks")
    @patch("ccg.git.run_git_command")
    @patch("os.path.exists")
    def test_check_and_install_pre_commit_success(
        self, mock_exists: Mock, mock_run: Mock, mock_hooks: Mock, mock_staged: Mock
    ) -> None:
        """Should install and run pre-commit hooks."""
        from ccg.git import check_and_install_pre_commit

        mock_exists.return_value = True
        mock_run.side_effect = [
            (True, "2.0.0"),  # pre-commit --version
            (True, None),  # pre-commit install
        ]
        mock_staged.return_value = ["src/file.py"]
        mock_hooks.return_value = True

        result = check_and_install_pre_commit()

        assert result is True


class TestCheckRemoteAccess:
    """Tests for check_remote_access function."""

    @patch("subprocess.run")
    @patch("ccg.git.run_git_command")
    def test_check_remote_access_success(self, mock_run: Mock, mock_subprocess: Mock) -> None:
        """Should return True if remote is accessible."""
        from ccg.git import check_remote_access

        mock_run.return_value = (True, "origin\thttps://github.com/user/repo.git")
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        result = check_remote_access()

        assert result is True

    @patch("ccg.git.run_git_command")
    def test_check_remote_access_no_remote(self, mock_run: Mock) -> None:
        """Should return False if no remote configured."""
        from ccg.git import check_remote_access

        mock_run.return_value = (False, None)

        result = check_remote_access()

        assert result is False

    @patch("subprocess.run")
    @patch("ccg.git.run_git_command")
    def test_check_remote_access_permission_denied(
        self, mock_run: Mock, mock_subprocess: Mock
    ) -> None:
        """Should return False on permission denied."""
        from ccg.git import check_remote_access

        mock_run.return_value = (True, "origin\thttps://github.com/user/repo.git")
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="permission denied")

        result = check_remote_access()

        assert result is False

    @patch("subprocess.run")
    @patch("ccg.git.run_git_command")
    def test_check_remote_access_timeout(self, mock_run: Mock, mock_subprocess: Mock) -> None:
        """Should return False on timeout."""
        from ccg.git import check_remote_access

        mock_run.return_value = (True, "origin\thttps://github.com/user/repo.git")
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["git", "ls-remote"], timeout=15
        )

        result = check_remote_access()

        assert result is False
