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


class TestHandleCommitOperation:
    """Tests for handle_commit_operation function."""

    @patch("ccg.cli.edit_specific_commit")
    @patch("ccg.cli.read_input")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_edit_by_number(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_commits: Mock,
        mock_input: Mock,
        mock_edit: Mock,
    ) -> None:
        """Should select commit by number for editing."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
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
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_delete_by_hash(
        self,
        mock_show: Mock,
        mock_check: Mock,
        mock_commits: Mock,
        mock_input: Mock,
        mock_delete: Mock,
    ) -> None:
        """Should select commit by hash for deleting."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
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
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_quit_operation(
        self, mock_show: Mock, mock_check: Mock, mock_commits: Mock, mock_input: Mock
    ) -> None:
        """Should quit on 'q' input."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_commits.return_value = [("abc123", "abc", "feat: test", "Author", "1 day ago")]
        mock_input.side_effect = ["", "q"]

        result = handle_commit_operation("edit")

        assert result == 0

    @patch("ccg.cli.read_input")
    @patch("ccg.cli.get_recent_commits")
    @patch("ccg.cli.check_is_git_repo")
    @patch("ccg.cli.show_repository_info")
    def test_invalid_then_valid_selection(
        self, mock_show: Mock, mock_check: Mock, mock_commits: Mock, mock_input: Mock
    ) -> None:
        """Should retry on invalid selection."""
        from ccg.cli import handle_commit_operation

        mock_check.return_value = True
        mock_commits.return_value = [("abc123", "abc", "feat: test", "Author", "1 day ago")]
        mock_input.side_effect = ["", "999", "1"]  # Invalid number, then valid

        with patch("ccg.cli.edit_specific_commit", return_value=0):
            result = handle_commit_operation("edit")

        assert result == 0


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

        mock_get.return_value = ("abc123", "abc", "feat: old", "", "Author", "1 day ago")
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

        mock_get.return_value = ("abc123", "abc", "feat: test", "", "Author", "1 day ago")
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

        mock_get.return_value = ("abc123", "abc", "feat: test", "", "Author", "1 day ago")
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

        mock_get.return_value = ("abc123", "abc", "feat: test", "", "Author", "1 day ago")
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
    def test_workflow_commit_only_mode(self, mock_validate: Mock, mock_generate: Mock) -> None:
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
    def test_single_directory_changes_dir(self, mock_exists: Mock, mock_isdir: Mock) -> None:
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
