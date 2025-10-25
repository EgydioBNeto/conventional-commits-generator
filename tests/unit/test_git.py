"""Unit tests for git.py module."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest

from ccg.cache import invalidate_repository_cache
from ccg.git import check_has_changes, check_is_git_repo, git_add, git_commit, run_git_command


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the repository cache before each test."""
    invalidate_repository_cache()
    yield
    invalidate_repository_cache()


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

    @patch("ccg.git.ProgressSpinner")
    @patch("ccg.git.run_git_command")
    def test_successful_commit(self, mock_run: Mock, mock_spinner: Mock) -> None:
        """Should create commit successfully."""
        mock_run.return_value = (True, None)
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance

        result = git_commit("feat: test commit")

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "commit", "-m", "feat: test commit"],
            "",
            None,
        )

    @patch("ccg.git.ProgressSpinner")
    @patch("ccg.git.run_git_command")
    def test_commit_with_body(self, mock_run: Mock, mock_spinner: Mock) -> None:
        """Should handle commit with message and body."""
        mock_run.return_value = (True, None)
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance

        message = "feat: new feature\n\nDetailed description"
        result = git_commit(message)

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "git"
        assert call_args[1] == "commit"

    @patch("ccg.git.ProgressSpinner")
    @patch("ccg.git.run_git_command")
    def test_commit_failure(self, mock_run: Mock, mock_spinner: Mock) -> None:
        """Should return False on failure."""
        mock_run.return_value = (False, "Error")
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance

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

    @pytest.mark.parametrize("user_confirms", [True, False])
    @patch("ccg.utils.confirm_user_action")
    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_handles_upstream_error(
        self, mock_run: Mock, mock_branch: Mock, mock_confirm: Mock, user_confirms: bool
    ) -> None:
        """Should handle upstream error and retry only if user confirms."""
        from ccg.git import git_push

        mock_branch.return_value = "feature"
        mock_confirm.return_value = user_confirms

        # Mock git push failing with an upstream error
        # Note: get_remote_name is cached, so it's only called once
        mock_run.side_effect = [
            (True, "origin"),  # First call to get_remote_name (cached for subsequent calls)
            (False, "no upstream branch"),  # git push fails
            # The following mock is only for the user_confirms=True case
            (True, None),  # git_push(set_upstream=True) succeeds
        ]

        git_push()

        # confirm_user_action should always be called once
        mock_confirm.assert_called_once()

        if user_confirms:
            # 3 calls: get_remote (cached), push, push (set-upstream)
            assert mock_run.call_count == 3
        else:
            # 2 calls: get_remote, push
            assert mock_run.call_count == 2

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_with_set_upstream_failure(self, mock_run: Mock, mock_branch: Mock) -> None:
        """Should handle failure when pushing with --set-upstream."""
        from ccg.git import git_push

        mock_branch.return_value = "feature"
        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (False, "Error: permission denied"),  # git push --set-upstream fails
        ]

        result = git_push(set_upstream=True)

        assert result is False
        assert mock_run.call_count == 2

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.run_git_command")
    def test_push_with_force_failure(self, mock_run: Mock, mock_branch: Mock) -> None:
        """Should handle failure when force pushing."""
        from ccg.git import git_push

        mock_branch.return_value = "main"
        mock_run.side_effect = [
            (True, "origin"),  # git remote
            (False, "Error: rejected"),  # git push --force fails
        ]

        result = git_push(force=True)

        assert result is False
        assert mock_run.call_count == 2


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


class TestGetRemoteName:
    """Tests for get_remote_name function."""

    @patch("ccg.git.run_git_command")
    def test_get_remote_name_success(self, mock_run: Mock) -> None:
        """Should return remote name."""
        from ccg.git import get_remote_name

        mock_run.return_value = (True, "origin")

        result = get_remote_name()

        assert result == "origin"

    @patch("ccg.git.run_git_command")
    def test_get_remote_name_no_remote(self, mock_run: Mock) -> None:
        """Should return None if no remote."""
        from ccg.git import get_remote_name

        mock_run.return_value = (False, None)

        result = get_remote_name()

        assert result is None

    @patch("ccg.git.run_git_command")
    def test_get_remote_name_empty_output(self, mock_run: Mock) -> None:
        """Should return None if output is empty."""
        from ccg.git import get_remote_name

        mock_run.return_value = (True, "")

        result = get_remote_name()

        assert result is None

    @patch("ccg.git.run_git_command")
    def test_get_remote_name_multiple_remotes(self, mock_run: Mock) -> None:
        """Should return first remote when multiple exist."""
        from ccg.git import get_remote_name

        mock_run.return_value = (True, "origin\nupstream\nfork")

        result = get_remote_name()

        assert result == "origin"


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

    @patch("ccg.git_strategies.edit_commit_with_strategy")
    @patch("ccg.git.run_git_command")
    def test_edit_latest_commit(self, mock_run: Mock, mock_strategy: Mock) -> None:
        """Should use strategy for latest commit."""
        from ccg.git import edit_commit_message

        mock_run.return_value = (True, "abc123")
        mock_strategy.return_value = True

        result = edit_commit_message("abc123", "new: message")

        assert result is True
        mock_strategy.assert_called_once_with(
            commit_hash="abc123",
            latest_commit_hash="abc123",
            new_message="new: message",
            new_body=None,
            is_initial_commit=False,
        )

    @patch("ccg.git_strategies.edit_commit_with_strategy")
    @patch("ccg.git.run_git_command")
    def test_edit_old_commit(self, mock_run: Mock, mock_strategy: Mock) -> None:
        """Should use strategy for old commit."""
        from ccg.git import edit_commit_message

        mock_run.side_effect = [
            (True, "def456"),  # latest commit (different)
            (True, ""),  # not initial commit
        ]
        mock_strategy.return_value = True

        result = edit_commit_message("abc123", "new: message")

        assert result is True
        mock_strategy.assert_called_once_with(
            commit_hash="abc123",
            latest_commit_hash="def456",
            new_message="new: message",
            new_body=None,
            is_initial_commit=False,
        )


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
    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_check_and_install_pre_commit_success(
        self, mock_exists: Mock, mock_subprocess: Mock, mock_hooks: Mock, mock_staged: Mock
    ) -> None:
        """Should install and run pre-commit hooks."""
        from ccg.git import check_and_install_pre_commit

        mock_exists.return_value = True
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout="pre-commit 2.0.0", stderr=""),  # pre-commit --version
            Mock(returncode=0, stdout="", stderr=""),  # pre-commit install
        ]
        mock_staged.return_value = ["src/file.py"]
        mock_hooks.return_value = True

        result = check_and_install_pre_commit()

        assert result is True

    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_check_pre_commit_not_installed(
        self, mock_exists: Mock, mock_run: Mock, capsys
    ) -> None:
        """Should return False if pre-commit is not installed."""
        from ccg.git import check_and_install_pre_commit

        mock_exists.return_value = True
        mock_run.side_effect = FileNotFoundError

        result = check_and_install_pre_commit()

        assert result is False
        captured = capsys.readouterr()
        assert "pre-commit is configured but not installed" in captured.out


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

    @pytest.mark.parametrize(
        "error_message,expected_message",
        [
            ("permission denied", "ACCESS DENIED"),
            ("access denied", "ACCESS DENIED"),
            ("authentication failed", "ACCESS DENIED"),
            ("fatal: could not read from remote repository", "REPOSITORY ERROR"),
            ("please make sure you have the correct access rights", "REPOSITORY ERROR"),
            ("repository not found", "REPOSITORY ERROR"),
            ("403 forbidden", "ACCESS DENIED"),
            ("401 unauthorized", "ACCESS DENIED"),
            ("ssh: connect to host", "NETWORK ERROR"),
            ("connection refused", "NETWORK ERROR"),
            ("terminal prompts disabled", "ACCESS DENIED"),
            ("could not read username", "ACCESS DENIED"),
        ],
    )
    @patch("subprocess.run")
    @patch("ccg.git.run_git_command")
    def test_check_remote_access_various_permission_errors(
        self,
        mock_run: Mock,
        mock_subprocess: Mock,
        error_message: str,
        expected_message: str,
        capsys,
    ) -> None:
        """Should return False and display appropriate error message based on error category."""
        from ccg.git import check_remote_access

        mock_run.return_value = (True, "origin\thttps://github.com/user/repo.git")
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr=error_message)

        result = check_remote_access()

        assert result is False
        captured = capsys.readouterr()
        assert expected_message in captured.out

    @patch("subprocess.run")
    @patch("ccg.git.run_git_command")
    def test_check_remote_access_other_error(
        self, mock_run: Mock, mock_subprocess: Mock, capsys
    ) -> None:
        """Should return False for a generic, non-permission error."""
        from ccg.git import check_remote_access

        mock_run.return_value = (True, "origin\thttps://github.com/user/repo.git")
        mock_subprocess.return_value = Mock(returncode=1, stdout="", stderr="some other error")

        result = check_remote_access()

        assert result is False
        captured = capsys.readouterr()
        assert "Cannot access remote repository" in captured.out


class TestDeleteLatestCommit:
    """Tests for delete_latest_commit function."""

    @patch("ccg.git.run_git_command")
    def test_delete_latest_success(self, mock_run: Mock) -> None:
        """Should delete latest commit with reset."""
        from ccg.git import delete_latest_commit

        mock_run.return_value = (True, None)

        result = delete_latest_commit()

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["git", "reset", "--hard", "HEAD~1"]


class TestCreateRebaseScriptForDeletion:
    """Tests for create_rebase_script_for_deletion function."""

    @patch("tempfile.NamedTemporaryFile")
    @patch("ccg.git.run_git_command")
    def test_create_script_success(self, mock_run: Mock, mock_tempfile: Mock) -> None:
        """Should create rebase script successfully."""
        from ccg.git import create_rebase_script_for_deletion

        mock_temp = Mock()
        mock_temp.name = "/tmp/rebase_script"
        mock_temp.__enter__ = Mock(return_value=mock_temp)
        mock_temp.__exit__ = Mock(return_value=False)
        mock_tempfile.return_value = mock_temp

        mock_run.side_effect = [
            (True, "abc123\ndef456\nghi789"),  # rev-list
            (True, "feat: first"),  # subject for abc123
            (True, "fix: second"),  # subject for def456 (target to delete)
            (True, "chore: third"),  # subject for ghi789
        ]

        success, script_file, script_lines = create_rebase_script_for_deletion("def456")

        assert success is True
        assert script_file == "/tmp/rebase_script"
        assert len(script_lines) == 2  # Excludes the deleted commit
        assert "abc123" in script_lines[0]
        assert "ghi789" in script_lines[1]

    @patch("ccg.git.run_git_command")
    def test_create_script_commit_not_found(self, mock_run: Mock) -> None:
        """Should return False if commit not in history."""
        from ccg.git import create_rebase_script_for_deletion

        mock_run.return_value = (True, "abc123\ndef456")

        success, script_file, script_lines = create_rebase_script_for_deletion("nonexistent")

        assert success is False
        assert script_file is None
        assert script_lines == []


class TestDeleteOldCommitWithRebase:
    """Tests for delete_old_commit_with_rebase function."""

    @patch("ccg.git.run_git_command")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_delete_all_commits_creates_empty_repo(
        self, mock_create_script: Mock, mock_run_git: Mock
    ) -> None:
        """Should handle deleting all commits by creating an empty repo."""
        from ccg.git import delete_old_commit_with_rebase

        # Simulate the script being empty, meaning all commits were to be deleted
        mock_create_script.return_value = (True, "/tmp/script", [])
        mock_run_git.return_value = (True, None)

        result = delete_old_commit_with_rebase("abc123")

        assert result is True
        # Asserts that 'git update-ref -d HEAD' was called
        mock_run_git.assert_called_once_with(
            ["git", "update-ref", "-d", "HEAD"],
            "Failed to create empty repository",
            "All commits removed - repository is now empty",
        )

    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_failure_aborts(
        self, mock_create_script: Mock, mock_subprocess: Mock, capsys
    ) -> None:
        """Should abort rebase on non-conflict failure and print stderr."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])
        mock_subprocess.return_value = Mock(returncode=1, stderr="Permission denied")

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is False
            # Check that rebase --abort was called
            abort_called = any(
                "rebase" in call.args[0] and "--abort" in call.args[0]
                for call in mock_run_git.call_args_list
            )
            assert abort_called
            captured = capsys.readouterr()
            assert "Permission denied" in captured.out

    @patch("ccg.git.read_input")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_conflict_user_resolves_successfully(
        self, mock_create_script: Mock, mock_subprocess: Mock, mock_read_input: Mock
    ) -> None:
        """Should complete rebase when user successfully resolves conflicts."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])

        # Subprocess calls:
        # 1. Initial rebase fails with conflict
        # 2. git status --short (to check for conflicts - shows conflicting files)
        # 3. git rebase --continue succeeds
        mock_subprocess.side_effect = [
            Mock(returncode=1, stderr="error: could not apply abc123... test commit"),
            Mock(
                returncode=0, stdout="UU file1.txt\nDD file2.py"
            ),  # git status --short shows conflicts
            Mock(returncode=0, stdout="", stderr=""),  # rebase --continue succeeds
        ]

        # User presses Enter to continue (empty string)
        mock_read_input.return_value = ""

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is True  # Successfully completed
            assert mock_read_input.call_count == 1
            # Check that rebase --abort was NOT called
            abort_called = any(
                "rebase" in call.args[0] and "--abort" in call.args[0]
                for call in mock_run_git.call_args_list
            )
            assert not abort_called

    @patch("ccg.git.read_input")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_conflict_user_says_not_resolved(
        self, mock_create_script: Mock, mock_subprocess: Mock, mock_read_input: Mock
    ) -> None:
        """Should abort when user types 'abort'."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])

        # Subprocess calls:
        # 1. Initial rebase fails with conflict
        # 2. git status --short (to check for conflicts)
        mock_subprocess.side_effect = [
            Mock(returncode=1, stderr="error: could not apply abc123... test commit"),
            Mock(returncode=0, stdout=""),  # git status --short
        ]

        # User types 'abort'
        mock_read_input.return_value = "abort"

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is False
            assert mock_read_input.call_count == 1
            # Check that rebase --abort WAS called
            abort_called = any(
                "rebase" in call.args[0] and "--abort" in call.args[0]
                for call in mock_run_git.call_args_list
            )
            assert abort_called

    @patch("ccg.git.read_input")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_conflict_still_has_conflicts_then_resolves(
        self, mock_create_script: Mock, mock_subprocess: Mock, mock_read_input: Mock
    ) -> None:
        """Should abort when continue fails with remaining conflicts."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])

        # Subprocess calls:
        # 1. Initial rebase: conflict
        # 2. git status --short (to check for conflicts)
        # 3. git rebase --continue: still has conflicts
        # 4. git status --short (recheck for remaining conflicts)
        mock_subprocess.side_effect = [
            Mock(returncode=1, stderr="error: could not apply abc123..."),
            Mock(returncode=0, stdout=""),  # git status --short
            Mock(
                returncode=1, stderr="error: conflict in file.txt", stdout="conflict"
            ),  # still conflicts
            Mock(returncode=0, stdout="UU file.txt"),  # recheck status shows conflicts
        ]

        # User presses Enter to continue
        mock_read_input.return_value = ""

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is False
            assert mock_read_input.call_count == 1
            # Check that rebase --abort WAS called (automatically)
            abort_called = any(
                "rebase" in call.args[0] and "--abort" in call.args[0]
                for call in mock_run_git.call_args_list
            )
            assert abort_called

    @patch("ccg.git.read_input")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_conflict_user_aborts(
        self, mock_create_script: Mock, mock_subprocess: Mock, mock_read_input: Mock
    ) -> None:
        """Should abort rebase when user chooses to abort on conflict."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])

        # Subprocess calls:
        # 1. Initial rebase fails with conflict
        # 2. git status --short (to check for conflicts)
        mock_subprocess.side_effect = [
            Mock(returncode=1, stderr="error: merge conflict in file.txt"),
            Mock(returncode=0, stdout=""),  # git status --short
        ]

        # User types 'abort'
        mock_read_input.return_value = "abort"

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is False
            # Check that read_input was called
            mock_read_input.assert_called_once()
            # Check that rebase --abort WAS called
            abort_called = any(
                "rebase" in call.args[0] and "--abort" in call.args[0]
                for call in mock_run_git.call_args_list
            )
            assert abort_called

    @patch("ccg.git.read_input")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_continue_fails_with_non_conflict_error(
        self, mock_create_script: Mock, mock_subprocess: Mock, mock_read_input: Mock
    ) -> None:
        """Should show error details when continue fails with non-conflict error."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])

        # Subprocess calls:
        # 1. Initial rebase: conflict
        # 2. git status --short (to check for conflicts)
        # 3. git rebase --continue: fails with non-conflict error (no "conflict" keyword)
        # 4. git status --short (recheck for remaining conflicts)
        mock_subprocess.side_effect = [
            Mock(returncode=1, stderr="error: could not apply abc123..."),
            Mock(returncode=0, stdout=""),  # git status --short
            Mock(
                returncode=1, stderr="fatal: unable to write new index file", stdout=""
            ),  # non-conflict error
            Mock(returncode=0, stdout=""),  # recheck status - no conflicts
        ]

        # User presses Enter to continue
        mock_read_input.return_value = ""

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is False
            assert mock_read_input.call_count == 1
            # Check that rebase --abort WAS called (automatically)
            abort_called = any(
                "rebase" in call.args[0] and "--abort" in call.args[0]
                for call in mock_run_git.call_args_list
            )
            assert abort_called

    @patch("ccg.git.read_input")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_continue_fails_user_aborts_after_retry(
        self, mock_create_script: Mock, mock_subprocess: Mock, mock_read_input: Mock
    ) -> None:
        """Should abort when continue fails after user tried to continue."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])

        # Subprocess calls:
        # 1. Initial rebase: conflict
        # 2. git status --short (to check for conflicts)
        # 3. git rebase --continue: still has conflicts
        # 4. git status --short (recheck for remaining conflicts)
        mock_subprocess.side_effect = [
            Mock(returncode=1, stderr="error: could not apply abc123..."),
            Mock(returncode=0, stdout=""),  # git status --short
            Mock(returncode=1, stderr="error: conflict in file.txt"),  # still has conflicts
            Mock(returncode=0, stdout="UU file.txt"),  # recheck status shows conflicts
        ]

        # User presses Enter to try to continue
        mock_read_input.return_value = ""

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is False
            assert mock_read_input.call_count == 1
            # Check that rebase --abort WAS called (automatically after failure)
            abort_called = any(
                "rebase" in call.args[0] and "--abort" in call.args[0]
                for call in mock_run_git.call_args_list
            )
            assert abort_called

    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_timeout_aborts(
        self, mock_create_script: Mock, mock_subprocess: Mock, capsys
    ) -> None:
        """Should abort rebase on timeout."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="git rebase", timeout=120)

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is False
            # Check that rebase --abort was called
            abort_called = any(
                "rebase" in call.args[0] and "--abort" in call.args[0]
                for call in mock_run_git.call_args_list
            )
            assert abort_called

    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_script_creation_fails(self, mock_create_script: Mock) -> None:
        """Should return False if script creation fails."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (False, None, [])

        result = delete_old_commit_with_rebase("abc123")

        assert result is False


# ============================================================================
# Hypothesis Property-Based Tests
# ============================================================================

from hypothesis import given
from hypothesis import strategies as st


class TestGetStagedFileChanges:
    """Tests for get_staged_file_changes function."""

    @patch("ccg.git.run_git_command")
    def test_get_staged_file_changes_success(self, mock_run: Mock) -> None:
        """Should return list of staged file changes with status."""
        from ccg.git import get_staged_file_changes

        mock_run.return_value = (True, "A\tnew_file.txt\nM\tmodified_file.py\nD\tdeleted_file.js\n")

        result = get_staged_file_changes()

        assert result == [
            ("A", "new_file.txt"),
            ("M", "modified_file.py"),
            ("D", "deleted_file.js"),
        ]

    @patch("ccg.git.run_git_command")
    def test_get_staged_file_changes_empty(self, mock_run: Mock) -> None:
        """Should return empty list if no staged file changes."""
        from ccg.git import get_staged_file_changes

        mock_run.return_value = (True, "")

        result = get_staged_file_changes()

        assert result == []

    @patch("ccg.git.run_git_command")
    def test_get_staged_file_changes_failure(self, mock_run: Mock) -> None:
        """Should return empty list on failure."""
        from ccg.git import get_staged_file_changes

        mock_run.return_value = (False, None)

        result = get_staged_file_changes()

        assert result == []


class TestIsPathInRepositoryProperties:
    """Property-based tests for is_path_in_repository function."""

    @given(st.text(min_size=1, max_size=100))
    def test_empty_repo_root_always_false(self, path: str) -> None:
        """Should return False when repo root is empty."""
        from ccg.git import is_path_in_repository

        result = is_path_in_repository(path, "")
        assert result is False

    @given(st.text(min_size=1, max_size=50))
    def test_same_path_as_repo_returns_true(self, path: str) -> None:
        """Should return True when path equals repo root."""
        from ccg.git import is_path_in_repository

        # Skip paths with special characters that would break path comparison
        try:
            result = is_path_in_repository(path, path)
            assert result is True
        except (ValueError, OSError):
            # Some paths may be invalid on certain OSes
            pass

    def test_child_path_returns_true(self) -> None:
        """Should return True for child paths."""
        from ccg.git import is_path_in_repository

        assert is_path_in_repository("/repo/src/file.py", "/repo") is True
        assert is_path_in_repository("/repo/tests", "/repo") is True

    def test_parent_path_returns_false(self) -> None:
        """Should return False for parent paths."""
        from ccg.git import is_path_in_repository

        assert is_path_in_repository("/home", "/home/user/repo") is False
        assert is_path_in_repository("/", "/home/user/repo") is False


class TestGetRemoteNameEdgeCases:
    """Additional tests for get_remote_name function."""

    @patch("ccg.git.run_git_command")
    def test_remote_with_whitespace(self, mock_run: Mock) -> None:
        """Should handle remote names with surrounding whitespace."""
        from ccg.git import get_remote_name

        mock_run.return_value = (True, "  origin  ")

        result = get_remote_name()

        assert result == "origin"

    @patch("ccg.git.run_git_command")
    def test_multiple_remotes_returns_first(self, mock_run: Mock) -> None:
        """Should return first remote when multiple exist."""
        from ccg.git import get_remote_name

        mock_run.return_value = (True, "origin\nupstream\nfork")

        result = get_remote_name()

        assert result == "origin"


class TestGetCommitByHashErrorPaths:
    """Tests for error handling in get_commit_by_hash."""

    @patch("ccg.git.run_git_command")
    def test_invalid_hash_returns_none(self, mock_run: Mock) -> None:
        """Should return None for invalid commit hash."""
        from ccg.git import get_commit_by_hash

        mock_run.return_value = (False, None)

        result = get_commit_by_hash("invalid123")

        assert result is None

    @patch("ccg.git.run_git_command")
    def test_commit_with_multiline_body(self, mock_run: Mock) -> None:
        """Should handle commits with multiline bodies."""
        from ccg.git import get_commit_by_hash

        mock_run.side_effect = [
            (True, None),  # verify
            (True, "abc123full"),  # full hash
            (True, "abc123"),  # short hash
            (True, "feat: test\n\nLine 1\n\nLine 2"),  # message with multiple paragraphs
            (True, "John"),  # author
            (True, "1 day ago"),  # date
        ]

        result = get_commit_by_hash("abc123")

        assert result is not None
        assert result[2] == "feat: test"
        assert "Line 1" in result[3]
        assert "Line 2" in result[3]


class TestRunGitCommandAdvanced:
    """Advanced tests for run_git_command error paths."""

    @patch("subprocess.run")
    def test_command_with_push_success_message(self, mock_run: Mock) -> None:
        """Should show section header for push success message."""
        from ccg.git import run_git_command

        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        success, _ = run_git_command(["git", "push"], "", "Changes pushed successfully!")

        assert success is True

    @patch("subprocess.run")
    def test_command_error_with_stderr_and_show_output(self, mock_run: Mock) -> None:
        """Should return stderr when show_output=True and error occurs."""
        from ccg.git import run_git_command

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["git", "invalid"], stderr="detailed error"
        )

        success, output = run_git_command(["git", "invalid"], "Error message", show_output=True)

        assert success is False
        assert output == "detailed error"

    @patch("subprocess.run")
    def test_command_error_with_stdout_fallback(self, mock_run: Mock) -> None:
        """Should fallback to stdout when stderr is empty."""
        from ccg.git import run_git_command

        error = subprocess.CalledProcessError(returncode=1, cmd=["git", "invalid"])
        error.stderr = None
        error.stdout = "stdout message"
        mock_run.side_effect = error

        success, output = run_git_command(["git", "invalid"], "Error", show_output=True)

        assert success is False
        assert output == "stdout message"

    @patch("subprocess.run")
    def test_command_error_shows_stderr_when_not_show_output(self, mock_run: Mock, capsys) -> None:
        """Should print stderr when show_output=False and error_message provided."""
        from ccg.git import run_git_command

        error = subprocess.CalledProcessError(returncode=1, cmd=["git", "invalid"])
        error.stderr = "error details"
        mock_run.side_effect = error

        success, output = run_git_command(["git", "invalid"], "Error message", show_output=False)

        assert success is False
        captured = capsys.readouterr()
        assert "error details" in captured.out


class TestPullFromRemoteAdvanced:
    """Advanced tests for pull_from_remote."""

    @patch("ccg.git.get_current_branch")
    @patch("ccg.git.get_remote_name")
    def test_pull_no_branch_name(self, mock_remote: Mock, mock_branch: Mock) -> None:
        """Should return False when cannot determine branch name."""
        from ccg.git import pull_from_remote

        mock_remote.return_value = "origin"
        mock_branch.return_value = None

        result = pull_from_remote()

        assert result is False


class TestCheckHasChangesAdvanced:
    """Advanced tests for check_has_changes with paths."""

    @patch("ccg.git.run_git_command")
    def test_check_changes_with_paths_found(self, mock_run: Mock) -> None:
        """Should return True when changes found in specific paths."""
        from ccg.git import check_has_changes

        mock_run.return_value = (True, "M  src/file.py")

        result = check_has_changes(paths=["src/"])

        assert result is True

    @patch("ccg.git.run_git_command")
    def test_check_changes_with_paths_not_found(self, mock_run: Mock) -> None:
        """Should return False when no changes in specific paths."""
        from ccg.git import check_has_changes

        mock_run.return_value = (True, "")

        result = check_has_changes(paths=["src/", "tests/"])

        assert result is False


class TestCheckRemoteAccessAdvanced:
    """Advanced tests for check_remote_access."""

    @patch("subprocess.run")
    @patch("ccg.git.run_git_command")
    def test_check_remote_access_exception(self, mock_run: Mock, mock_subprocess: Mock) -> None:
        """Should handle general exceptions during remote check."""
        from ccg.git import check_remote_access

        mock_run.return_value = (True, "origin\thttps://github.com/user/repo.git")
        mock_subprocess.side_effect = Exception("Unexpected error")

        result = check_remote_access()

        assert result is False


class TestDeleteOldCommitWithRebaseAdvanced:
    """Advanced tests for delete_old_commit_with_rebase error paths."""

    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_script_creation_returns_false(self, mock_create: Mock) -> None:
        """Should return False when script creation fails."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create.return_value = (False, None, [])

        result = delete_old_commit_with_rebase("abc123")

        assert result is False

    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_general_exception_aborts(
        self, mock_create: Mock, mock_subprocess: Mock
    ) -> None:
        """Should abort rebase on general exception."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create.return_value = (True, "/tmp/script", ["pick abc123 test"])
        mock_subprocess.side_effect = Exception("Unexpected error")

        with patch("ccg.git.run_git_command") as mock_run_git:
            result = delete_old_commit_with_rebase("def456")

            assert result is False
            # Check that rebase --abort was called
            abort_called = any(
                "rebase" in str(call.args[0]) and "--abort" in str(call.args[0])
                for call in mock_run_git.call_args_list
            )
            assert abort_called

    @patch("os.path.exists")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_cleanup_script_file_on_exception(
        self, mock_create: Mock, mock_exists: Mock
    ) -> None:
        """Should clean up script file even when exception occurs."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create.return_value = (True, "/tmp/script", ["pick abc123 test"])
        mock_exists.return_value = True

        with patch("os.unlink") as mock_unlink:
            with patch("subprocess.run", side_effect=Exception("Error")):
                with patch("ccg.git.run_git_command"):
                    result = delete_old_commit_with_rebase("def456")

                    assert result is False
                    mock_unlink.assert_called_once_with("/tmp/script")


class TestRunPreCommitHooksAdvanced:
    """Advanced tests for run_pre_commit_hooks error paths."""

    @patch("subprocess.run")
    def test_run_hooks_called_process_error(self, mock_run: Mock) -> None:
        """Should handle CalledProcessError from hooks."""
        from ccg.git import run_pre_commit_hooks

        error = subprocess.CalledProcessError(returncode=1, cmd=["pre-commit"])
        error.stdout = "hook failed"
        error.stderr = "error details"
        mock_run.side_effect = error

        result = run_pre_commit_hooks(["file.py"])

        assert result is False

    @patch("subprocess.run")
    def test_run_hooks_general_exception(self, mock_run: Mock) -> None:
        """Should handle general exceptions from hooks."""
        from ccg.git import run_pre_commit_hooks

        mock_run.side_effect = Exception("Unexpected error")

        result = run_pre_commit_hooks(["file.py"])

        assert result is False


class TestCheckAndInstallPreCommitAdvanced:
    """Advanced tests for check_and_install_pre_commit error paths."""

    @patch("ccg.git.get_staged_files")
    @patch("ccg.git.run_git_command")
    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_check_hooks_not_installed_failure(
        self, mock_exists: Mock, mock_subprocess: Mock, mock_run: Mock, mock_staged: Mock
    ) -> None:
        """Should return False when hook installation fails."""
        from ccg.git import check_and_install_pre_commit

        mock_exists.return_value = True
        mock_subprocess.return_value = Mock(returncode=0, stdout="2.0.0", stderr="")
        mock_run.return_value = (False, None)  # install fails

        result = check_and_install_pre_commit()

        assert result is False

    @patch("ccg.git.get_staged_files")
    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_check_pre_commit_timeout_treated_as_installed(
        self, mock_exists: Mock, mock_subprocess: Mock, mock_staged: Mock
    ) -> None:
        """Should treat timeout as pre-commit being installed."""
        from ccg.git import check_and_install_pre_commit

        mock_exists.return_value = True
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd=["pre-commit"], timeout=10)
        mock_staged.return_value = []

        with patch("ccg.git.run_git_command", return_value=(True, None)):
            result = check_and_install_pre_commit()

            # Should continue as if installed
            assert result is True

    @patch("ccg.git.get_staged_files")
    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_check_pre_commit_called_process_error_treated_as_installed(
        self, mock_exists: Mock, mock_subprocess: Mock, mock_staged: Mock
    ) -> None:
        """Should treat CalledProcessError as pre-commit being installed."""
        from ccg.git import check_and_install_pre_commit

        mock_exists.return_value = True
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["pre-commit"]
        )
        mock_staged.return_value = []

        with patch("ccg.git.run_git_command", return_value=(True, None)):
            result = check_and_install_pre_commit()

            # Should continue as if installed
            assert result is True

    @patch("os.path.exists")
    def test_check_general_exception(self, mock_exists: Mock) -> None:
        """Should handle general exceptions during check."""
        from ccg.git import check_and_install_pre_commit

        mock_exists.side_effect = Exception("Unexpected error")

        result = check_and_install_pre_commit()

        assert result is False


class TestCreateRebaseScriptForDeletionAdvanced:
    """Advanced tests for create_rebase_script_for_deletion."""

    @patch("ccg.git.run_git_command")
    def test_create_script_get_commits_fails(self, mock_run: Mock) -> None:
        """Should return False when cannot get commit history."""
        from ccg.git import create_rebase_script_for_deletion

        mock_run.return_value = (False, None)

        success, script_file, script_lines = create_rebase_script_for_deletion("abc123")

        assert success is False
        assert script_file is None
        assert script_lines == []

    @patch("tempfile.NamedTemporaryFile")
    @patch("ccg.git.run_git_command")
    def test_create_script_tempfile_fails(self, mock_run: Mock, mock_tempfile: Mock) -> None:
        """Should handle tempfile creation failure."""
        from ccg.git import create_rebase_script_for_deletion

        mock_run.side_effect = [
            (True, "abc123\ndef456"),  # rev-list
            (True, "feat: first"),  # subject for abc123
        ]
        mock_tempfile.side_effect = OSError("Cannot create temp file")

        success, script_file, script_lines = create_rebase_script_for_deletion("def456")

        assert success is False
        assert script_file is None


class TestDeleteCommitAdvanced:
    """Advanced tests for delete_commit."""

    @patch("ccg.git.run_git_command")
    def test_delete_commit_not_accessible(self, mock_run: Mock) -> None:
        """Should return False when commit not accessible."""
        from ccg.git import delete_commit

        mock_run.return_value = (False, None)

        result = delete_commit("invalid")

        assert result is False

    @patch("ccg.git.run_git_command")
    def test_delete_get_latest_commit_fails(self, mock_run: Mock) -> None:
        """Should return False when cannot get latest commit."""
        from ccg.git import delete_commit

        mock_run.side_effect = [
            (True, None),  # verify commit exists
            (False, None),  # get latest commit fails
        ]

        result = delete_commit("abc123")

        assert result is False


class TestEditCommitMessageAdvanced:
    """Advanced tests for edit_commit_message."""

    @patch("ccg.git.run_git_command")
    def test_edit_get_latest_commit_fails(self, mock_run: Mock) -> None:
        """Should return False when cannot get latest commit."""
        from ccg.git import edit_commit_message

        mock_run.return_value = (False, None)

        result = edit_commit_message("abc123", "feat: new")

        assert result is False

    @patch("ccg.git_strategies.edit_commit_with_strategy")
    @patch("ccg.git.run_git_command")
    def test_edit_initial_commit_detected(self, mock_run: Mock, mock_strategy: Mock) -> None:
        """Should detect and handle initial commit editing."""
        from ccg.git import edit_commit_message

        mock_run.side_effect = [
            (True, "def456"),  # latest commit (different)
            (True, "abc123"),  # initial commit check - contains our hash
        ]
        mock_strategy.return_value = True

        result = edit_commit_message("abc123", "feat: new")

        assert result is True
        # Check that is_initial_commit was set to True
        mock_strategy.assert_called_once_with(
            commit_hash="abc123",
            latest_commit_hash="def456",
            new_message="feat: new",
            new_body=None,
            is_initial_commit=True,
        )


class TestGetCommitByHashAdvanced:
    """Advanced tests for get_commit_by_hash error paths."""

    @patch("ccg.git.run_git_command")
    def test_get_commit_full_hash_fails(self, mock_run: Mock) -> None:
        """Should return None when cannot get full hash."""
        from ccg.git import get_commit_by_hash

        mock_run.side_effect = [
            (True, None),  # verify succeeds
            (False, None),  # get full hash fails
        ]

        result = get_commit_by_hash("abc")

        assert result is None

    @patch("ccg.git.run_git_command")
    def test_get_commit_message_fails(self, mock_run: Mock) -> None:
        """Should return None when cannot get commit message."""
        from ccg.git import get_commit_by_hash

        mock_run.side_effect = [
            (True, None),  # verify
            (True, "abc123full"),  # full hash
            (True, "abc"),  # short hash
            (False, None),  # message fails
        ]

        result = get_commit_by_hash("abc")

        assert result is None

    @patch("ccg.git.run_git_command")
    def test_get_commit_author_fails(self, mock_run: Mock) -> None:
        """Should use 'Unknown' when cannot get author."""
        from ccg.git import get_commit_by_hash

        mock_run.side_effect = [
            (True, None),  # verify
            (True, "abc123full"),  # full hash
            (True, "abc"),  # short hash
            (True, "feat: test"),  # message
            (False, None),  # author fails
            (True, "1 day ago"),  # date
        ]

        result = get_commit_by_hash("abc")

        assert result is not None
        assert result[4] == "Unknown"

    @patch("ccg.git.run_git_command")
    def test_get_commit_date_fails(self, mock_run: Mock) -> None:
        """Should use 'Unknown date' when cannot get date."""
        from ccg.git import get_commit_by_hash

        mock_run.side_effect = [
            (True, None),  # verify
            (True, "abc123full"),  # full hash
            (True, "abc"),  # short hash
            (True, "feat: test"),  # message
            (True, "John"),  # author
            (False, None),  # date fails
        ]

        result = get_commit_by_hash("abc")

        assert result is not None
        assert result[5] == "Unknown date"


class TestCreateRebaseScriptForDeletionEdgeCases:
    """Edge case tests for create_rebase_script_for_deletion."""

    @patch("ccg.git.run_git_command")
    def test_create_script_get_subject_fails(self, mock_run: Mock) -> None:
        """Should skip commit when cannot get subject."""
        from ccg.git import create_rebase_script_for_deletion

        mock_run.side_effect = [
            (True, "abc123\ndef456\nghi789"),  # rev-list
            (False, None),  # subject for abc123 fails
            (True, "fix: second"),  # subject for def456 (target)
            (True, "feat: third"),  # subject for ghi789
        ]

        with patch("tempfile.NamedTemporaryFile") as mock_temp:
            mock_file = Mock()
            mock_file.name = "/tmp/script"
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=False)
            mock_temp.return_value = mock_file

            success, script_file, script_lines = create_rebase_script_for_deletion("def456")

            assert success is True
            # Should only have ghi789 in script (abc123 skipped due to error)
            assert len(script_lines) == 1
            assert "ghi789" in script_lines[0]


class TestHandleUpstreamErrorReturnFalse:
    """Test handle_upstream_error when error doesn't match patterns."""

    @patch("ccg.utils.confirm_user_action", return_value=False)
    def test_upstream_error_no_match_returns_false(self, mock_confirm: Mock) -> None:
        """Should return False when error message doesn't match upstream patterns."""
        from ccg.git import handle_upstream_error

        error_output = "some other error message"
        result = handle_upstream_error("main", "origin", error_output)

        assert result is False
        mock_confirm.assert_not_called()


class TestGetCommitByHashShortHashFallback:
    """Test get_commit_by_hash when short hash retrieval fails."""

    @patch("ccg.git.run_git_command")
    def test_short_hash_fallback_uses_first_seven_chars(self, mock_run: Mock) -> None:
        """Should use first 7 chars of commit_hash when short hash fails."""
        from ccg.git import get_commit_by_hash

        mock_run.side_effect = [
            (True, None),  # rev-parse --verify
            (True, "abc123def456"),  # rev-parse (full hash)
            (False, None),  # rev-parse --short (fails)
            (True, "feat: test"),  # log -1 --pretty=%B
            (True, "Author Name"),  # log -1 --pretty=%an
            (True, "1 day ago"),  # log -1 --pretty=%ar
        ]

        result = get_commit_by_hash("abc123")

        assert result is not None
        assert result[1] == "abc123"[:7]  # short_hash fallback


class TestBranchExistsOnRemoteNoRemote:
    """Test branch_exists_on_remote when no remote configured."""

    @patch("ccg.git.get_remote_name", return_value=None)
    def test_no_remote_configured_returns_false(self, mock_get_remote: Mock) -> None:
        """Should return False when no remote is configured."""
        from ccg.git import branch_exists_on_remote

        result = branch_exists_on_remote("main")

        assert result is False


class TestGetRepositoryRootFailure:
    """Test get_repository_root when git command fails."""

    @patch("ccg.git.run_git_command", return_value=(False, None))
    def test_repository_root_failure_returns_none(self, mock_run: Mock) -> None:
        """Should return None when cannot get repository root."""
        from ccg.git import get_repository_root

        result = get_repository_root()

        assert result is None


class TestIsPathInRepositoryValueError:
    """Test is_path_in_repository when paths are on different drives."""

    @patch("os.path.relpath", side_effect=ValueError("path is on different drive"))
    @patch("os.path.abspath", side_effect=lambda x: x)
    def test_value_error_different_drives_returns_false(
        self, mock_abspath: Mock, mock_relpath: Mock
    ) -> None:
        """Should return False when ValueError raised (different drives)."""
        from ccg.git import is_path_in_repository

        result = is_path_in_repository("/path/to/file", "/different/repo")

        assert result is False


class TestCheckRemoteAccessNoOutput:
    """Test check_remote_access when remote check returns no output."""

    @patch("ccg.git.run_git_command")
    @patch("subprocess.run")
    def test_remote_access_ls_remote_no_output_returns_false(
        self, mock_subprocess: Mock, mock_run: Mock
    ) -> None:
        """Should return False when ls-remote returns non-zero but no error output."""
        from ccg.git import check_remote_access

        mock_run.return_value = (True, "origin\thttps://github.com/user/repo.git (fetch)")

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = ""
        mock_result.stdout = ""
        mock_subprocess.return_value = mock_result

        result = check_remote_access()

        assert result is False


class TestDiscardLocalChangesSecondStepFailure:
    """Test discard_local_changes when second command fails."""

    @patch("ccg.git.run_git_command")
    def test_discard_changes_checkout_fails_returns_false(self, mock_run: Mock) -> None:
        """Should return False when git checkout fails."""
        from ccg.git import discard_local_changes

        mock_run.side_effect = [
            (True, None),  # git reset HEAD succeeds
            (False, None),  # git checkout . fails
        ]

        result = discard_local_changes()

        assert result is False


class TestRunPreCommitHooksFailureReturnsFalse:
    """Test run_pre_commit_hooks failure mode."""

    @patch("subprocess.run")
    def test_pre_commit_hooks_failure_returns_false(self, mock_run: Mock) -> None:
        """Should return False when pre-commit hooks fail."""
        from ccg.git import run_pre_commit_hooks

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "Hook failed"
        mock_result.stderr = "Error details"
        mock_run.return_value = mock_result

        result = run_pre_commit_hooks(["file1.py", "file2.py"])

        assert result is False


class TestCheckHasChangesGitFailure:
    """Test check_has_changes when git command fails."""

    @patch("ccg.git.run_git_command")
    def test_check_has_changes_git_command_fails(self, mock_run: Mock) -> None:
        """Should return False when git command fails without paths."""
        from ccg.git import check_has_changes

        mock_run.return_value = (False, None)

        result = check_has_changes()

        assert result is False


class TestDeleteOldCommitWithRebaseSuccess:
    """Test delete_old_commit_with_rebase success path."""

    @patch("os.path.exists")
    @patch("os.unlink")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_success_with_cleanup(
        self, mock_create_script: Mock, mock_subprocess: Mock, mock_unlink: Mock, mock_exists: Mock
    ) -> None:
        """Should successfully delete commit and cleanup script file."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])
        mock_subprocess.return_value = Mock(returncode=0, stderr="")
        mock_exists.return_value = True

        result = delete_old_commit_with_rebase("def456")

        assert result is True
        mock_unlink.assert_called_once_with("/tmp/script")

    @patch("os.unlink")
    @patch("os.path.exists")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_success_cleanup_exception_ignored(
        self, mock_create_script: Mock, mock_subprocess: Mock, mock_exists: Mock, mock_unlink: Mock
    ) -> None:
        """Should ignore exceptions during script cleanup."""
        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])
        mock_subprocess.return_value = Mock(returncode=0, stderr="")
        mock_exists.return_value = True
        mock_unlink.side_effect = Exception("Cannot delete file")

        result = delete_old_commit_with_rebase("def456")

        assert result is True  # Should still succeed despite cleanup failure

    @patch("os.unlink")
    @patch("os.path.exists")
    @patch("ccg.git.get_copy_command_for_rebase")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_success_with_windows_batch_file_cleanup(
        self,
        mock_create_script: Mock,
        mock_subprocess: Mock,
        mock_get_copy: Mock,
        mock_exists: Mock,
        mock_unlink: Mock,
    ) -> None:
        """Should cleanup both script and batch file on Windows."""
        from pathlib import Path

        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        # Simulate Windows: get_copy_command_for_rebase returns a batch file path
        mock_batch_file = Path("/tmp/script_copy.bat")
        mock_get_copy.return_value = ("C:\\tmp\\script_copy.bat", mock_batch_file)

        # Both script and batch file exist
        mock_exists.return_value = True

        result = delete_old_commit_with_rebase("def456")

        assert result is True
        # Verify both files were deleted
        assert mock_unlink.call_count == 2
        mock_unlink.assert_any_call("/tmp/script")
        mock_unlink.assert_any_call("/tmp/script_copy.bat")

    @patch("os.unlink")
    @patch("os.path.exists")
    @patch("ccg.git.get_copy_command_for_rebase")
    @patch("subprocess.run")
    @patch("ccg.git.create_rebase_script_for_deletion")
    def test_rebase_success_with_windows_batch_file_cleanup_exception(
        self,
        mock_create_script: Mock,
        mock_subprocess: Mock,
        mock_get_copy: Mock,
        mock_exists: Mock,
        mock_unlink: Mock,
    ) -> None:
        """Should ignore exceptions during Windows batch file cleanup."""
        from pathlib import Path

        from ccg.git import delete_old_commit_with_rebase

        mock_create_script.return_value = (True, "/tmp/script", ["pick abc123 test"])
        mock_subprocess.return_value = Mock(returncode=0, stderr="")

        # Simulate Windows: get_copy_command_for_rebase returns a batch file path
        mock_batch_file = Path("/tmp/script_copy.bat")
        mock_get_copy.return_value = ("C:\\tmp\\script_copy.bat", mock_batch_file)

        # Both files exist
        mock_exists.return_value = True

        # First unlink (script file) succeeds, second unlink (batch file) fails
        mock_unlink.side_effect = [None, Exception("Permission denied")]

        result = delete_old_commit_with_rebase("def456")

        # Should still succeed despite batch file cleanup failure
        assert result is True
        # Verify both unlinks were attempted
        assert mock_unlink.call_count == 2
        mock_unlink.assert_any_call("/tmp/script")
        mock_unlink.assert_any_call("/tmp/script_copy.bat")
