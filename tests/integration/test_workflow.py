"""Integration tests for complete CCG workflows.

These tests verify end-to-end functionality by running real git operations
in temporary repositories, ensuring that all components work together correctly.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccg.core import generate_commit_message
from ccg.git import (
    delete_commit,
    edit_commit_message,
    get_commit_by_hash,
    get_recent_commits,
    get_staged_files,
    git_add,
    git_commit,
)
from ccg.repository import GitRepository


class TestCommitWorkflow:
    """Test complete commit creation workflow."""

    def test_stage_and_commit_workflow(self, temp_git_repo):
        """Test staging files and creating a commit."""
        # Change to temp repo directory
        temp_git_repo.enter()

        try:
            # Create a file
            temp_git_repo.write_file("test.txt", "test content")

            # Stage the file using CCG's git_add
            success = git_add()
            assert success is True

            # Verify file is staged
            staged = get_staged_files()
            assert "test.txt" in staged

            # Create commit using CCG's git_commit
            commit_message = "feat: add test file"
            success = git_commit(commit_message)
            assert success is True

            # Verify commit was created
            commit_hash = temp_git_repo.get_latest_commit_hash()
            assert len(commit_hash) == 40

            # Verify commit message
            message = temp_git_repo.get_commit_subject()
            assert message == commit_message

        finally:
            temp_git_repo.exit()

    def test_commit_with_body(self, temp_git_repo):
        """Test creating a commit with body text."""
        temp_git_repo.enter()

        try:
            # Create and stage file
            temp_git_repo.write_file("feature.txt", "new feature")
            git_add()

            # Commit with body
            message = "feat: add new feature\n\nThis is a detailed description\nof the feature."
            success = git_commit(message)
            assert success is True

            # Verify full commit message
            full_message = temp_git_repo.get_commit_message()
            assert "feat: add new feature" in full_message
            assert "This is a detailed description" in full_message

        finally:
            temp_git_repo.exit()

    def test_multiple_files_workflow(self, temp_git_repo):
        """Test staging and committing multiple files."""
        temp_git_repo.enter()

        try:
            # Create multiple files
            temp_git_repo.write_file("file1.txt", "content 1")
            temp_git_repo.write_file("file2.txt", "content 2")
            temp_git_repo.write_file("file3.txt", "content 3")

            # Stage all files
            success = git_add()
            assert success is True

            # Verify all files are staged
            staged = get_staged_files()
            assert "file1.txt" in staged
            assert "file2.txt" in staged
            assert "file3.txt" in staged

            # Commit
            success = git_commit("feat: add multiple files")
            assert success is True

            # Verify commit
            assert temp_git_repo.get_commit_count() == 1

        finally:
            temp_git_repo.exit()

    def test_repository_abstraction(self, temp_git_repo):
        """Test GitRepository abstraction for commit workflow."""
        temp_git_repo.enter()

        try:
            repo = GitRepository()

            # Verify we're in a git repo
            assert repo.is_git_repo() is True

            # Create and stage file
            temp_git_repo.write_file("abstract.txt", "testing abstraction")
            success = repo.add()
            assert success is True

            # Verify file is staged
            staged = repo.get_staged_files()
            assert "abstract.txt" in staged

            # Commit
            success = repo.commit("test: verify repository abstraction")
            assert success is True

            # Verify commit via repository
            commits = repo.get_recent_commits(count=1)
            assert len(commits) == 1
            assert "verify repository abstraction" in commits[0].subject

        finally:
            temp_git_repo.exit()


class TestEditCommitWorkflow:
    """Test commit editing workflows."""

    def test_edit_latest_commit(self, temp_git_repo_with_commits):
        """Test editing the latest commit message."""
        temp_git_repo_with_commits.enter()

        try:
            # Get latest commit hash
            original_hash = temp_git_repo_with_commits.get_latest_commit_hash()
            original_message = temp_git_repo_with_commits.get_commit_subject()

            # Edit the commit message
            new_message = "chore: updated file3"
            success = edit_commit_message(original_hash, new_message)
            assert success is True

            # Verify message changed (hash will change with amend)
            new_commit_message = temp_git_repo_with_commits.get_commit_subject()
            assert new_commit_message == new_message
            assert new_commit_message != original_message

        finally:
            temp_git_repo_with_commits.exit()

    def test_edit_latest_commit_with_body(self, temp_git_repo_with_commits):
        """Test editing latest commit with body text."""
        temp_git_repo_with_commits.enter()

        try:
            latest_hash = temp_git_repo_with_commits.get_latest_commit_hash()

            # Edit with body
            new_message = "chore: updated file3"
            new_body = "Added detailed description\nof the changes."
            success = edit_commit_message(latest_hash, new_message, new_body)
            assert success is True

            # Verify full message
            full_message = temp_git_repo_with_commits.get_commit_message()
            assert new_message in full_message
            assert "Added detailed description" in full_message

        finally:
            temp_git_repo_with_commits.exit()

    def test_edit_old_commit_with_filter_branch(self, temp_git_repo_with_commits):
        """Test editing an old commit using filter-branch.

        Note: This test verifies that the edit operation completes successfully.
        Verifying the exact message content after filter-branch is complex due to
        hash changes and is better tested in unit tests.
        """
        temp_git_repo_with_commits.enter()

        try:
            # Get the first commit (oldest)
            result = temp_git_repo_with_commits.run_git(["rev-list", "--max-parents=0", "HEAD"])
            first_commit_hash = result.stdout.strip()

            # Edit the old commit - just verify it succeeds
            new_message = "feat: updated initial commit"
            success = edit_commit_message(first_commit_hash, new_message)
            assert success is True

            # Verify repository still has 3 commits after edit
            assert temp_git_repo_with_commits.get_commit_count() == 3

        finally:
            temp_git_repo_with_commits.exit()

    def test_repository_edit_commit(self, temp_git_repo_with_commits):
        """Test editing commit via GitRepository abstraction."""
        temp_git_repo_with_commits.enter()

        try:
            repo = GitRepository()

            # Get latest commit
            commits = repo.get_recent_commits(count=1)
            latest_hash = commits[0].full_hash

            # Edit via repository
            success = repo.edit_commit_message(latest_hash, "chore: edited via repository")
            assert success is True

            # Verify change
            updated_commits = repo.get_recent_commits(count=1)
            assert "edited via repository" in updated_commits[0].subject

        finally:
            temp_git_repo_with_commits.exit()


class TestDeleteCommitWorkflow:
    """Test commit deletion workflows."""

    def test_delete_latest_commit(self, temp_git_repo_with_commits):
        """Test deleting the latest commit."""
        temp_git_repo_with_commits.enter()

        try:
            # Verify initial state
            initial_count = temp_git_repo_with_commits.get_commit_count()
            assert initial_count == 3

            latest_hash = temp_git_repo_with_commits.get_latest_commit_hash()

            # Delete latest commit
            success = delete_commit(latest_hash)
            assert success is True

            # Verify commit was deleted
            new_count = temp_git_repo_with_commits.get_commit_count()
            assert new_count == initial_count - 1

        finally:
            temp_git_repo_with_commits.exit()

    def test_delete_old_commit_with_rebase(self, temp_git_repo_with_commits):
        """Test deleting an old commit using rebase."""
        temp_git_repo_with_commits.enter()

        try:
            # Get the second commit
            result = temp_git_repo_with_commits.run_git(["rev-parse", "HEAD~1"])
            second_commit_hash = result.stdout.strip()

            initial_count = temp_git_repo_with_commits.get_commit_count()

            # Delete the second commit
            success = delete_commit(second_commit_hash)
            assert success is True

            # Verify commit count decreased
            new_count = temp_git_repo_with_commits.get_commit_count()
            assert new_count == initial_count - 1

        finally:
            temp_git_repo_with_commits.exit()

    def test_repository_delete_commit(self, temp_git_repo_with_commits):
        """Test deleting commit via GitRepository abstraction."""
        temp_git_repo_with_commits.enter()

        try:
            repo = GitRepository()

            # Get latest commit
            commits = repo.get_recent_commits(count=1)
            latest_hash = commits[0].full_hash

            initial_count = temp_git_repo_with_commits.get_commit_count()

            # Delete via repository
            success = repo.delete_commit(latest_hash)
            assert success is True

            # Verify deletion
            new_count = temp_git_repo_with_commits.get_commit_count()
            assert new_count == initial_count - 1

        finally:
            temp_git_repo_with_commits.exit()


class TestTagWorkflow:
    """Test tag creation workflows."""

    def test_create_lightweight_tag(self, temp_git_repo_with_commits):
        """Test creating a lightweight tag."""
        temp_git_repo_with_commits.enter()

        try:
            # Create tag via git module
            from ccg.git import create_tag

            success = create_tag("v1.0.0")
            assert success is True

            # Verify tag exists
            tags = temp_git_repo_with_commits.get_tags()
            assert "v1.0.0" in tags

        finally:
            temp_git_repo_with_commits.exit()

    def test_create_annotated_tag(self, temp_git_repo_with_commits):
        """Test creating an annotated tag with message."""
        temp_git_repo_with_commits.enter()

        try:
            from ccg.git import create_tag

            success = create_tag("v2.0.0", "Release version 2.0.0")
            assert success is True

            # Verify tag exists
            tags = temp_git_repo_with_commits.get_tags()
            assert "v2.0.0" in tags

            # Verify tag message
            result = temp_git_repo_with_commits.run_git(["tag", "-n", "-l", "v2.0.0"])
            assert "Release version 2.0.0" in result.stdout

        finally:
            temp_git_repo_with_commits.exit()

    def test_repository_create_tag(self, temp_git_repo_with_commits):
        """Test creating tag via GitRepository abstraction."""
        temp_git_repo_with_commits.enter()

        try:
            repo = GitRepository()

            # Create tag via repository
            success = repo.create_tag("v3.0.0", "Release 3.0.0")
            assert success is True

            # Verify tag
            tags = temp_git_repo_with_commits.get_tags()
            assert "v3.0.0" in tags

        finally:
            temp_git_repo_with_commits.exit()


class TestGetCommitInfo:
    """Test retrieving commit information."""

    def test_get_recent_commits(self, temp_git_repo_with_commits):
        """Test getting recent commits."""
        temp_git_repo_with_commits.enter()

        try:
            # Get all commits
            commits = get_recent_commits()
            assert len(commits) == 3

            # Verify commit structure
            for commit in commits:
                assert len(commit) == 5  # full_hash, short_hash, subject, author, date
                assert len(commit[0]) == 40  # full hash
                assert len(commit[1]) == 7  # short hash

            # Get limited commits
            limited = get_recent_commits(count=2)
            assert len(limited) == 2

        finally:
            temp_git_repo_with_commits.exit()

    def test_get_commit_by_hash(self, temp_git_repo_with_commits):
        """Test getting specific commit by hash."""
        temp_git_repo_with_commits.enter()

        try:
            latest_hash = temp_git_repo_with_commits.get_latest_commit_hash()

            # Get commit details
            commit = get_commit_by_hash(latest_hash)
            assert commit is not None
            assert len(commit) == 6  # includes body
            assert commit[0] == latest_hash

        finally:
            temp_git_repo_with_commits.exit()

    def test_repository_get_commits(self, temp_git_repo_with_commits):
        """Test getting commits via GitRepository abstraction."""
        temp_git_repo_with_commits.enter()

        try:
            repo = GitRepository()

            # Get recent commits as CommitInfo objects
            commits = repo.get_recent_commits(count=2)
            assert len(commits) == 2

            # Verify CommitInfo structure
            for commit in commits:
                assert hasattr(commit, "full_hash")
                assert hasattr(commit, "short_hash")
                assert hasattr(commit, "subject")
                assert hasattr(commit, "body")
                assert hasattr(commit, "author")
                assert hasattr(commit, "date")

            # Get specific commit
            latest_hash = temp_git_repo_with_commits.get_latest_commit_hash()
            commit = repo.get_commit_by_hash(latest_hash)
            assert commit is not None
            assert commit.full_hash == latest_hash

        finally:
            temp_git_repo_with_commits.exit()


class TestGenerateCommitMessage:
    """Test interactive commit message generation.

    Note: Interactive prompt testing is better suited for unit tests
    where we can mock the entire prompt_toolkit input mechanism.
    Integration tests focus on git operations that don't require
    interactive input.
    """

    pass  # Placeholder - interactive tests moved to unit tests
