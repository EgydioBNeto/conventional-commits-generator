"""Tests for the repository module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccg.repository import CommitInfo, GitRepository


class TestCommitInfo:
    """Test CommitInfo dataclass."""

    def test_commit_info_initialization(self) -> None:
        """Should initialize CommitInfo with all fields."""
        commit = CommitInfo(
            full_hash="abc123def456",
            short_hash="abc123",
            subject="feat: add feature",
            body="This is the body",
            author="John Doe",
            date="2 days ago",
        )

        assert commit.full_hash == "abc123def456"
        assert commit.short_hash == "abc123"
        assert commit.subject == "feat: add feature"
        assert commit.body == "This is the body"
        assert commit.author == "John Doe"
        assert commit.date == "2 days ago"

    def test_from_tuple(self) -> None:
        """Should create CommitInfo from 6-element tuple."""
        commit_tuple = (
            "abc123def456",
            "abc123",
            "feat: add feature",
            "This is the body",
            "John Doe",
            "2 days ago",
        )

        commit = CommitInfo.from_tuple(commit_tuple)

        assert commit.full_hash == "abc123def456"
        assert commit.short_hash == "abc123"
        assert commit.subject == "feat: add feature"
        assert commit.body == "This is the body"
        assert commit.author == "John Doe"
        assert commit.date == "2 days ago"

    def test_from_short_tuple(self) -> None:
        """Should create CommitInfo from 5-element tuple with empty body."""
        commit_tuple = (
            "abc123def456",
            "abc123",
            "feat: add feature",
            "John Doe",
            "2 days ago",
        )

        commit = CommitInfo.from_short_tuple(commit_tuple)

        assert commit.full_hash == "abc123def456"
        assert commit.short_hash == "abc123"
        assert commit.subject == "feat: add feature"
        assert commit.body == ""
        assert commit.author == "John Doe"
        assert commit.date == "2 days ago"


class TestGitRepository:
    """Test GitRepository class."""

    def test_init_default_path(self) -> None:
        """Should initialize with current working directory by default."""
        repo = GitRepository()

        assert repo.path == Path.cwd()

    def test_init_custom_path(self) -> None:
        """Should initialize with custom path."""
        custom_path = Path("/path/to/repo")
        repo = GitRepository(path=custom_path)

        assert repo.path == custom_path

    @patch("ccg.repository.run_git_command")
    def test_is_git_repo_success(self, mock_run_git: MagicMock) -> None:
        """Should return True if inside git repository."""
        mock_run_git.return_value = (True, "true")

        repo = GitRepository()
        result = repo.is_git_repo()

        assert result is True
        mock_run_git.assert_called_once()
        assert "rev-parse" in mock_run_git.call_args[0][0]
        assert "--is-inside-work-tree" in mock_run_git.call_args[0][0]

    @patch("ccg.repository.run_git_command")
    def test_is_git_repo_failure(self, mock_run_git: MagicMock) -> None:
        """Should return False if not inside git repository."""
        mock_run_git.return_value = (False, None)

        repo = GitRepository()
        result = repo.is_git_repo()

        assert result is False

    @patch("ccg.git.check_has_changes")
    def test_has_changes_no_paths(self, mock_check: MagicMock) -> None:
        """Should check for changes in entire repository."""
        mock_check.return_value = True

        repo = GitRepository()
        result = repo.has_changes()

        assert result is True
        mock_check.assert_called_once_with(None)

    @patch("ccg.git.check_has_changes")
    def test_has_changes_with_paths(self, mock_check: MagicMock) -> None:
        """Should check for changes in specific paths."""
        mock_check.return_value = False
        paths = ["file1.txt", "file2.txt"]

        repo = GitRepository()
        result = repo.has_changes(paths)

        assert result is False
        mock_check.assert_called_once_with(paths)

    @patch("ccg.repository._get_current_branch")
    def test_get_current_branch(self, mock_get_branch: MagicMock) -> None:
        """Should get current branch name."""
        mock_get_branch.return_value = "main"

        repo = GitRepository()
        result = repo.get_current_branch()

        assert result == "main"
        mock_get_branch.assert_called_once()

    @patch("ccg.repository._get_current_branch")
    def test_get_current_branch_none(self, mock_get_branch: MagicMock) -> None:
        """Should return None if unable to determine branch."""
        mock_get_branch.return_value = None

        repo = GitRepository()
        result = repo.get_current_branch()

        assert result is None

    @patch("ccg.repository._get_repository_name")
    def test_get_repository_name(self, mock_get_name: MagicMock) -> None:
        """Should get repository name."""
        mock_get_name.return_value = "my-repo"

        repo = GitRepository()
        result = repo.get_repository_name()

        assert result == "my-repo"
        mock_get_name.assert_called_once()

    @patch("ccg.repository._get_repository_root")
    def test_get_repository_root(self, mock_get_root: MagicMock) -> None:
        """Should get repository root directory."""
        mock_get_root.return_value = "/path/to/repo"

        repo = GitRepository()
        result = repo.get_repository_root()

        assert result == "/path/to/repo"
        mock_get_root.assert_called_once()

    @patch("ccg.repository._get_remote_name")
    def test_get_remote_name(self, mock_get_remote: MagicMock) -> None:
        """Should get remote name."""
        mock_get_remote.return_value = "origin"

        repo = GitRepository()
        result = repo.get_remote_name()

        assert result == "origin"
        mock_get_remote.assert_called_once()

    @patch("ccg.repository._branch_exists_on_remote")
    def test_branch_exists_on_remote_true(self, mock_branch_exists: MagicMock) -> None:
        """Should return True if branch exists on remote."""
        mock_branch_exists.return_value = True

        repo = GitRepository()
        result = repo.branch_exists_on_remote("feature-branch")

        assert result is True
        mock_branch_exists.assert_called_once_with("feature-branch")

    @patch("ccg.repository._branch_exists_on_remote")
    def test_branch_exists_on_remote_false(self, mock_branch_exists: MagicMock) -> None:
        """Should return False if branch does not exist on remote."""
        mock_branch_exists.return_value = False

        repo = GitRepository()
        result = repo.branch_exists_on_remote("new-branch")

        assert result is False

    @patch("ccg.repository._get_staged_files")
    def test_get_staged_files(self, mock_get_staged: MagicMock) -> None:
        """Should get list of staged files."""
        mock_get_staged.return_value = ["file1.txt", "file2.py"]

        repo = GitRepository()
        result = repo.get_staged_files()

        assert result == ["file1.txt", "file2.py"]
        mock_get_staged.assert_called_once()

    @patch("ccg.repository._get_staged_files")
    def test_get_staged_files_empty(self, mock_get_staged: MagicMock) -> None:
        """Should return empty list if no files staged."""
        mock_get_staged.return_value = []

        repo = GitRepository()
        result = repo.get_staged_files()

        assert result == []

    @patch("ccg.repository._get_staged_file_changes")
    def test_get_staged_file_changes(self, mock_get_changes: MagicMock) -> None:
        """Should get list of staged file changes with status."""
        mock_get_changes.return_value = [
            ("A", "new_file.txt"),
            ("M", "modified_file.py"),
        ]

        repo = GitRepository()
        result = repo.get_staged_file_changes()

        assert result == [("A", "new_file.txt"), ("M", "modified_file.py")]
        mock_get_changes.assert_called_once()

    @patch("ccg.repository._get_recent_commits")
    def test_get_recent_commits_with_count(self, mock_get_commits: MagicMock) -> None:
        """Should get specific number of recent commits."""
        mock_get_commits.return_value = [
            ("abc123", "abc12", "feat: feature 1", "Author 1", "1 day ago"),
            ("def456", "def45", "fix: bug fix", "Author 2", "2 days ago"),
        ]

        repo = GitRepository()
        result = repo.get_recent_commits(count=2)

        assert len(result) == 2
        assert isinstance(result[0], CommitInfo)
        assert result[0].full_hash == "abc123"
        assert result[0].short_hash == "abc12"
        assert result[0].subject == "feat: feature 1"
        assert result[0].body == ""
        assert result[0].author == "Author 1"
        assert result[0].date == "1 day ago"
        mock_get_commits.assert_called_once_with(2)

    @patch("ccg.repository._get_recent_commits")
    def test_get_recent_commits_all(self, mock_get_commits: MagicMock) -> None:
        """Should get all commits if count not specified."""
        mock_get_commits.return_value = [
            ("abc123", "abc12", "feat: feature", "Author", "1 day ago"),
        ]

        repo = GitRepository()
        result = repo.get_recent_commits()

        assert len(result) == 1
        mock_get_commits.assert_called_once_with(None)

    @patch("ccg.repository._get_commit_by_hash")
    def test_get_commit_by_hash_found(self, mock_get_commit: MagicMock) -> None:
        """Should get commit details by hash."""
        mock_get_commit.return_value = (
            "abc123def456",
            "abc123",
            "feat: new feature",
            "This is the body\nwith multiple lines",
            "John Doe",
            "2 days ago",
        )

        repo = GitRepository()
        result = repo.get_commit_by_hash("abc123")

        assert result is not None
        assert isinstance(result, CommitInfo)
        assert result.full_hash == "abc123def456"
        assert result.short_hash == "abc123"
        assert result.subject == "feat: new feature"
        assert result.body == "This is the body\nwith multiple lines"
        assert result.author == "John Doe"
        assert result.date == "2 days ago"
        mock_get_commit.assert_called_once_with("abc123")

    @patch("ccg.repository._get_commit_by_hash")
    def test_get_commit_by_hash_not_found(self, mock_get_commit: MagicMock) -> None:
        """Should return None if commit not found."""
        mock_get_commit.return_value = None

        repo = GitRepository()
        result = repo.get_commit_by_hash("nonexistent")

        assert result is None

    @patch("ccg.repository._git_add")
    def test_add_no_paths(self, mock_git_add: MagicMock) -> None:
        """Should stage all changes if no paths specified."""
        mock_git_add.return_value = True

        repo = GitRepository()
        result = repo.add()

        assert result is True
        mock_git_add.assert_called_once_with(None)

    @patch("ccg.repository._git_add")
    def test_add_with_paths(self, mock_git_add: MagicMock) -> None:
        """Should stage specific paths."""
        mock_git_add.return_value = True
        paths = ["file1.txt", "dir/"]

        repo = GitRepository()
        result = repo.add(paths)

        assert result is True
        mock_git_add.assert_called_once_with(paths)

    @patch("ccg.repository._git_add")
    def test_add_failure(self, mock_git_add: MagicMock) -> None:
        """Should return False on staging failure."""
        mock_git_add.return_value = False

        repo = GitRepository()
        result = repo.add()

        assert result is False

    @patch("ccg.repository._git_commit")
    def test_commit_success(self, mock_git_commit: MagicMock) -> None:
        """Should create commit with message."""
        mock_git_commit.return_value = True

        repo = GitRepository()
        result = repo.commit("feat: new feature")

        assert result is True
        mock_git_commit.assert_called_once_with("feat: new feature")

    @patch("ccg.repository._git_commit")
    def test_commit_failure(self, mock_git_commit: MagicMock) -> None:
        """Should return False on commit failure."""
        mock_git_commit.return_value = False

        repo = GitRepository()
        result = repo.commit("feat: feature")

        assert result is False

    @patch("ccg.repository._git_push")
    def test_push_default(self, mock_git_push: MagicMock) -> None:
        """Should push with default flags."""
        mock_git_push.return_value = True

        repo = GitRepository()
        result = repo.push()

        assert result is True
        mock_git_push.assert_called_once_with(set_upstream=False, force=False)

    @patch("ccg.repository._git_push")
    def test_push_set_upstream(self, mock_git_push: MagicMock) -> None:
        """Should push with set-upstream flag."""
        mock_git_push.return_value = True

        repo = GitRepository()
        result = repo.push(set_upstream=True)

        assert result is True
        mock_git_push.assert_called_once_with(set_upstream=True, force=False)

    @patch("ccg.repository._git_push")
    def test_push_force(self, mock_git_push: MagicMock) -> None:
        """Should push with force flag."""
        mock_git_push.return_value = True

        repo = GitRepository()
        result = repo.push(force=True)

        assert result is True
        mock_git_push.assert_called_once_with(set_upstream=False, force=True)

    @patch("ccg.repository._git_push")
    def test_push_set_upstream_and_force(self, mock_git_push: MagicMock) -> None:
        """Should push with both flags."""
        mock_git_push.return_value = True

        repo = GitRepository()
        result = repo.push(set_upstream=True, force=True)

        assert result is True
        mock_git_push.assert_called_once_with(set_upstream=True, force=True)

    @patch("ccg.repository._git_push")
    def test_push_failure(self, mock_git_push: MagicMock) -> None:
        """Should return False on push failure."""
        mock_git_push.return_value = False

        repo = GitRepository()
        result = repo.push()

        assert result is False

    @patch("ccg.repository._pull_from_remote")
    def test_pull_success(self, mock_pull: MagicMock) -> None:
        """Should pull from remote successfully."""
        mock_pull.return_value = True

        repo = GitRepository()
        result = repo.pull()

        assert result is True
        mock_pull.assert_called_once()

    @patch("ccg.repository._pull_from_remote")
    def test_pull_failure(self, mock_pull: MagicMock) -> None:
        """Should return False on pull failure."""
        mock_pull.return_value = False

        repo = GitRepository()
        result = repo.pull()

        assert result is False

    @patch("ccg.repository._create_tag")
    def test_create_tag_lightweight(self, mock_create_tag: MagicMock) -> None:
        """Should create lightweight tag."""
        mock_create_tag.return_value = True

        repo = GitRepository()
        result = repo.create_tag("v1.0.0")

        assert result is True
        mock_create_tag.assert_called_once_with("v1.0.0", None)

    @patch("ccg.repository._create_tag")
    def test_create_tag_annotated(self, mock_create_tag: MagicMock) -> None:
        """Should create annotated tag with message."""
        mock_create_tag.return_value = True

        repo = GitRepository()
        result = repo.create_tag("v1.0.0", "Release v1.0.0")

        assert result is True
        mock_create_tag.assert_called_once_with("v1.0.0", "Release v1.0.0")

    @patch("ccg.repository._create_tag")
    def test_create_tag_failure(self, mock_create_tag: MagicMock) -> None:
        """Should return False on tag creation failure."""
        mock_create_tag.return_value = False

        repo = GitRepository()
        result = repo.create_tag("v1.0.0")

        assert result is False

    @patch("ccg.repository._push_tag")
    def test_push_tag_success(self, mock_push_tag: MagicMock) -> None:
        """Should push tag to remote."""
        mock_push_tag.return_value = True

        repo = GitRepository()
        result = repo.push_tag("v1.0.0")

        assert result is True
        mock_push_tag.assert_called_once_with("v1.0.0")

    @patch("ccg.repository._push_tag")
    def test_push_tag_failure(self, mock_push_tag: MagicMock) -> None:
        """Should return False on tag push failure."""
        mock_push_tag.return_value = False

        repo = GitRepository()
        result = repo.push_tag("v1.0.0")

        assert result is False

    @patch("ccg.repository._edit_commit_message")
    def test_edit_commit_message_subject_only(self, mock_edit: MagicMock) -> None:
        """Should edit commit message with subject only."""
        mock_edit.return_value = True

        repo = GitRepository()
        result = repo.edit_commit_message("abc123", "fix: corrected bug")

        assert result is True
        mock_edit.assert_called_once_with("abc123", "fix: corrected bug", None)

    @patch("ccg.repository._edit_commit_message")
    def test_edit_commit_message_with_body(self, mock_edit: MagicMock) -> None:
        """Should edit commit message with subject and body."""
        mock_edit.return_value = True

        repo = GitRepository()
        result = repo.edit_commit_message("abc123", "fix: corrected bug", "This is the body")

        assert result is True
        mock_edit.assert_called_once_with("abc123", "fix: corrected bug", "This is the body")

    @patch("ccg.repository._edit_commit_message")
    def test_edit_commit_message_failure(self, mock_edit: MagicMock) -> None:
        """Should return False on edit failure."""
        mock_edit.return_value = False

        repo = GitRepository()
        result = repo.edit_commit_message("abc123", "new message")

        assert result is False

    @patch("ccg.repository._delete_commit")
    def test_delete_commit_success(self, mock_delete: MagicMock) -> None:
        """Should delete commit by hash."""
        mock_delete.return_value = True

        repo = GitRepository()
        result = repo.delete_commit("abc123")

        assert result is True
        mock_delete.assert_called_once_with("abc123")

    @patch("ccg.repository._delete_commit")
    def test_delete_commit_failure(self, mock_delete: MagicMock) -> None:
        """Should return False on delete failure."""
        mock_delete.return_value = False

        repo = GitRepository()
        result = repo.delete_commit("abc123")

        assert result is False

    @patch("ccg.repository._discard_local_changes")
    def test_discard_local_changes_success(self, mock_discard: MagicMock) -> None:
        """Should discard all local changes."""
        mock_discard.return_value = True

        repo = GitRepository()
        result = repo.discard_local_changes()

        assert result is True
        mock_discard.assert_called_once()

    @patch("ccg.repository._discard_local_changes")
    def test_discard_local_changes_failure(self, mock_discard: MagicMock) -> None:
        """Should return False on discard failure."""
        mock_discard.return_value = False

        repo = GitRepository()
        result = repo.discard_local_changes()

        assert result is False

    @patch("ccg.repository.invalidate_repository_cache")
    def test_invalidate_cache(self, mock_invalidate: MagicMock) -> None:
        """Should invalidate repository cache."""
        repo = GitRepository()
        repo.invalidate_cache()

        mock_invalidate.assert_called_once()


class TestGitRepositoryIntegration:
    """Integration tests for GitRepository with mocked git commands."""

    @patch("ccg.repository.run_git_command")
    @patch("ccg.repository._git_add")
    @patch("ccg.repository._git_commit")
    @patch("ccg.repository._git_push")
    def test_full_commit_workflow(
        self,
        mock_push: MagicMock,
        mock_commit: MagicMock,
        mock_add: MagicMock,
        mock_run_git: MagicMock,
    ) -> None:
        """Should perform full add-commit-push workflow."""
        # Setup mocks
        mock_run_git.return_value = (True, "true")
        mock_add.return_value = True
        mock_commit.return_value = True
        mock_push.return_value = True

        # Execute workflow
        repo = GitRepository()
        assert repo.is_git_repo()
        assert repo.add()
        assert repo.commit("feat: new feature")
        assert repo.push()

        # Verify all steps called
        mock_add.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_called_once()

    @patch("ccg.repository._get_recent_commits")
    @patch("ccg.repository._get_commit_by_hash")
    @patch("ccg.repository._edit_commit_message")
    def test_edit_workflow(
        self,
        mock_edit: MagicMock,
        mock_get_commit: MagicMock,
        mock_get_recent: MagicMock,
    ) -> None:
        """Should perform commit listing and editing workflow."""
        # Setup mocks
        mock_get_recent.return_value = [
            ("abc123", "abc12", "feat: feature", "Author", "1 day ago"),
        ]
        mock_get_commit.return_value = (
            "abc123",
            "abc12",
            "feat: feature",
            "",
            "Author",
            "1 day ago",
        )
        mock_edit.return_value = True

        # Execute workflow
        repo = GitRepository()
        commits = repo.get_recent_commits(1)
        assert len(commits) == 1

        commit_hash = commits[0].full_hash
        commit_detail = repo.get_commit_by_hash(commit_hash)
        assert commit_detail is not None

        result = repo.edit_commit_message(commit_hash, "fix: corrected feature")
        assert result is True

        # Verify
        mock_get_recent.assert_called_once_with(1)
        mock_get_commit.assert_called_once_with("abc123")
        mock_edit.assert_called_once()
