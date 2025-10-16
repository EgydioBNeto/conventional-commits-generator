"""Pytest fixtures for integration tests.

This module provides fixtures for creating temporary git repositories
and executing real git operations for end-to-end testing.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Generator, List, Optional

import pytest


class TempGitRepo:
    """Helper class for managing a temporary git repository."""

    def __init__(self, path: Path) -> None:
        """Initialize temporary git repository.

        Args:
            path: Path to the temporary directory
        """
        self.path = path
        self.original_cwd = Path.cwd()

    def run_git(
        self, args: List[str], check: bool = True, capture: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a git command in the repository.

        Args:
            args: Git command arguments (e.g., ['add', '.'])
            check: Whether to raise exception on non-zero exit
            capture: Whether to capture stdout/stderr

        Returns:
            CompletedProcess with command results
        """
        cmd = ["git"] + args
        kwargs: dict[str, Any] = {"cwd": self.path, "check": check}

        if capture:
            kwargs["capture_output"] = True
            kwargs["text"] = True

        return subprocess.run(cmd, **kwargs)

    def init(self) -> None:
        """Initialize git repository with basic configuration."""
        self.run_git(["init"])
        self.run_git(["config", "user.name", "Test User"])
        self.run_git(["config", "user.email", "test@example.com"])
        # Disable GPG signing for tests
        self.run_git(["config", "commit.gpgsign", "false"])

    def write_file(self, filename: str, content: str) -> Path:
        """Write a file in the repository.

        Args:
            filename: Name of the file to create
            content: Content to write

        Returns:
            Path to the created file
        """
        file_path = self.path / filename
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def add(self, paths: Optional[List[str]] = None) -> None:
        """Stage files for commit.

        Args:
            paths: Optional list of paths to stage (defaults to all)
        """
        if paths:
            self.run_git(["add"] + paths)
        else:
            self.run_git(["add", "."])

    def commit(self, message: str) -> str:
        """Create a commit.

        Args:
            message: Commit message

        Returns:
            Full commit hash
        """
        self.run_git(["commit", "-m", message])
        result = self.run_git(["rev-parse", "HEAD"])
        return result.stdout.strip()

    def get_commit_message(self, commit_hash: str = "HEAD") -> str:
        """Get commit message for a commit.

        Args:
            commit_hash: Commit hash or ref (defaults to HEAD)

        Returns:
            Full commit message (subject + body)
        """
        result = self.run_git(["log", "-1", "--format=%B", commit_hash])
        return result.stdout.strip()

    def get_commit_subject(self, commit_hash: str = "HEAD") -> str:
        """Get commit subject line.

        Args:
            commit_hash: Commit hash or ref (defaults to HEAD)

        Returns:
            Commit subject (first line)
        """
        result = self.run_git(["log", "-1", "--format=%s", commit_hash])
        return result.stdout.strip()

    def get_latest_commit_hash(self) -> str:
        """Get the full hash of the latest commit.

        Returns:
            Full commit hash of HEAD
        """
        result = self.run_git(["rev-parse", "HEAD"])
        return result.stdout.strip()

    def get_short_hash(self, commit_hash: str = "HEAD") -> str:
        """Get short hash for a commit.

        Args:
            commit_hash: Commit hash or ref (defaults to HEAD)

        Returns:
            Short (7-character) commit hash
        """
        result = self.run_git(["rev-parse", "--short", commit_hash])
        return result.stdout.strip()

    def get_commit_count(self) -> int:
        """Get total number of commits in repository.

        Returns:
            Number of commits
        """
        result = self.run_git(["rev-list", "--count", "HEAD"])
        return int(result.stdout.strip())

    def create_tag(self, tag_name: str, message: Optional[str] = None) -> None:
        """Create a git tag.

        Args:
            tag_name: Name of the tag
            message: Optional tag message (creates annotated tag)
        """
        if message:
            self.run_git(["tag", "-a", tag_name, "-m", message])
        else:
            self.run_git(["tag", tag_name])

    def get_tags(self) -> List[str]:
        """Get list of all tags.

        Returns:
            List of tag names
        """
        result = self.run_git(["tag", "-l"])
        output = result.stdout.strip()
        return output.split("\n") if output else []

    def has_changes(self) -> bool:
        """Check if there are uncommitted changes.

        Returns:
            True if there are changes, False if clean
        """
        result = self.run_git(["status", "--porcelain"])
        return bool(result.stdout.strip())

    def enter(self) -> None:
        """Change working directory to repository."""
        os.chdir(self.path)

    def exit(self) -> None:
        """Restore original working directory."""
        os.chdir(self.original_cwd)


@pytest.fixture
def temp_git_repo() -> Generator[TempGitRepo, None, None]:
    """Create a temporary git repository for testing.

    Yields:
        TempGitRepo instance with initialized repository

    Example:
        def test_commit(temp_git_repo):
            temp_git_repo.write_file("test.txt", "content")
            temp_git_repo.add()
            commit_hash = temp_git_repo.commit("test: initial commit")
            assert len(commit_hash) == 40
    """
    temp_dir = tempfile.mkdtemp(prefix="ccg_test_")
    temp_path = Path(temp_dir)

    try:
        repo = TempGitRepo(temp_path)
        repo.init()
        yield repo
    finally:
        # Clean up temporary directory
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_git_repo_with_commits() -> Generator[TempGitRepo, None, None]:
    """Create a temporary git repository with initial commits.

    Yields:
        TempGitRepo instance with 3 initial commits

    Example:
        def test_edit_old_commit(temp_git_repo_with_commits):
            commits = temp_git_repo_with_commits.get_commit_count()
            assert commits == 3
    """
    temp_dir = tempfile.mkdtemp(prefix="ccg_test_")
    temp_path = Path(temp_dir)

    try:
        repo = TempGitRepo(temp_path)
        repo.init()

        # Create initial commits
        repo.write_file("file1.txt", "content 1")
        repo.add()
        repo.commit("feat: add file1")

        repo.write_file("file2.txt", "content 2")
        repo.add()
        repo.commit("fix: add file2")

        repo.write_file("file3.txt", "content 3")
        repo.add()
        repo.commit("chore: add file3")

        yield repo
    finally:
        # Clean up temporary directory
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)
