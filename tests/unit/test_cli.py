"""Unit tests for cli.py module."""

from unittest.mock import Mock, patch

import pytest

from ccg.cli import (
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
        assert args.path is None

    def test_parse_push_flag(self) -> None:
        """Should parse --push flag."""
        args = parse_args(["--push"])
        assert args.push is True

    def test_parse_commit_flag(self) -> None:
        """Should parse --commit flag."""
        args = parse_args(["--commit"])
        assert args.commit is True

    def test_parse_edit_flag(self) -> None:
        """Should parse --edit flag."""
        args = parse_args(["--edit"])
        assert args.edit is True

    def test_parse_delete_flag(self) -> None:
        """Should parse --delete flag."""
        args = parse_args(["--delete"])
        assert args.delete is True

    def test_parse_tag_flag(self) -> None:
        """Should parse --tag flag."""
        args = parse_args(["--tag"])
        assert args.tag is True

    def test_parse_reset_flag(self) -> None:
        """Should parse --reset flag."""
        args = parse_args(["--reset"])
        assert args.reset is True

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
    def test_show_info_with_none_values(self, mock_repo: Mock, mock_branch: Mock) -> None:
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
    def test_validate_nonexistent_path(self, mock_error: Mock, mock_exists: Mock) -> None:
        """Should exit when path doesn't exist."""
        mock_exists.return_value = False

        with pytest.raises(SystemExit):
            validate_paths_exist(["nonexistent.txt"])

        mock_error.assert_called()


class TestPushOnlyWorkflow:
    """Tests for push-only workflow."""

    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.git_push")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_success(
        self, mock_show: Mock, mock_check: Mock, mock_push: Mock, mock_branch: Mock
    ) -> None:
        """Should push successfully."""
        mock_check.return_value = True
        mock_push.return_value = True
        mock_branch.return_value = True  # Branch exists on remote

        result = handle_push_only()

        assert result == 0
        mock_push.assert_called_once()

    @patch("ccg.cli.branch_exists_on_remote")
    @patch("ccg.cli.git_push")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_push_only_failure(
        self, mock_show: Mock, mock_check: Mock, mock_push: Mock, mock_branch: Mock
    ) -> None:
        """Should return error code on push failure."""
        mock_check.return_value = True
        mock_push.return_value = False
        mock_branch.return_value = True  # Branch exists on remote

        result = handle_push_only()

        assert result == 1


class TestTagWorkflow:
    """Tests for tag creation workflow."""

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
    ) -> None:
        """Should create lightweight tag."""
        mock_check.return_value = True
        mock_input.return_value = "v1.0.0"
        mock_confirm.side_effect = [False, False]  # Not annotated (1st), don't push (2nd)
        mock_create.return_value = True

        result = handle_tag()

        assert result == 0
        mock_create.assert_called_once()

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
    ) -> None:
        """Should create annotated tag and push."""
        mock_check.return_value = True
        mock_input.side_effect = ["v1.0.0", "Release version 1.0.0"]
        mock_confirm.side_effect = [True, True]  # Annotated (1st), push (2nd)
        mock_create.return_value = True
        mock_push.return_value = True

        result = handle_tag()

        assert result == 0
        mock_push.assert_called_once()


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
    def test_reset_cancelled(self, mock_show: Mock, mock_check: Mock, mock_confirm: Mock) -> None:
        """Should cancel reset when user declines."""
        mock_check.return_value = True
        mock_confirm.return_value = False

        result = handle_reset()

        assert result == 0
