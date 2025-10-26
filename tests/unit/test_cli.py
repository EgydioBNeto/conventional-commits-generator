"""Unit tests for cli.py module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ccg.cli import (
    handle_analyze,
    handle_push_only,
    handle_reset,
    handle_tag,
    parse_args,
    show_repository_info,
    validate_paths_exist,
)


class TestArgumentParsing:
    """Tests for command-line argument parsing."""

    def test_parse_no_args(self) -> None:
        """Should parse with no arguments."""
        args = parse_args([])

        assert args.push is False
        assert args.commit is False
        assert args.edit is False
        assert args.delete is False
        assert args.tag is False
        assert args.reset is False
        assert args.analyze is False
        assert args.path is None

    @pytest.mark.parametrize(
        "flag_name",
        ["push", "commit", "edit", "delete", "tag", "reset", "analyze"],
    )
    def test_parse_operation_flags(self, flag_name: str) -> None:
        """Should parse operation flags."""
        args = parse_args([f"--{flag_name}"])
        assert getattr(args, flag_name) is True

    def test_parse_single_path(self) -> None:
        """Should parse --path with single argument."""
        args = parse_args(["--path", "src/"])
        assert args.path == ["src/"]

    def test_parse_multiple_paths(self) -> None:
        """Should parse --path with multiple arguments."""
        args = parse_args(["--path", "src/", "tests/", "README.md"])
        assert args.path == ["src/", "tests/", "README.md"]

    def test_parse_combined_flags(self) -> None:
        """Should parse combined flags."""
        args = parse_args(["--commit", "--path", "src/"])
        assert args.commit is True
        assert args.path == ["src/"]

    def test_parse_unknown_args_exits(self) -> None:
        """Should exit on unknown arguments."""
        import sys

        with patch.object(sys, "exit") as mock_exit:
            parse_args(["--unknown"])
            mock_exit.assert_called_once_with(1)

    def test_parse_verbose_flag(self) -> None:
        """Should parse --verbose flag."""
        args = parse_args(["--verbose"])
        assert args.verbose is True

    def test_parse_verbose_short_flag(self) -> None:
        """Should parse -v short flag for verbose."""
        args = parse_args(["-v"])
        assert args.verbose is True

    def test_parse_no_verbose_defaults_to_false(self) -> None:
        """Should default verbose to False when not specified."""
        args = parse_args([])
        assert args.verbose is False

    def test_parse_path_flag_twice_exits(self) -> None:
        """Should exit when --path flag is used twice."""
        import sys

        with patch.object(sys, "stderr"):
            with pytest.raises(SystemExit) as exc_info:
                parse_args(["--path", "src/", "--path", "tests/"])
            assert exc_info.value.code == 2  # argparse error code

    def test_parse_path_with_multiple_operation_flags_exits(self) -> None:
        """Should exit when --path is used with more than one operation flag."""
        import sys

        with patch.object(sys, "exit") as mock_exit:
            parse_args(["--path", "src/", "--push", "--edit"])
            mock_exit.assert_called_once_with(1)

    def test_parse_path_with_one_operation_flag_succeeds(self) -> None:
        """Should succeed when --path is used with one operation flag."""
        args = parse_args(["--path", "src/", "--push"])
        assert args.path == ["src/"]
        assert args.push is True

    def test_parse_path_with_operation_and_verbose_succeeds(self) -> None:
        """Should succeed when --path is used with one operation flag and --verbose."""
        args = parse_args(["--path", "src/", "--push", "--verbose"])
        assert args.path == ["src/"]
        assert args.push is True
        assert args.verbose is True


class TestRepositoryInfo:
    """Tests for repository information display."""

    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.get_repository_name")
    def test_show_repo_and_branch(self, mock_repo: Mock, mock_branch: Mock) -> None:
        """Should display repository name and branch."""
        mock_repo.return_value = "my-project"
        mock_branch.return_value = "main"

        show_repository_info()

        mock_repo.assert_called_once()
        mock_branch.assert_called_once()

    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.get_repository_name")
    def test_show_info_with_none_values(
        self, mock_repo: Mock, mock_branch: Mock
    ) -> None:
        """Should handle None repository name and branch gracefully."""
        mock_repo.return_value = None
        mock_branch.return_value = None

        # Should not raise exception
        show_repository_info()


class TestPathValidation:
    """Tests for path validation."""

    @patch("os.path.exists")
    def test_validate_all_paths_exist(self, mock_exists: Mock) -> None:
        """Should pass when all paths exist."""
        mock_exists.return_value = True

        # Should not raise or exit
        validate_paths_exist(["file1.txt", "file2.py"])

    @patch("os.path.exists")
    def test_validate_empty_paths(self, mock_exists: Mock) -> None:
        """Should pass with empty path list."""
        # Should not raise or exit
        validate_paths_exist([])

    @patch("os.path.exists")
    @patch("ccg.cli.print_error")
    def test_validate_nonexistent_path(
        self, mock_error: Mock, mock_exists: Mock
    ) -> None:
        """Should exit when path doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(SystemExit):
            validate_paths_exist(["nonexistent.txt"])

        mock_error.assert_called()


class TestNoDuplicatePathsValidation:
    """Tests for duplicate paths validation."""

    def test_validate_no_duplicates(self) -> None:
        """Should pass when there are no duplicate paths."""
        from ccg.cli import validate_no_duplicate_paths

        # Should not raise or exit
        validate_no_duplicate_paths(["file1.txt", "file2.py", "src/"])

    def test_validate_empty_paths(self) -> None:
        """Should pass with empty path list."""
        from ccg.cli import validate_no_duplicate_paths

        # Should not raise or exit
        validate_no_duplicate_paths([])

    @patch("ccg.cli.print_error")
    def test_validate_exact_duplicate(self, mock_error: Mock) -> None:
        """Should exit when exact duplicate paths are found."""
        from ccg.cli import validate_no_duplicate_paths

        with pytest.raises(SystemExit):
            validate_no_duplicate_paths(["file.txt", "file.txt"])

        mock_error.assert_called()

    @patch("os.path.abspath")
    @patch("ccg.cli.print_error")
    def test_validate_normalized_duplicate(
        self, mock_error: Mock, mock_abspath: Mock
    ) -> None:
        """Should exit when normalized paths are duplicates (e.g., . and .)."""
        from ccg.cli import validate_no_duplicate_paths

        # Mock abspath to return the same path for both
        mock_abspath.return_value = "/absolute/path"

        with pytest.raises(SystemExit):
            validate_no_duplicate_paths([".", "."])

        mock_error.assert_called()

    @patch("ccg.cli.print_error")
    def test_validate_multiple_duplicates(self, mock_error: Mock) -> None:
        """Should exit when multiple duplicates are found."""
        from ccg.cli import validate_no_duplicate_paths

        with pytest.raises(SystemExit):
            validate_no_duplicate_paths(
                ["file.txt", "other.py", "file.txt", "other.py"]
            )

        mock_error.assert_called()


class TestPushOnlyWorkflow:
    """Tests for push-only workflow."""

    @patch("ccg.cli.has_commits_to_push")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.git_push")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_success(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_push: Mock,
        mock_branch: Mock,
        mock_remote: Mock,
        mock_get_branch: Mock,
        mock_has_commits: Mock,
    ) -> None:
        """Should push successfully."""
        mock_check.return_value = True
        mock_remote.return_value = True
        mock_get_branch.return_value = "main"
        mock_branch.return_value = True  # Branch exists on remote
        mock_has_commits.return_value = True  # Has commits to push
        mock_push.return_value = True

        result = handle_push_only()

        assert result == 0
        mock_push.assert_called_once()

    @patch("ccg.cli.has_commits_to_push")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.git_push")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_failure(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_push: Mock,
        mock_branch: Mock,
        mock_remote: Mock,
        mock_get_branch: Mock,
        mock_has_commits: Mock,
    ) -> None:
        """Should return error code on push failure."""
        mock_check.return_value = True
        mock_remote.return_value = True
        mock_get_branch.return_value = "main"
        mock_branch.return_value = True  # Branch exists on remote
        mock_has_commits.return_value = True  # Has commits to push
        mock_push.return_value = False

        result = handle_push_only()

        assert result == 1


class TestTagWorkflow:
    """Tests for tag creation workflow."""

    @patch("ccg.cli._get_commit_selection")
    @patch("ccg.cli._display_commits_list")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.create_tag")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_create_lightweight_tag(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_confirm: Mock,
        mock_input: Mock,
        mock_create: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
        mock_count_input: Mock,
        mock_get_commits: Mock,
        mock_display: Mock,
        mock_selection: Mock,
    ) -> None:
        """Should create lightweight tag on selected commit."""
        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            ("abc123", "abc12", "feat: test", "Author", "2024-01-01")
        ]
        mock_selection.return_value = "abc123"
        mock_input.return_value = "v1.0.0"
        mock_confirm.side_effect = [
            False,
            False,
        ]  # Not annotated (1st), don't push (2nd)
        mock_create.return_value = True

        result = handle_tag()

        assert result == 0
        mock_create.assert_called_once_with("v1.0.0", None, "abc123")

    @patch("ccg.cli._get_commit_selection")
    @patch("ccg.cli._display_commits_list")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.push_tag")
    @patch("ccg.cli.create_tag")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_create_annotated_tag_and_push(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_confirm: Mock,
        mock_input: Mock,
        mock_create: Mock,
        mock_push: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
        mock_count_input: Mock,
        mock_get_commits: Mock,
        mock_display: Mock,
        mock_selection: Mock,
    ) -> None:
        """Should create annotated tag on selected commit and push."""
        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            ("def456", "def45", "fix: bug", "Author", "2024-01-02")
        ]
        mock_selection.return_value = "def456"
        mock_input.side_effect = ["v1.0.0", "Release version 1.0.0"]
        mock_confirm.side_effect = [True, True]  # Annotated (1st), push (2nd)
        mock_create.return_value = True
        mock_push.return_value = True

        result = handle_tag()

        assert result == 0
        mock_create.assert_called_once_with("v1.0.0", "Release version 1.0.0", "def456")
        mock_push.assert_called_once()

    @patch("ccg.cli._get_commit_selection")
    @patch("ccg.cli._display_commits_list")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.create_tag")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_validation_loop(
        self,
        mock_show,
        mock_check,
        mock_confirm,
        mock_input,
        mock_create,
        mock_remote,
        mock_has_changes,
        mock_count_input,
        mock_get_commits,
        mock_display,
        mock_selection,
        capsys,
    ):
        """Should reject invalid tag format and then accept a valid one."""
        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            ("ghi789", "ghi78", "docs: update", "Author", "2024-01-03")
        ]
        mock_selection.return_value = "ghi789"
        mock_input.side_effect = ["invalid-tag", "v1.2.3"]
        mock_confirm.return_value = False  # Don't create annotated, don't push
        mock_create.return_value = True

        result = handle_tag()

        assert result == 0
        captured = capsys.readouterr()
        assert "Invalid tag format" in captured.out
        mock_create.assert_called_once_with("v1.2.3", None, "ghi789")

    @patch("ccg.cli._get_commit_selection")
    @patch("ccg.cli._display_commits_list")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_cancelled_by_user(
        self,
        mock_show,
        mock_check,
        mock_remote,
        mock_has_changes,
        mock_count_input,
        mock_get_commits,
        mock_display,
        mock_selection,
    ):
        """Should return 0 when user cancels commit selection."""
        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            ("abc123", "abc12", "feat: test", "Author", "2024-01-01")
        ]
        mock_selection.return_value = None  # User cancelled

        result = handle_tag()

        assert result == 0

    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_no_commits_found(
        self,
        mock_show,
        mock_check,
        mock_remote,
        mock_has_changes,
        mock_count_input,
        mock_get_commits,
    ):
        """Should return 1 when no commits are found."""
        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = []  # No commits

        result = handle_tag()

        assert result == 1


class TestResetWorkflow:
    """Tests for reset and pull workflow."""

    @patch("ccg.cli.pull_from_remote")
    @patch("ccg.cli.discard_local_changes")
    @patch("ccg.cli.confirm_reset")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_reset_confirmed(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
        mock_confirm: Mock,
        mock_discard: Mock,
        mock_pull: Mock,
    ) -> None:
        """Should reset local changes and pull when confirmed."""
        mock_check.return_value = True
        mock_remote.return_value = True
        mock_has_changes.return_value = True
        mock_confirm.return_value = True
        mock_discard.return_value = True
        mock_pull.return_value = True

        result = handle_reset()

        assert result == 0
        mock_discard.assert_called_once()
        mock_pull.assert_called_once()

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_reset_cancelled(
        self, mock_show: Mock, mock_check: Mock, mock_confirm: Mock
    ) -> None:
        """Should cancel reset when user declines."""
        mock_check.return_value = True
        mock_confirm.return_value = False

        result = handle_reset()

        assert result == 0


class TestHandleCommitOperation:
    """Tests for handle_commit_operation function."""

    @patch("ccg.cli.edit_specific_commit")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_edit_by_number(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_has_changes: Mock,
        mock_commits: Mock,
        mock_input: Mock,
        mock_edit: Mock,
    ) -> None:
        """Should select commit by number for editing."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_has_changes.return_value = False  # No uncommitted changes
        mock_commits.return_value = [
            ("abc123", "abc", "feat: test", "Author", "1 day ago"),
            ("def456", "def", "fix: bug", "Author", "2 days ago"),
        ]
        mock_input.side_effect = ["", "1"]  # First for count, then for selection
        mock_edit.return_value = 0

        result = handle_commit_operation("edit")

        assert result == 0
        mock_edit.assert_called_once_with("abc123")

    @patch("ccg.cli.delete_specific_commit")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_delete_by_hash(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_has_changes: Mock,
        mock_commits: Mock,
        mock_input: Mock,
        mock_delete: Mock,
    ) -> None:
        """Should select commit by hash for deleting."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_has_changes.return_value = False  # No uncommitted changes
        mock_commits.return_value = [
            ("abc123", "abc", "feat: test", "Author", "1 day ago"),
            ("def456", "def", "fix: bug", "Author", "2 days ago"),
        ]
        mock_input.side_effect = ["5", "abc"]  # Count=5, hash starting with 'abc'
        mock_delete.return_value = 0

        result = handle_commit_operation("delete")

        assert result == 0
        mock_delete.assert_called_once_with("abc123")

    @patch("ccg.cli.read_input")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_quit_operation(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_has_changes: Mock,
        mock_commits: Mock,
        mock_input: Mock,
    ) -> None:
        """Should quit on 'q' input."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_has_changes.return_value = False  # No uncommitted changes
        mock_commits.return_value = [
            ("abc123", "abc", "feat: test", "Author", "1 day ago")
        ]
        mock_input.side_effect = ["", "q"]

        result = handle_commit_operation("edit")

        assert result == 0

    @patch("ccg.cli.read_input")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_invalid_then_valid_selection(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_has_changes: Mock,
        mock_commits: Mock,
        mock_input: Mock,
    ) -> None:
        """Should retry on invalid selection."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_has_changes.return_value = False  # No uncommitted changes
        mock_commits.return_value = [
            ("abc123", "abc", "feat: test", "Author", "1 day ago")
        ]
        mock_input.side_effect = ["", "999", "1"]  # Invalid number, then valid

        with patch("ccg.cli.edit_specific_commit", return_value=0):
            result = handle_commit_operation("edit")

        assert result == 0

    @patch("ccg.cli.edit_specific_commit")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_multiple_matching_hashes(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_has_changes: Mock,
        mock_commits: Mock,
        mock_input: Mock,
        mock_edit: Mock,
        capsys,
    ) -> None:
        """Should show error for ambiguous hash and retry."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_has_changes.return_value = False  # No uncommitted changes
        mock_commits.return_value = [
            ("abc1234", "abc1", "feat: one", "Author", "1 day ago"),
            ("abc5678", "abc5", "feat: two", "Author", "2 days ago"),
        ]
        # First input is ambiguous, second is specific
        mock_input.side_effect = ["", "abc", "abc1234"]
        mock_edit.return_value = 0

        result = handle_commit_operation("edit")

        assert result == 0
        captured = capsys.readouterr()
        assert "Multiple commits match this hash" in captured.out
        mock_edit.assert_called_once_with("abc1234")

    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_edit_blocked_by_uncommitted_changes(
        self, mock_show: Mock, mock_check: Mock, mock_has_changes: Mock, capsys
    ) -> None:
        """Should block edit operation when there are uncommitted changes."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_has_changes.return_value = True  # Uncommitted changes exist

        result = handle_commit_operation("edit")

        assert result == 1
        captured = capsys.readouterr()
        assert "Cannot proceed: You have uncommitted changes" in captured.out
        assert "Please commit or stash your changes" in captured.out

    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_delete_blocked_by_uncommitted_changes(
        self, mock_show: Mock, mock_check: Mock, mock_has_changes: Mock, capsys
    ) -> None:
        """Should block delete operation when there are uncommitted changes."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_has_changes.return_value = True  # Uncommitted changes exist

        result = handle_commit_operation("delete")

        assert result == 1
        captured = capsys.readouterr()
        assert "Cannot proceed: You have uncommitted changes" in captured.out
        assert "Please commit or stash your changes" in captured.out


class TestEditSpecificCommit:
    """Tests for edit_specific_commit function."""

    @patch("ccg.cli.handle_push_after_edit")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.edit_commit_message")
    @patch("ccg.cli.confirm_commit_edit")
    @patch("ccg.cli.handle_commit_edit_input")
    @patch("ccg.cli.get_commit_by_hash")
    def test_edit_and_push(
        self,
        mock_get: Mock,
        mock_input: Mock,
        mock_confirm: Mock,
        mock_edit: Mock,
        mock_push_confirm: Mock,
        mock_handle_push: Mock,
    ) -> None:
        """Should edit commit and push."""
        from ccg.cli import edit_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: old",
            "",
            "Author",
            "1 day ago",
        )
        mock_input.return_value = ("feat: new", None)
        mock_confirm.return_value = True
        mock_edit.return_value = True
        mock_push_confirm.return_value = True
        mock_handle_push.return_value = 0

        result = edit_specific_commit("abc123")

        assert result == 0
        mock_edit.assert_called_once()
        mock_handle_push.assert_called_once()

    @patch("ccg.cli.handle_commit_edit_input")
    @patch("ccg.cli.get_commit_by_hash")
    def test_edit_cancelled(self, mock_get: Mock, mock_input: Mock) -> None:
        """Should return 0 when edit is cancelled."""
        from ccg.cli import edit_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: test",
            "",
            "Author",
            "1 day ago",
        )
        mock_input.return_value = (None, None)  # User cancelled

        result = edit_specific_commit("abc123")

        assert result == 0

    @patch("ccg.cli.get_commit_by_hash")
    def test_commit_not_found(self, mock_get: Mock) -> None:
        """Should return 1 when commit not found."""
        from ccg.cli import edit_specific_commit

        mock_get.return_value = None

        result = edit_specific_commit("invalid")

        assert result == 1


class TestDeleteSpecificCommit:
    """Tests for delete_specific_commit function."""

    @patch("ccg.cli.handle_push_after_edit")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.delete_commit")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.get_commit_by_hash")
    def test_delete_and_push(
        self,
        mock_get: Mock,
        mock_confirm: Mock,
        mock_delete: Mock,
        mock_push_confirm: Mock,
        mock_handle_push: Mock,
    ) -> None:
        """Should delete commit and push."""
        from ccg.cli import delete_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: test",
            "",
            "Author",
            "1 day ago",
        )
        mock_confirm.return_value = True
        mock_delete.return_value = True
        mock_push_confirm.return_value = True
        mock_handle_push.return_value = 0

        result = delete_specific_commit("abc123")

        assert result == 0
        mock_delete.assert_called_once()

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.get_commit_by_hash")
    def test_delete_cancelled(self, mock_get: Mock, mock_confirm: Mock) -> None:
        """Should return 0 when delete is cancelled."""
        from ccg.cli import delete_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: test",
            "",
            "Author",
            "1 day ago",
        )
        mock_confirm.return_value = False

        result = delete_specific_commit("abc123")

        assert result == 0


class TestHandleGitWorkflow:
    """Tests for handle_git_workflow function."""

    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.git_commit")
    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_full_workflow_success(
        self,
        mock_validate: Mock,
        mock_add: Mock,
        mock_precommit: Mock,
        mock_generate: Mock,
        mock_commit: Mock,
        mock_confirm_push: Mock,
    ) -> None:
        """Should execute full workflow successfully."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = True
        mock_generate.return_value = "feat: test commit"
        mock_commit.return_value = True
        mock_confirm_push.return_value = False  # Don't push

        result = handle_git_workflow()

        assert result == 0
        mock_validate.assert_called_once()
        mock_add.assert_called_once()
        mock_commit.assert_called_once()

    @patch("ccg.cli.validate_repository_state")
    def test_workflow_validation_fails(self, mock_validate: Mock) -> None:
        """Should return 1 if validation fails."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = False

        result = handle_git_workflow()

        assert result == 1

    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_staging_fails(self, mock_validate: Mock, mock_add: Mock) -> None:
        """Should return 1 if staging fails."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = False

        result = handle_git_workflow()

        assert result == 1

    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_precommit_fails(
        self, mock_validate: Mock, mock_add: Mock, mock_precommit: Mock
    ) -> None:
        """Should return 1 if pre-commit fails."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = False

        result = handle_git_workflow()

        assert result == 1

    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_commit_only_mode(
        self, mock_validate: Mock, mock_generate: Mock
    ) -> None:
        """Should handle --commit flag (generate only, no commit)."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_generate.return_value = "feat: test"

        result = handle_git_workflow(commit_only=True)

        assert result == 0

    @patch("ccg.cli.git_commit")
    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_commit_fails(
        self,
        mock_validate: Mock,
        mock_add: Mock,
        mock_precommit: Mock,
        mock_generate: Mock,
        mock_commit: Mock,
    ) -> None:
        """Should return 1 if git commit fails."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = True
        mock_generate.return_value = "feat: test"
        mock_commit.return_value = False

        result = handle_git_workflow()

        assert result == 1

    @patch("ccg.cli.git_push")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.git_commit")
    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_with_push_existing_branch(
        self,
        mock_validate: Mock,
        mock_add: Mock,
        mock_precommit: Mock,
        mock_generate: Mock,
        mock_commit: Mock,
        mock_confirm_push: Mock,
        mock_get_branch: Mock,
        mock_branch_exists: Mock,
        mock_push: Mock,
    ) -> None:
        """Should push to existing remote branch."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = True
        mock_generate.return_value = "feat: test"
        mock_commit.return_value = True
        mock_confirm_push.return_value = True
        mock_get_branch.return_value = "main"
        mock_branch_exists.return_value = True
        mock_push.return_value = True

        result = handle_git_workflow()

        assert result == 0
        mock_push.assert_called_once()

    @patch("ccg.cli.confirm_create_branch")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.git_commit")
    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_create_new_branch_cancelled(
        self,
        mock_validate: Mock,
        mock_add: Mock,
        mock_precommit: Mock,
        mock_generate: Mock,
        mock_commit: Mock,
        mock_confirm_push: Mock,
        mock_get_branch: Mock,
        mock_branch_exists: Mock,
        mock_confirm_create: Mock,
    ) -> None:
        """Should handle cancellation of new branch creation."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = True
        mock_generate.return_value = "feat: test"
        mock_commit.return_value = True
        mock_confirm_push.return_value = True
        mock_get_branch.return_value = "new-feature"
        mock_branch_exists.return_value = False
        mock_confirm_create.return_value = False

        result = handle_git_workflow()

        assert result == 0


class TestValidateRepositoryState:
    """Tests for validate_repository_state function."""

    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.show_repository_info")
    @patch("ccg.cli.check_is_git_repo")
    def test_validation_success(
        self, mock_check_repo: Mock, mock_show_info: Mock, mock_remote: Mock
    ) -> None:
        """Should return True when all validations pass."""
        from ccg.cli import validate_repository_state

        mock_check_repo.return_value = True
        mock_remote.return_value = True

        result = validate_repository_state(commit_only=True)

        assert result is True

    @patch("ccg.cli.check_is_git_repo")
    def test_validation_not_git_repo(self, mock_check_repo: Mock) -> None:
        """Should return False if not a git repo."""
        from ccg.cli import validate_repository_state

        mock_check_repo.return_value = False

        result = validate_repository_state()

        assert result is False

    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.show_repository_info")
    @patch("ccg.cli.check_is_git_repo")
    def test_validation_no_changes(
        self,
        mock_check_repo: Mock,
        mock_show_info: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
    ) -> None:
        """Should return False when no changes detected."""
        from ccg.cli import validate_repository_state

        mock_check_repo.return_value = True
        mock_remote.return_value = True
        mock_has_changes.return_value = False

        result = validate_repository_state(commit_only=False)

        assert result is False


class TestChangeToWorkingDirectory:
    """Tests for change_to_working_directory function."""

    @patch("os.path.isdir")
    @patch("os.path.exists")
    def test_single_directory_changes_dir(
        self, mock_exists: Mock, mock_isdir: Mock
    ) -> None:
        """Should change to directory and return None."""
        from ccg.cli import change_to_working_directory

        mock_exists.return_value = True
        mock_isdir.return_value = True

        with patch("os.chdir") as mock_chdir:
            result = change_to_working_directory(["src/"])

            assert result is None
            mock_chdir.assert_called_once()

    @patch("ccg.cli.validate_paths_in_repository")
    @patch("os.path.isdir")
    @patch("os.path.exists")
    def test_multiple_paths_returns_paths(
        self, mock_exists: Mock, mock_isdir: Mock, mock_validate: Mock
    ) -> None:
        """Should return paths when multiple provided."""
        from ccg.cli import change_to_working_directory

        mock_exists.return_value = True
        mock_isdir.return_value = False

        result = change_to_working_directory(["file1.py", "file2.py"])

        assert result == ["file1.py", "file2.py"]

    def test_none_paths_returns_none(self) -> None:
        """Should return None when no paths provided."""
        from ccg.cli import change_to_working_directory

        result = change_to_working_directory(None)

        assert result is None


class TestRequireGitRepoDecorator:
    """Tests for require_git_repo decorator."""

    @patch("ccg.cli.show_repository_info")
    @patch("ccg.cli.check_is_git_repo")
    def test_decorator_passes_when_git_repo(
        self, mock_check: Mock, mock_show: Mock
    ) -> None:
        """Should execute function when in git repo."""
        from ccg.cli import require_git_repo

        mock_check.return_value = True

        @require_git_repo
        def test_func() -> int:
            return 0

        result = test_func()

        assert result == 0
        mock_check.assert_called_once()
        mock_show.assert_called_once()

    @patch("ccg.cli.check_is_git_repo")
    def test_decorator_returns_1_when_not_git_repo(self, mock_check: Mock) -> None:
        """Should return 1 when not in git repo."""
        from ccg.cli import require_git_repo

        mock_check.return_value = False

        @require_git_repo
        def test_func() -> int:
            return 0

        result = test_func()

        assert result == 1


class TestCustomHelpFormatter:
    """Tests for CustomHelpFormatter."""

    def test_custom_formatter_initialization(self) -> None:
        """Should initialize with custom parameters."""
        from ccg.cli import CustomHelpFormatter

        formatter = CustomHelpFormatter("ccg")

        assert formatter is not None

    @patch("ccg.cli.print_logo")
    def test_format_usage_prints_logo(self, mock_logo: Mock) -> None:
        """Should print logo when formatting usage."""
        from ccg.cli import CustomHelpFormatter

        formatter = CustomHelpFormatter("ccg")
        formatter._format_usage("usage", [], [], None)

        mock_logo.assert_called_once()


class TestConfirmCreateBranch:
    """Tests for confirm_create_branch function."""

    @patch("ccg.cli.confirm_user_action")
    def test_confirm_create_branch_yes(self, mock_confirm: Mock) -> None:
        """Should return True when user confirms."""
        from ccg.cli import confirm_create_branch

        mock_confirm.return_value = True

        result = confirm_create_branch()

        assert result is True

    @patch("ccg.cli.confirm_user_action")
    def test_confirm_create_branch_no(self, mock_confirm: Mock) -> None:
        """Should return False when user declines."""
        from ccg.cli import confirm_create_branch

        mock_confirm.return_value = False

        result = confirm_create_branch()

        assert result is False


class TestConfirmReset:
    """Tests for confirm_reset function."""

    @patch("ccg.cli.confirm_user_action")
    def test_confirm_reset_yes(self, mock_confirm: Mock) -> None:
        """Should return True when user confirms reset."""
        from ccg.cli import confirm_reset

        mock_confirm.return_value = True

        result = confirm_reset()

        assert result is True

    @patch("ccg.cli.confirm_user_action")
    def test_confirm_reset_no(self, mock_confirm: Mock) -> None:
        """Should return False when user declines reset."""
        from ccg.cli import confirm_reset

        mock_confirm.return_value = False

        result = confirm_reset()

        assert result is False


class TestGetCommitCountInput:
    """Tests for get_commit_count_input function."""

    @patch("ccg.cli.read_input")
    def test_return_none_on_empty_input(self, mock_input: Mock) -> None:
        """Should return None for empty input."""
        from ccg.cli import get_commit_count_input

        mock_input.return_value = ""

        result = get_commit_count_input()

        assert result is None

    @patch("ccg.cli.read_input")
    def test_return_none_on_zero(self, mock_input: Mock) -> None:
        """Should return None when user enters 0."""
        from ccg.cli import get_commit_count_input

        mock_input.return_value = "0"

        result = get_commit_count_input()

        assert result is None

    @patch("ccg.cli.read_input")
    def test_return_count_on_valid_number(self, mock_input: Mock) -> None:
        """Should return count for valid positive number."""
        from ccg.cli import get_commit_count_input

        mock_input.return_value = "5"

        result = get_commit_count_input()

        assert result == 5

    @patch("ccg.cli.read_input")
    def test_loop_on_invalid_input(self, mock_input: Mock, capsys) -> None:
        """Should loop and show error for invalid input."""
        from ccg.cli import get_commit_count_input

        mock_input.side_effect = ["invalid", "10"]

        result = get_commit_count_input()

        assert result == 10
        captured = capsys.readouterr()
        assert "valid positive number" in captured.out


class TestHandleCommitEditInput:
    """Tests for handle_commit_edit_input function."""

    @patch("ccg.cli.read_input")
    def test_cancel_on_empty_message(self, mock_input: Mock) -> None:
        """Should return (None, None) when message is empty."""
        from ccg.cli import handle_commit_edit_input

        mock_input.return_value = ""

        message, body = handle_commit_edit_input("feat: old")

        assert message is None
        assert body is None

    @patch("ccg.cli.read_input")
    @patch("ccg.cli.validate_commit_message")
    def test_return_message_and_body_on_success(
        self, mock_validate: Mock, mock_input: Mock
    ) -> None:
        """Should return new message and body on valid input."""
        from ccg.cli import handle_commit_edit_input

        mock_validate.return_value = (True, None)
        mock_input.side_effect = ["feat: new message", "This is the body"]

        message, body = handle_commit_edit_input("feat: old", "old body")

        assert message == "feat: new message"
        assert body == "This is the body"

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.validate_commit_message")
    def test_retry_on_invalid_message_when_confirmed(
        self, mock_validate: Mock, mock_input: Mock, mock_confirm: Mock
    ) -> None:
        """Should retry when validation fails and user confirms retry."""
        from ccg.cli import handle_commit_edit_input

        mock_validate.side_effect = [(False, "Invalid format"), (True, None)]
        mock_input.side_effect = ["invalid message", "feat: valid message", "body"]
        mock_confirm.return_value = True

        message, body = handle_commit_edit_input("feat: old")

        assert message == "feat: valid message"
        assert body == "body"

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.validate_commit_message")
    def test_cancel_on_invalid_message_when_not_confirmed(
        self, mock_validate: Mock, mock_input: Mock, mock_confirm: Mock
    ) -> None:
        """Should cancel when validation fails and user declines retry."""
        from ccg.cli import handle_commit_edit_input

        mock_validate.return_value = (False, "Invalid format")
        mock_input.return_value = "invalid message"
        mock_confirm.return_value = False

        message, body = handle_commit_edit_input("feat: old")

        assert message is None
        assert body is None


class TestConfirmCommitEdit:
    """Tests for confirm_commit_edit function."""

    @patch("ccg.cli.confirm_commit")
    def test_confirm_edit_with_body(self, mock_confirm: Mock) -> None:
        """Should confirm edit with body."""
        from ccg.cli import confirm_commit_edit

        mock_confirm.return_value = True

        result = confirm_commit_edit("feat: old", "old body", "feat: new", "new body")

        assert result is True

    @patch("ccg.cli.confirm_commit")
    def test_confirm_edit_without_body(self, mock_confirm: Mock) -> None:
        """Should confirm edit without body."""
        from ccg.cli import confirm_commit_edit

        mock_confirm.return_value = False

        result = confirm_commit_edit("feat: old", None, "feat: new", None)

        assert result is False


class TestHandlePushAfterEdit:
    """Tests for handle_push_after_edit function."""

    @patch("ccg.cli.git_push")
    @patch("ccg.cli.confirm_create_branch")
    @patch("ccg.cli.branch_exists_on_remote")
    def test_create_new_branch_when_confirmed(
        self, mock_branch_exists: Mock, mock_confirm: Mock, mock_push: Mock
    ) -> None:
        """Should create new branch when user confirms."""
        from ccg.cli import handle_push_after_edit

        mock_branch_exists.return_value = False
        mock_confirm.return_value = True
        mock_push.return_value = True

        result = handle_push_after_edit("new-feature")

        assert result == 0
        mock_push.assert_called_once_with(set_upstream=True)

    @patch("ccg.cli.confirm_create_branch")
    @patch("ccg.cli.branch_exists_on_remote")
    def test_cancel_branch_creation_when_declined(
        self, mock_branch_exists: Mock, mock_confirm: Mock
    ) -> None:
        """Should cancel when user declines branch creation."""
        from ccg.cli import handle_push_after_edit

        mock_branch_exists.return_value = False
        mock_confirm.return_value = False

        result = handle_push_after_edit("new-feature")

        assert result == 0

    @patch("ccg.cli.git_push")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.branch_exists_on_remote")
    def test_force_push_existing_branch_when_confirmed(
        self, mock_branch_exists: Mock, mock_confirm: Mock, mock_push: Mock
    ) -> None:
        """Should force push to existing branch when confirmed."""
        from ccg.cli import handle_push_after_edit

        mock_branch_exists.return_value = True
        mock_confirm.return_value = True
        mock_push.return_value = True

        result = handle_push_after_edit("main")

        assert result == 0
        mock_push.assert_called_once_with(force=True)

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.branch_exists_on_remote")
    def test_cancel_force_push_when_declined(
        self, mock_branch_exists: Mock, mock_confirm: Mock
    ) -> None:
        """Should cancel when user declines force push."""
        from ccg.cli import handle_push_after_edit

        mock_branch_exists.return_value = True
        mock_confirm.return_value = False

        result = handle_push_after_edit("main")

        assert result == 0


class TestDisplayCommitDetails:
    """Tests for display_commit_details function."""

    def test_display_with_body(self, capsys) -> None:
        """Should display commit details with body."""
        from ccg.cli import display_commit_details

        commit = (
            "abc123full",
            "abc",
            "feat: test",
            "This is the body",
            "John Doe",
            "1 day ago",
        )

        display_commit_details(commit)

        captured = capsys.readouterr()
        assert "abc123full" in captured.out
        assert "feat: test" in captured.out
        assert "This is the body" in captured.out
        assert "John Doe" in captured.out

    def test_display_without_body(self, capsys) -> None:
        """Should display commit details without body."""
        from ccg.cli import display_commit_details

        commit = ("abc123full", "abc", "feat: test", "", "John Doe", "1 day ago")

        display_commit_details(commit)

        captured = capsys.readouterr()
        assert "abc123full" in captured.out
        assert "feat: test" in captured.out
        assert "Body:" not in captured.out


class TestEditSpecificCommitAdvanced:
    """Advanced tests for edit_specific_commit."""

    @patch("ccg.cli.confirm_commit_edit")
    @patch("ccg.cli.handle_commit_edit_input")
    @patch("ccg.cli.get_commit_by_hash")
    def test_edit_cancelled_by_confirm(
        self, mock_get: Mock, mock_input: Mock, mock_confirm: Mock
    ) -> None:
        """Should return 0 when user cancels at confirmation step."""
        from ccg.cli import edit_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: old",
            "",
            "Author",
            "1 day ago",
        )
        mock_input.return_value = ("feat: new", None)
        mock_confirm.return_value = False

        result = edit_specific_commit("abc123")

        assert result == 0

    @patch("ccg.cli.edit_commit_message")
    @patch("ccg.cli.confirm_commit_edit")
    @patch("ccg.cli.handle_commit_edit_input")
    @patch("ccg.cli.get_commit_by_hash")
    def test_edit_fails(
        self, mock_get: Mock, mock_input: Mock, mock_confirm: Mock, mock_edit: Mock
    ) -> None:
        """Should return 1 when edit operation fails."""
        from ccg.cli import edit_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: old",
            "",
            "Author",
            "1 day ago",
        )
        mock_input.return_value = ("feat: new", None)
        mock_confirm.return_value = True
        mock_edit.return_value = False

        result = edit_specific_commit("abc123")

        assert result == 1

    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.edit_commit_message")
    @patch("ccg.cli.confirm_commit_edit")
    @patch("ccg.cli.handle_commit_edit_input")
    @patch("ccg.cli.get_commit_by_hash")
    def test_edit_push_fails_no_branch(
        self,
        mock_get: Mock,
        mock_input: Mock,
        mock_confirm: Mock,
        mock_edit: Mock,
        mock_push_confirm: Mock,
        mock_branch: Mock,
    ) -> None:
        """Should return 1 when cannot determine branch name."""
        from ccg.cli import edit_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: old",
            "",
            "Author",
            "1 day ago",
        )
        mock_input.return_value = ("feat: new", None)
        mock_confirm.return_value = True
        mock_edit.return_value = True
        mock_push_confirm.return_value = True
        mock_branch.return_value = None

        result = edit_specific_commit("abc123")

        assert result == 1


class TestDeleteSpecificCommitAdvanced:
    """Advanced tests for delete_specific_commit."""

    @patch("ccg.cli.delete_commit")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.get_commit_by_hash")
    def test_delete_fails(
        self, mock_get: Mock, mock_confirm: Mock, mock_delete: Mock
    ) -> None:
        """Should return 1 when delete operation fails."""
        from ccg.cli import delete_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: test",
            "",
            "Author",
            "1 day ago",
        )
        mock_confirm.return_value = True
        mock_delete.return_value = False

        result = delete_specific_commit("abc123")

        assert result == 1

    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.delete_commit")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.get_commit_by_hash")
    def test_delete_push_fails_no_branch(
        self,
        mock_get: Mock,
        mock_confirm: Mock,
        mock_delete: Mock,
        mock_push_confirm: Mock,
        mock_branch: Mock,
    ) -> None:
        """Should return 1 when cannot determine branch name after delete."""
        from ccg.cli import delete_specific_commit

        mock_get.return_value = (
            "abc123",
            "abc",
            "feat: test",
            "",
            "Author",
            "1 day ago",
        )
        mock_confirm.return_value = True
        mock_delete.return_value = True
        mock_push_confirm.return_value = True
        mock_branch.return_value = None

        result = delete_specific_commit("abc123")

        assert result == 1

    @patch("ccg.cli.get_commit_by_hash")
    def test_delete_commit_not_found(self, mock_get: Mock) -> None:
        """Should return 1 when commit not found."""
        from ccg.cli import delete_specific_commit

        mock_get.return_value = None

        result = delete_specific_commit("nonexistent")

        assert result == 1


class TestHandleTagAdvanced:
    """Advanced tests for handle_tag."""

    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_with_uncommitted_changes(
        self, mock_show: Mock, mock_check: Mock, mock_has_changes: Mock
    ) -> None:
        """Should return 1 when there are uncommitted changes."""
        from ccg.cli import handle_tag

        mock_check.return_value = True
        mock_has_changes.return_value = True

        result = handle_tag()

        assert result == 1
        mock_has_changes.assert_called_once()

    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_no_remote_access(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
    ) -> None:
        """Should return 1 when no remote access."""
        from ccg.cli import handle_tag

        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = False

        result = handle_tag()

        assert result == 1

    @patch("ccg.cli._get_commit_selection")
    @patch("ccg.cli._display_commits_list")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_cancelled_empty_name(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_input: Mock,
        mock_has_changes: Mock,
        mock_count_input: Mock,
        mock_get_commits: Mock,
        mock_display: Mock,
        mock_selection: Mock,
    ) -> None:
        """Should return 0 when tag name is empty (cancelled)."""
        from ccg.cli import handle_tag

        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            ("abc123", "abc12", "feat: test", "Author", "2024-01-01")
        ]
        mock_selection.return_value = "abc123"
        mock_input.return_value = ""

        result = handle_tag()

        assert result == 0

    @patch("ccg.cli._get_commit_selection")
    @patch("ccg.cli._display_commits_list")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_annotated_empty_message(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_confirm: Mock,
        mock_input: Mock,
        mock_has_changes: Mock,
        mock_count_input: Mock,
        mock_get_commits: Mock,
        mock_display: Mock,
        mock_selection: Mock,
    ) -> None:
        """Should return 1 when annotated tag message is empty."""
        from ccg.cli import handle_tag

        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            ("def456", "def45", "fix: bug", "Author", "2024-01-02")
        ]
        mock_selection.return_value = "def456"
        mock_input.side_effect = ["v1.0.0", ""]  # Tag name, then empty message
        mock_confirm.return_value = True  # Want annotated tag

        result = handle_tag()

        assert result == 1

    @patch("ccg.cli._get_commit_selection")
    @patch("ccg.cli._display_commits_list")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.create_tag")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_creation_fails(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_confirm: Mock,
        mock_input: Mock,
        mock_create: Mock,
        mock_has_changes: Mock,
        mock_count_input: Mock,
        mock_get_commits: Mock,
        mock_display: Mock,
        mock_selection: Mock,
    ) -> None:
        """Should return 1 when tag creation fails."""
        from ccg.cli import handle_tag

        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            ("ghi789", "ghi78", "docs: update", "Author", "2024-01-03")
        ]
        mock_selection.return_value = "ghi789"
        mock_input.return_value = "v1.0.0"
        mock_confirm.return_value = False  # Not annotated
        mock_create.return_value = False

        result = handle_tag()

        assert result == 1

    @patch("ccg.cli._get_commit_selection")
    @patch("ccg.cli._display_commits_list")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.push_tag")
    @patch("ccg.cli.create_tag")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_tag_push_fails(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_confirm: Mock,
        mock_input: Mock,
        mock_create: Mock,
        mock_push: Mock,
        mock_has_changes: Mock,
        mock_count_input: Mock,
        mock_get_commits: Mock,
        mock_display: Mock,
        mock_selection: Mock,
    ) -> None:
        """Should return 1 when push tag fails."""
        from ccg.cli import handle_tag

        mock_check.return_value = True
        mock_has_changes.return_value = False
        mock_remote.return_value = True
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            ("jkl012", "jkl01", "chore: cleanup", "Author", "2024-01-04")
        ]
        mock_selection.return_value = "jkl012"
        mock_input.return_value = "v1.0.0"
        mock_confirm.side_effect = [False, True]  # Not annotated, but push
        mock_create.return_value = True
        mock_push.return_value = False

        result = handle_tag()

        assert result == 1


class TestHandleResetAdvanced:
    """Advanced tests for handle_reset."""

    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_reset_no_remote_access(
        self, mock_show: Mock, mock_check: Mock, mock_remote: Mock
    ) -> None:
        """Should return 1 when no remote access."""
        from ccg.cli import handle_reset

        mock_check.return_value = True
        mock_remote.return_value = False

        result = handle_reset()

        assert result == 1

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_reset_no_changes_pull_confirmed(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
        mock_confirm: Mock,
    ) -> None:
        """Should pull when no changes and user confirms."""
        from ccg.cli import handle_reset

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_has_changes.return_value = False
        mock_confirm.return_value = True

        with patch("ccg.cli.pull_from_remote", return_value=True) as mock_pull:
            result = handle_reset()

            assert result == 0
            mock_pull.assert_called_once()

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_reset_no_changes_pull_declined(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
        mock_confirm: Mock,
    ) -> None:
        """Should cancel when no changes and user declines pull."""
        from ccg.cli import handle_reset

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_has_changes.return_value = False
        mock_confirm.return_value = False

        result = handle_reset()

        assert result == 0

    @patch("ccg.cli.discard_local_changes")
    @patch("ccg.cli.confirm_reset")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_reset_discard_fails(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
        mock_confirm: Mock,
        mock_discard: Mock,
    ) -> None:
        """Should return 1 when discard fails."""
        from ccg.cli import handle_reset

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_has_changes.return_value = True
        mock_confirm.return_value = True
        mock_discard.return_value = False

        result = handle_reset()

        assert result == 1

    @patch("ccg.cli.pull_from_remote")
    @patch("ccg.cli.discard_local_changes")
    @patch("ccg.cli.confirm_reset")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_reset_pull_fails(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
        mock_confirm: Mock,
        mock_discard: Mock,
        mock_pull: Mock,
    ) -> None:
        """Should return 1 when pull fails."""
        from ccg.cli import handle_reset

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_has_changes.return_value = True
        mock_confirm.return_value = True
        mock_discard.return_value = True
        mock_pull.return_value = False

        result = handle_reset()

        assert result == 1

    @patch("ccg.cli.confirm_reset")
    @patch("ccg.cli.check_has_changes")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_reset_with_changes_cancelled_by_user(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_has_changes: Mock,
        mock_confirm: Mock,
    ) -> None:
        """Should return 0 when user cancels reset with existing changes."""
        from ccg.cli import handle_reset

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_has_changes.return_value = True
        mock_confirm.return_value = False  # User declines reset

        result = handle_reset()

        assert result == 0
        mock_confirm.assert_called_once()


class TestHandlePushOnlyAdvanced:
    """Advanced tests for handle_push_only."""

    @patch("ccg.cli.check_is_git_repo")
    def test_push_only_not_git_repo(self, mock_check: Mock) -> None:
        """Should return 1 when not a git repo."""
        from ccg.cli import handle_push_only

        mock_check.return_value = False

        result = handle_push_only()

        assert result == 1

    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_no_remote_access(
        self, mock_show: Mock, mock_check: Mock, mock_remote: Mock
    ) -> None:
        """Should return 1 when no remote access."""
        from ccg.cli import handle_push_only

        mock_check.return_value = True
        mock_remote.return_value = False

        result = handle_push_only()

        assert result == 1

    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_no_branch_name(
        self, mock_show: Mock, mock_check: Mock, mock_remote: Mock, mock_branch: Mock
    ) -> None:
        """Should return 1 when cannot determine branch name."""
        from ccg.cli import handle_push_only

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_branch.return_value = None

        result = handle_push_only()

        assert result == 1

    @patch("ccg.cli.git_push")
    @patch("ccg.cli.confirm_create_branch")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_create_branch_fails(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_branch: Mock,
        mock_exists: Mock,
        mock_confirm: Mock,
        mock_push: Mock,
    ) -> None:
        """Should return 1 when creating branch fails."""
        from ccg.cli import handle_push_only

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_branch.return_value = "new-feature"
        mock_exists.return_value = False
        mock_confirm.return_value = True
        mock_push.return_value = False

        result = handle_push_only()

        assert result == 1

    @patch("ccg.cli.confirm_create_branch")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_decline_create_branch(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_branch: Mock,
        mock_exists: Mock,
        mock_confirm: Mock,
    ) -> None:
        """Should return 0 when user declines creating branch."""
        from ccg.cli import handle_push_only

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_branch.return_value = "new-feature"
        mock_exists.return_value = False
        mock_confirm.return_value = False

        result = handle_push_only()

        assert result == 0

    @patch("ccg.cli.has_commits_to_push")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_no_commits_to_push(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_remote: Mock,
        mock_branch: Mock,
        mock_exists: Mock,
        mock_has_commits: Mock,
    ) -> None:
        """Should return 1 when there are no commits to push."""
        from ccg.cli import handle_push_only

        mock_check.return_value = True
        mock_remote.return_value = True
        mock_branch.return_value = "main"
        mock_exists.return_value = True  # Branch exists on remote
        mock_has_commits.return_value = False  # No commits to push

        result = handle_push_only()

        assert result == 1
        mock_has_commits.assert_called_once()


class TestValidateRepositoryStateAdvanced:
    """Advanced tests for validate_repository_state."""

    @patch("ccg.cli.check_remote_access")
    @patch("ccg.cli.show_repository_info")
    @patch("ccg.cli.check_is_git_repo")
    def test_validation_remote_access_fails_exits(
        self, mock_check_repo: Mock, mock_show_info: Mock, mock_remote: Mock
    ) -> None:
        """Should exit when remote access fails."""
        from ccg.cli import validate_repository_state

        mock_check_repo.return_value = True
        mock_remote.return_value = False

        with pytest.raises(SystemExit):
            validate_repository_state()


class TestValidatePathsInRepository:
    """Tests for validate_paths_in_repository function."""

    @patch("ccg.cli.is_path_in_repository")
    @patch("ccg.cli.get_repository_root")
    def test_validate_paths_inside_repo(
        self, mock_root: Mock, mock_is_path: Mock
    ) -> None:
        """Should pass when all paths are inside repository."""
        from ccg.cli import validate_paths_in_repository

        mock_root.return_value = "/home/user/repo"
        mock_is_path.return_value = True

        # Should not raise
        validate_paths_in_repository(["src/file.py", "tests/test.py"])

    @patch("ccg.cli.get_repository_root")
    def test_validate_paths_no_repo_root(self, mock_root: Mock) -> None:
        """Should exit when cannot determine repo root."""
        from ccg.cli import validate_paths_in_repository

        mock_root.return_value = None

        with pytest.raises(SystemExit):
            validate_paths_in_repository(["src/file.py"])

    @patch("ccg.cli.is_path_in_repository")
    @patch("ccg.cli.get_repository_root")
    def test_validate_paths_outside_repo(
        self, mock_root: Mock, mock_is_path: Mock
    ) -> None:
        """Should exit when paths are outside repository."""
        from ccg.cli import validate_paths_in_repository

        mock_root.return_value = "/home/user/repo"
        mock_is_path.return_value = False

        with pytest.raises(SystemExit):
            validate_paths_in_repository(["/home/other/file.py"])


class TestChangeToWorkingDirectoryAdvanced:
    """Advanced tests for change_to_working_directory."""

    @patch("os.path.isdir")
    @patch("os.path.exists")
    def test_change_dir_fails(self, mock_exists: Mock, mock_isdir: Mock) -> None:
        """Should exit when cannot change directory."""
        from ccg.cli import change_to_working_directory

        mock_exists.return_value = True
        mock_isdir.return_value = True

        with patch("os.chdir", side_effect=OSError("Permission denied")):
            with pytest.raises(SystemExit):
                change_to_working_directory(["src/"])


class TestHandleGitWorkflowAdvanced:
    """Advanced tests for handle_git_workflow."""

    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_generate_message_returns_none(
        self,
        mock_validate: Mock,
        mock_add: Mock,
        mock_precommit: Mock,
        mock_generate: Mock,
    ) -> None:
        """Should return 1 when generate_commit_message returns None."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = True
        mock_generate.return_value = None

        result = handle_git_workflow()

        assert result == 1

    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.git_commit")
    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_push_no_branch_name(
        self,
        mock_validate: Mock,
        mock_add: Mock,
        mock_precommit: Mock,
        mock_generate: Mock,
        mock_commit: Mock,
        mock_confirm_push: Mock,
        mock_branch: Mock,
    ) -> None:
        """Should return 1 when cannot determine branch name."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = True
        mock_generate.return_value = "feat: test"
        mock_commit.return_value = True
        mock_confirm_push.return_value = True
        mock_branch.return_value = None

        result = handle_git_workflow()

        assert result == 1

    @patch("ccg.cli.git_push")
    @patch("ccg.cli.confirm_create_branch")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.git_commit")
    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_create_branch_fails(
        self,
        mock_validate: Mock,
        mock_add: Mock,
        mock_precommit: Mock,
        mock_generate: Mock,
        mock_commit: Mock,
        mock_confirm_push: Mock,
        mock_branch: Mock,
        mock_exists: Mock,
        mock_confirm_create: Mock,
        mock_push: Mock,
    ) -> None:
        """Should return 1 when creating branch fails."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = True
        mock_generate.return_value = "feat: test"
        mock_commit.return_value = True
        mock_confirm_push.return_value = True
        mock_branch.return_value = "new-feature"
        mock_exists.return_value = False
        mock_confirm_create.return_value = True
        mock_push.return_value = False

        result = handle_git_workflow()

        assert result == 1

    @patch("ccg.cli.git_push")
    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.get_current_branch")
    @patch("ccg.cli.confirm_push")
    @patch("ccg.cli.git_commit")
    @patch("ccg.cli.generate_commit_message")
    @patch("ccg.cli.check_and_install_pre_commit")
    @patch("ccg.cli.git_add")
    @patch("ccg.cli.validate_repository_state")
    def test_workflow_push_existing_branch_fails(
        self,
        mock_validate: Mock,
        mock_add: Mock,
        mock_precommit: Mock,
        mock_generate: Mock,
        mock_commit: Mock,
        mock_confirm_push: Mock,
        mock_branch: Mock,
        mock_exists: Mock,
        mock_push: Mock,
    ) -> None:
        """Should return 1 when push to existing branch fails."""
        from ccg.cli import handle_git_workflow

        mock_validate.return_value = True
        mock_add.return_value = True
        mock_precommit.return_value = True
        mock_generate.return_value = "feat: test"
        mock_commit.return_value = True
        mock_confirm_push.return_value = True
        mock_branch.return_value = "main"
        mock_exists.return_value = True
        mock_push.return_value = False

        result = handle_git_workflow()

        assert result == 1


class TestHandleCommitOperationNoCommits:
    """Test handle_commit_operation when no commits are found."""

    @patch("ccg.cli.get_commit_count_input", return_value=5)
    @patch("ccg.cli.get_recent_commits", return_value=[])
    @patch("ccg.cli.check_has_changes", return_value=False)
    @patch("ccg.cli.check_is_git_repo", return_value=True)
    @patch("ccg.cli.show_repository_info")
    def test_edit_no_commits_found(
        self,
        mock_show_info: Mock,
        mock_is_repo: Mock,
        mock_has_changes: Mock,
        mock_get_commits: Mock,
        mock_count: Mock,
    ) -> None:
        """Should return 1 when no commits are found for editing."""
        from ccg.cli import handle_edit

        result = handle_edit()

        assert result == 1
        mock_get_commits.assert_called_once_with(5)


class TestHandleEditAndDeleteReturnPaths:
    """Test return statements in handle_edit and handle_delete."""

    @patch("ccg.cli.handle_commit_operation", return_value=0)
    def test_handle_edit_return_value(self, mock_operation: Mock) -> None:
        """Should return result from handle_commit_operation for edit."""
        from ccg.cli import handle_edit

        result = handle_edit()

        assert result == 0
        mock_operation.assert_called_once_with("edit")

    @patch("ccg.cli.handle_commit_operation", return_value=1)
    def test_handle_delete_return_value(self, mock_operation: Mock) -> None:
        """Should return result from handle_commit_operation for delete."""
        from ccg.cli import handle_delete

        result = handle_delete()

        assert result == 1
        mock_operation.assert_called_once_with("delete")


class TestHandlePushAfterEditBranchNotOnRemote:
    """Test handle_push_after_edit when branch doesn't exist on remote."""

    @patch("ccg.cli.branch_exists_on_remote", return_value=False)
    @patch("ccg.cli.confirm_create_branch", return_value=False)
    def test_push_after_edit_cancel_branch_creation(
        self, mock_confirm: Mock, mock_branch_exists: Mock
    ) -> None:
        """Should return 0 when user cancels branch creation."""
        from ccg.cli import handle_push_after_edit

        result = handle_push_after_edit("feature-branch")

        assert result == 0
        mock_branch_exists.assert_called_once_with("feature-branch")
        mock_confirm.assert_called_once()

    @patch("ccg.cli.branch_exists_on_remote", return_value=False)
    @patch("ccg.cli.confirm_create_branch", return_value=True)
    @patch("ccg.cli.git_push", return_value=False)
    def test_push_after_edit_fail_create_branch(
        self, mock_push: Mock, mock_confirm: Mock, mock_branch_exists: Mock
    ) -> None:
        """Should return 1 when branch creation push fails."""
        from ccg.cli import handle_push_after_edit

        result = handle_push_after_edit("feature-branch")

        assert result == 1
        mock_push.assert_called_once_with(set_upstream=True)


class TestHandlePushAfterEditForceFailure:
    """Test handle_push_after_edit when force push fails."""

    @patch("ccg.cli.branch_exists_on_remote", return_value=True)
    @patch("ccg.cli.confirm_user_action", return_value=True)
    @patch("ccg.cli.git_push", return_value=False)
    def test_push_after_edit_force_push_fails(
        self, mock_push: Mock, mock_confirm: Mock, mock_branch_exists: Mock
    ) -> None:
        """Should return 1 when force push fails."""
        from ccg.cli import handle_push_after_edit

        result = handle_push_after_edit("main")

        assert result == 1
        mock_push.assert_called_once_with(force=True)


class TestEditSpecificCommitNoPush:
    """Test edit_specific_commit when user doesn't want to push."""

    @patch(
        "ccg.cli.get_commit_by_hash",
        return_value=("abc123", "abc", "feat: test", None, "Author", "1 day ago"),
    )
    @patch("ccg.cli.handle_commit_edit_input", return_value=("new message", None))
    @patch("ccg.cli.confirm_commit_edit", return_value=True)
    @patch("ccg.cli.edit_commit_message", return_value=True)
    @patch("ccg.cli.confirm_push", return_value=False)
    def test_edit_commit_no_push(
        self,
        mock_confirm_push: Mock,
        mock_edit: Mock,
        mock_confirm_edit: Mock,
        mock_input: Mock,
        mock_get_commit: Mock,
    ) -> None:
        """Should return 0 when user chooses not to push after edit."""
        from ccg.cli import edit_specific_commit

        result = edit_specific_commit("abc123")

        assert result == 0
        mock_confirm_push.assert_called_once()


class TestDeleteSpecificCommitNoPush:
    """Test delete_specific_commit when user doesn't want to push."""

    @patch(
        "ccg.cli.get_commit_by_hash",
        return_value=("abc123", "abc", "feat: test", None, "Author", "1 day ago"),
    )
    @patch("ccg.cli.confirm_user_action", return_value=True)
    @patch("ccg.cli.delete_commit", return_value=True)
    @patch("ccg.cli.confirm_push", return_value=False)
    def test_delete_commit_no_push(
        self,
        mock_confirm_push: Mock,
        mock_delete: Mock,
        mock_confirm: Mock,
        mock_get_commit: Mock,
    ) -> None:
        """Should return 0 when user chooses not to push after delete."""
        from ccg.cli import delete_specific_commit

        result = delete_specific_commit("abc123")

        assert result == 0
        mock_confirm_push.assert_called_once()


class TestMainModuleExecution:
    """Test CLI module execution."""

    @patch("sys.exit")
    @patch("ccg.cli.main", return_value=0)
    def test_cli_module_execution(self, mock_main: Mock, mock_exit: Mock) -> None:
        """Should call sys.exit(main()) when cli.py is run as __main__."""
        import ccg.cli

        result = ccg.cli.main([])
        assert isinstance(result, int)


class TestLoggingIntegration:
    """Tests for logging integration in CLI."""

    @patch("ccg.logging.Path.home")
    @patch("ccg.cli.handle_git_workflow")
    @patch("ccg.cli.parse_args")
    def test_main_initializes_logging_verbose(
        self, mock_parse: Mock, mock_workflow: Mock, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should initialize logging with verbose=True when --verbose flag is used."""
        from ccg.cli import main

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        mock_args = Mock()
        mock_args.verbose = True
        mock_args.push = False
        mock_args.commit = False
        mock_args.edit = False
        mock_args.delete = False
        mock_args.reset = False
        mock_args.tag = False
        mock_args.analyze = False
        mock_args.path = None
        mock_parse.return_value = mock_args
        mock_workflow.return_value = 0

        with patch("sys.argv", ["ccg", "--verbose"]):
            result = main()

        assert result == 0
        assert log_file.exists()

    @patch("ccg.logging.Path.home")
    @patch("ccg.cli.handle_git_workflow")
    @patch("ccg.cli.parse_args")
    def test_main_initializes_logging_non_verbose(
        self, mock_parse: Mock, mock_workflow: Mock, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should initialize logging with verbose=False by default."""
        from ccg.cli import main

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        mock_args = Mock()
        mock_args.verbose = False
        mock_args.push = False
        mock_args.commit = False
        mock_args.edit = False
        mock_args.delete = False
        mock_args.reset = False
        mock_args.tag = False
        mock_args.analyze = False
        mock_args.path = None
        mock_parse.return_value = mock_args
        mock_workflow.return_value = 0

        with patch("sys.argv", ["ccg"]):
            result = main()

        assert result == 0
        assert log_file.exists()

    @patch("ccg.logging.Path.home")
    @patch("ccg.cli.parse_args")
    def test_main_logs_startup_info(
        self, mock_parse: Mock, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should log startup information."""
        from ccg.cli import main

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        mock_args = Mock()
        mock_args.verbose = False
        mock_args.push = False
        mock_args.commit = False
        mock_args.edit = False
        mock_args.delete = False
        mock_args.reset = False
        mock_args.tag = False
        mock_args.analyze = False
        mock_args.path = None
        mock_parse.return_value = mock_args

        with patch("sys.argv", ["ccg"]):
            with patch("ccg.cli.handle_git_workflow", return_value=0):
                main()

        # Read log file
        log_content = log_file.read_text(encoding="utf-8")
        assert "CCG started" in log_content

    @patch("ccg.logging.Path.home")
    @patch("ccg.cli.parse_args")
    def test_main_logs_workflow_routes(
        self, mock_parse: Mock, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should log which workflow is running."""
        from ccg.cli import main

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        mock_args = Mock()
        mock_args.verbose = False
        mock_args.push = False
        mock_args.commit = False
        mock_args.edit = True
        mock_args.delete = False
        mock_args.reset = False
        mock_args.tag = False
        mock_args.analyze = False
        mock_args.path = None
        mock_parse.return_value = mock_args

        with patch("sys.argv", ["ccg", "--edit"]):
            with patch("ccg.cli.handle_edit", return_value=0):
                main()

        log_content = log_file.read_text(encoding="utf-8")
        assert "Running edit workflow" in log_content

    @patch("ccg.logging.Path.home")
    @patch("ccg.cli.parse_args")
    def test_main_logs_user_cancellation(
        self, mock_parse: Mock, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should log when operation is cancelled by user."""
        from ccg.cli import main

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        mock_parse.side_effect = KeyboardInterrupt()

        with patch("sys.argv", ["ccg"]):
            result = main()

        assert result == 130
        log_content = log_file.read_text(encoding="utf-8")
        assert "Operation cancelled by user" in log_content

    @patch("ccg.logging.Path.home")
    @patch("ccg.cli.parse_args")
    def test_main_logs_exceptions(
        self, mock_parse: Mock, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should log unexpected exceptions."""
        from ccg.cli import main

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        mock_parse.side_effect = Exception("Test error")

        with patch("sys.argv", ["ccg"]):
            result = main()

        assert result == 1
        log_content = log_file.read_text(encoding="utf-8")
        assert "Unexpected error in main()" in log_content

    @patch("ccg.logging.Path.home")
    @patch("ccg.cli.parse_args")
    def test_main_logs_session_end(
        self, mock_parse: Mock, mock_home: Mock, tmp_path: Path
    ) -> None:
        """Should log session end."""
        from ccg.cli import main

        mock_home.return_value = tmp_path
        log_file = tmp_path / ".ccg" / "ccg.log"

        mock_args = Mock()
        mock_args.verbose = False
        mock_args.push = False
        mock_args.commit = False
        mock_args.edit = False
        mock_args.delete = False
        mock_args.reset = False
        mock_args.tag = False
        mock_args.analyze = False
        mock_args.path = None
        mock_parse.return_value = mock_args

        with patch("sys.argv", ["ccg"]):
            with patch("ccg.cli.handle_git_workflow", return_value=0):
                main()

        log_content = log_file.read_text(encoding="utf-8")
        assert "CCG session ended" in log_content


class TestMainFunction:
    """Tests for main function."""

    @patch("ccg.cli.handle_git_workflow")
    @patch("ccg.cli.parse_args")
    def test_main_default_workflow(self, mock_parse: Mock, mock_workflow: Mock) -> None:
        """Should execute default workflow when no flags."""
        from ccg.cli import main

        mock_args = Mock()
        mock_args.push = False
        mock_args.commit = False
        mock_args.edit = False
        mock_args.delete = False
        mock_args.reset = False
        mock_args.tag = False
        mock_args.analyze = False
        mock_args.path = None
        mock_parse.return_value = mock_args
        mock_workflow.return_value = 0

        with patch("sys.argv", ["ccg"]):
            result = main()

        assert result == 0
        mock_workflow.assert_called_once()

    @pytest.mark.parametrize(
        "flag_name,handler_name",
        [
            ("edit", "handle_edit"),
            ("delete", "handle_delete"),
            ("push", "handle_push_only"),
            ("reset", "handle_reset"),
            ("tag", "handle_tag"),
            ("analyze", "handle_analyze"),
        ],
    )
    @patch("ccg.cli.parse_args")
    def test_main_operation_flags(
        self, mock_parse: Mock, flag_name: str, handler_name: str
    ) -> None:
        """Should handle operation flags and call appropriate handlers."""
        from ccg.cli import main

        # Create mock args with all flags False except the one being tested
        mock_args = Mock()
        for flag in ["push", "commit", "edit", "delete", "reset", "tag", "analyze"]:
            setattr(mock_args, flag, flag == flag_name)
        mock_args.path = None
        mock_parse.return_value = mock_args

        # Patch the specific handler for this test case
        with patch(f"ccg.cli.{handler_name}", return_value=0) as mock_handler:
            with patch("sys.argv", ["ccg", f"--{flag_name}"]):
                result = main()

            assert result == 0
            mock_handler.assert_called_once()

    @patch("ccg.cli.handle_git_workflow")
    @patch("ccg.cli.change_to_working_directory")
    @patch("ccg.cli.parse_args")
    def test_main_with_path_flag_and_operation(
        self, mock_parse: Mock, mock_change_dir: Mock, mock_workflow: Mock
    ) -> None:
        """Should change directory when --path used with operation flag."""
        from ccg.cli import main

        mock_args = Mock()
        mock_args.push = False
        mock_args.commit = False
        mock_args.edit = True
        mock_args.delete = False
        mock_args.reset = False
        mock_args.tag = False
        mock_args.analyze = False
        mock_args.path = ["src/"]
        mock_parse.return_value = mock_args
        mock_change_dir.return_value = None

        with patch("sys.argv", ["ccg", "--path", "src/", "--edit"]):
            with patch("ccg.cli.handle_edit", return_value=0):
                result = main()

        assert result == 0
        mock_change_dir.assert_called_once()

    @patch("ccg.cli.handle_git_workflow")
    @patch("ccg.cli.change_to_working_directory")
    @patch("ccg.cli.parse_args")
    def test_main_with_path_no_operation(
        self, mock_parse: Mock, mock_change_dir: Mock, mock_workflow: Mock
    ) -> None:
        """Should handle path without operation flag."""
        from ccg.cli import main

        mock_args = Mock()
        mock_args.push = False
        mock_args.commit = False
        mock_args.edit = False
        mock_args.delete = False
        mock_args.reset = False
        mock_args.tag = False
        mock_args.analyze = False
        mock_args.path = ["src/"]
        mock_parse.return_value = mock_args
        mock_change_dir.return_value = None
        mock_workflow.return_value = 0

        with patch("sys.argv", ["ccg", "--path", "src/"]):
            result = main()

        assert result == 0
        mock_change_dir.assert_called()

    @patch("ccg.cli.print_info")
    @patch("ccg.cli.print_warning")
    @patch("ccg.cli.parse_args")
    def test_main_keyboard_interrupt(
        self, mock_parse: Mock, mock_warning: Mock, mock_info: Mock
    ) -> None:
        """Should return 130 on KeyboardInterrupt and show goodbye message."""
        from ccg.cli import main

        mock_parse.side_effect = KeyboardInterrupt()

        result = main()

        assert result == 130
        mock_warning.assert_called_once_with("Operation cancelled by user")
        mock_info.assert_called_once_with("Goodbye! 👋")

    @patch("ccg.cli.print_info")
    @patch("ccg.cli.print_warning")
    @patch("ccg.cli.parse_args")
    def test_main_eof_error(
        self, mock_parse: Mock, mock_warning: Mock, mock_info: Mock
    ) -> None:
        """Should return 130 on EOFError and show goodbye message."""
        from ccg.cli import main

        mock_parse.side_effect = EOFError()

        result = main()

        assert result == 130
        mock_warning.assert_called_once_with("Operation cancelled by user")
        mock_info.assert_called_once_with("Goodbye! 👋")

    @patch("ccg.cli.print_error")
    @patch("ccg.cli.parse_args")
    def test_main_unexpected_exception(
        self, mock_parse: Mock, mock_error: Mock, capsys
    ) -> None:
        """Should return 1 on unexpected exception and print error details."""
        from ccg.cli import main

        mock_parse.side_effect = Exception("Unexpected error")

        result = main()

        assert result == 1
        mock_error.assert_called_once_with("An unexpected error occurred")
        # Verify the exception message is printed to stdout
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.out


class TestHandleDeleteRebaseDetection:
    """Test handle_delete rebase-in-progress detection."""

    @patch("ccg.cli.handle_commit_operation", return_value=0)
    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.run_git_command")
    @patch("ccg.cli.Path")
    def test_rebase_already_in_progress_user_cleans_up(
        self,
        mock_path: Mock,
        mock_run_git: Mock,
        mock_confirm: Mock,
        mock_operation: Mock,
    ) -> None:
        """Should detect existing rebase, clean up if user confirms, and continue with delete."""
        from ccg.cli import handle_delete

        # Mock Path to simulate rebase-merge directory exists
        mock_git_dir = Mock()
        mock_rebase_merge = Mock()
        mock_rebase_merge.exists.return_value = True
        mock_rebase_apply = Mock()
        mock_rebase_apply.exists.return_value = False

        mock_git_dir.__truediv__ = Mock(
            side_effect=lambda x: (
                mock_rebase_merge if x == "rebase-merge" else mock_rebase_apply
            )
        )
        mock_path.return_value = mock_git_dir

        mock_confirm.return_value = True  # User wants to clean up
        mock_run_git.return_value = (True, "")  # Cleanup succeeds

        result = handle_delete()

        # Should return 0 (success) and proceed to commit list after cleanup
        assert result == 0
        # Check that confirm was called
        mock_confirm.assert_called_once()
        # Check that rebase --abort was called
        mock_run_git.assert_called_once_with(["git", "rebase", "--abort"], "", "")
        # Check that handle_commit_operation was called to continue with delete
        mock_operation.assert_called_once_with("delete")

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.run_git_command")
    @patch("ccg.cli.Path")
    def test_rebase_already_in_progress_user_declines(
        self, mock_path: Mock, mock_run_git: Mock, mock_confirm: Mock
    ) -> None:
        """Should detect existing rebase before showing commits and exit if user declines cleanup."""
        from ccg.cli import handle_delete

        # Mock Path to simulate rebase-merge directory exists
        mock_git_dir = Mock()
        mock_rebase_merge = Mock()
        mock_rebase_merge.exists.return_value = True
        mock_rebase_apply = Mock()
        mock_rebase_apply.exists.return_value = False

        mock_git_dir.__truediv__ = Mock(
            side_effect=lambda x: (
                mock_rebase_merge if x == "rebase-merge" else mock_rebase_apply
            )
        )
        mock_path.return_value = mock_git_dir

        mock_confirm.return_value = False  # User declines cleanup

        result = handle_delete()

        # Should return 1 (error) and not proceed to commit list
        assert result == 1
        # Check that confirm was called
        mock_confirm.assert_called_once()
        # Check that rebase --abort was NOT called
        mock_run_git.assert_not_called()

    @patch("ccg.cli.confirm_user_action")
    @patch("ccg.cli.run_git_command")
    @patch("ccg.cli.Path")
    def test_rebase_cleanup_fails(
        self, mock_path: Mock, mock_run_git: Mock, mock_confirm: Mock
    ) -> None:
        """Should return error if rebase cleanup fails."""
        from ccg.cli import handle_delete

        # Mock Path to simulate rebase-merge directory exists
        mock_git_dir = Mock()
        mock_rebase_merge = Mock()
        mock_rebase_merge.exists.return_value = True
        mock_rebase_apply = Mock()
        mock_rebase_apply.exists.return_value = False

        mock_git_dir.__truediv__ = Mock(
            side_effect=lambda x: (
                mock_rebase_merge if x == "rebase-merge" else mock_rebase_apply
            )
        )
        mock_path.return_value = mock_git_dir

        mock_confirm.return_value = True  # User wants to clean up
        mock_run_git.return_value = (False, "Error")  # Cleanup fails

        result = handle_delete()

        # Should return 1 (error) when cleanup fails
        assert result == 1
        # Check that confirm was called
        mock_confirm.assert_called_once()
        # Check that rebase --abort was called
        mock_run_git.assert_called_once_with(["git", "rebase", "--abort"], "", "")

    @patch("ccg.cli.handle_commit_operation", return_value=0)
    @patch("ccg.cli.Path")
    def test_no_rebase_in_progress_proceeds_normally(
        self, mock_path: Mock, mock_operation: Mock
    ) -> None:
        """Should proceed to commit list when no rebase is in progress."""
        from ccg.cli import handle_delete

        # Mock Path to simulate NO rebase directories exist
        mock_git_dir = Mock()
        mock_rebase_merge = Mock()
        mock_rebase_merge.exists.return_value = False
        mock_rebase_apply = Mock()
        mock_rebase_apply.exists.return_value = False

        mock_git_dir.__truediv__ = Mock(
            side_effect=lambda x: (
                mock_rebase_merge if x == "rebase-merge" else mock_rebase_apply
            )
        )
        mock_path.return_value = mock_git_dir

        result = handle_delete()

        # Should proceed normally and call handle_commit_operation
        assert result == 0
        mock_operation.assert_called_once_with("delete")


class TestHandleAnalyze:
    """Tests for handle_analyze workflow."""

    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    def test_analyze_all_valid_commits(
        self, mock_count_input: Mock, mock_get_commits: Mock
    ) -> None:
        """Should show all commits as valid when they follow conventional commits."""
        mock_count_input.return_value = None
        mock_get_commits.return_value = [
            (
                "abc123def456",
                "abc123",
                "feat: add new feature",
                "John Doe",
                "2 days ago",
            ),
            ("def456ghi789", "def456", "fix: resolve bug", "Jane Doe", "1 day ago"),
        ]

        result = handle_analyze()

        assert result == 0
        mock_count_input.assert_called_once()
        mock_get_commits.assert_called_once_with(None)

    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    def test_analyze_some_invalid_commits(
        self, mock_count_input: Mock, mock_get_commits: Mock
    ) -> None:
        """Should show invalid commits with error messages."""
        mock_count_input.return_value = 5
        mock_get_commits.return_value = [
            (
                "abc123def456",
                "abc123",
                "feat: add new feature",
                "John Doe",
                "3 days ago",
            ),
            (
                "def456ghi789",
                "def456",
                "invalid commit message",
                "Jane Doe",
                "2 days ago",
            ),
            ("ghi789jkl012", "ghi789", "fix: resolve bug", "John Doe", "1 day ago"),
        ]

        result = handle_analyze()

        assert result == 0
        mock_count_input.assert_called_once()
        mock_get_commits.assert_called_once_with(5)

    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    def test_analyze_no_commits_found(
        self, mock_count_input: Mock, mock_get_commits: Mock
    ) -> None:
        """Should return 1 when no commits are found."""
        mock_count_input.return_value = None
        mock_get_commits.return_value = []

        result = handle_analyze()

        assert result == 1
        mock_count_input.assert_called_once()
        mock_get_commits.assert_called_once()

    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.get_commit_count_input")
    def test_analyze_all_invalid_commits(
        self, mock_count_input: Mock, mock_get_commits: Mock
    ) -> None:
        """Should show all commits as invalid when none follow conventional commits."""
        mock_count_input.return_value = 3
        mock_get_commits.return_value = [
            ("abc123def456", "abc123", "random message", "John Doe", "2 days ago"),
            ("def456ghi789", "def456", "another bad commit", "Jane Doe", "1 day ago"),
        ]

        result = handle_analyze()

        assert result == 0
        mock_count_input.assert_called_once()
        mock_get_commits.assert_called_once_with(3)
