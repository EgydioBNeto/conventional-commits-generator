"""Git repository abstraction for better testability and maintainability.

This module provides a GitRepository class that encapsulates git operations with
state management, making the codebase more testable and easier to maintain.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ccg.cache import invalidate_repository_cache
from ccg.git import branch_exists_on_remote as _branch_exists_on_remote
from ccg.git import create_tag as _create_tag
from ccg.git import delete_commit as _delete_commit
from ccg.git import discard_local_changes as _discard_local_changes
from ccg.git import edit_commit_message as _edit_commit_message
from ccg.git import get_commit_by_hash as _get_commit_by_hash
from ccg.git import get_current_branch as _get_current_branch
from ccg.git import get_recent_commits as _get_recent_commits
from ccg.git import get_remote_name as _get_remote_name
from ccg.git import get_repository_name as _get_repository_name
from ccg.git import get_repository_root as _get_repository_root
from ccg.git import get_staged_file_changes as _get_staged_file_changes
from ccg.git import get_staged_files as _get_staged_files
from ccg.git import git_add as _git_add
from ccg.git import git_commit as _git_commit
from ccg.git import git_push as _git_push
from ccg.git import pull_from_remote as _pull_from_remote
from ccg.git import push_tag as _push_tag
from ccg.git import run_git_command

logger = logging.getLogger("ccg.repository")


@dataclass
class CommitInfo:
    """Information about a git commit.

    This dataclass provides a structured representation of commit metadata,
    making it easier to work with commit information throughout the application.
    """

    full_hash: str
    short_hash: str
    subject: str
    body: str
    author: str
    date: str

    @classmethod
    def from_tuple(cls, commit_tuple: Tuple[str, str, str, str, str, str]) -> "CommitInfo":
        """Create CommitInfo from a 6-element tuple.

        Args:
            commit_tuple: Tuple containing (full_hash, short_hash, subject,
                         body, author, date)

        Returns:
            CommitInfo instance populated with the tuple values
        """
        return cls(
            full_hash=commit_tuple[0],
            short_hash=commit_tuple[1],
            subject=commit_tuple[2],
            body=commit_tuple[3],
            author=commit_tuple[4],
            date=commit_tuple[5],
        )

    @classmethod
    def from_short_tuple(cls, commit_tuple: Tuple[str, str, str, str, str]) -> "CommitInfo":
        """Create CommitInfo from a 5-element tuple (without body).

        Args:
            commit_tuple: Tuple containing (full_hash, short_hash, subject,
                         author, date)

        Returns:
            CommitInfo instance with body set to empty string
        """
        return cls(
            full_hash=commit_tuple[0],
            short_hash=commit_tuple[1],
            subject=commit_tuple[2],
            body="",
            author=commit_tuple[3],
            date=commit_tuple[4],
        )


class GitRepository:
    """Encapsulate git operations with state management.

    This class provides an object-oriented interface to git operations, with
    internal caching and state tracking for better performance and testability.

    Example:
        >>> repo = GitRepository()
        >>> if repo.is_git_repo():
        ...     repo.add()
        ...     repo.commit("feat: add new feature")
        ...     repo.push()
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        """Initialize GitRepository instance.

        Args:
            path: Optional path to repository root (defaults to current working directory)
        """
        self.path = path or Path.cwd()
        logger.debug(f"Initialized GitRepository at {self.path}")

    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository.

        Returns:
            True if inside a git repository, False otherwise
        """
        success, _ = run_git_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            "Not a git repository",
            show_output=True,
        )
        return success

    def has_changes(self, paths: Optional[List[str]] = None) -> bool:
        """Check if there are uncommitted changes.

        Args:
            paths: Optional list of specific paths to check

        Returns:
            True if changes detected, False if working directory is clean
        """
        from ccg.git import check_has_changes

        return check_has_changes(paths)

    def get_current_branch(self) -> Optional[str]:
        """Get current branch name (cached).

        Returns:
            Branch name or None if unable to determine
        """
        return _get_current_branch()

    def get_repository_name(self) -> Optional[str]:
        """Get repository name (cached).

        Returns:
            Repository name or None if unable to determine
        """
        return _get_repository_name()

    def get_repository_root(self) -> Optional[str]:
        """Get repository root directory (cached).

        Returns:
            Absolute path to repository root or None if unable to determine
        """
        return _get_repository_root()

    def get_remote_name(self) -> Optional[str]:
        """Get primary remote name (cached).

        Returns:
            Remote name (typically 'origin') or None if no remote configured
        """
        return _get_remote_name()

    def branch_exists_on_remote(self, branch_name: str) -> bool:
        """Check if branch exists on remote repository.

        Args:
            branch_name: Name of the branch to check

        Returns:
            True if branch exists on remote, False otherwise
        """
        return _branch_exists_on_remote(branch_name)

    def get_staged_files(self) -> List[str]:
        """Get list of files staged for commit.

        Returns:
            List of file paths, empty list on error
        """
        return _get_staged_files()

    def get_staged_file_changes(self) -> List[Tuple[str, str]]:
        """Get list of staged files with their status.

        Returns:
            List of tuples (status, file_path), empty list on error
        """
        return _get_staged_file_changes()

    def get_recent_commits(self, count: Optional[int] = None) -> List[CommitInfo]:
        """Get list of recent commits.

        Args:
            count: Optional number of commits to retrieve (None = all)

        Returns:
            List of CommitInfo objects
        """
        commits = _get_recent_commits(count)
        return [CommitInfo.from_short_tuple(c) for c in commits]

    def get_commit_by_hash(self, commit_hash: str) -> Optional[CommitInfo]:
        """Get detailed commit information by hash.

        Args:
            commit_hash: Full or partial commit hash

        Returns:
            CommitInfo object or None if commit not found
        """
        commit = _get_commit_by_hash(commit_hash)
        if commit:
            return CommitInfo.from_tuple(commit)
        return None

    def add(self, paths: Optional[List[str]] = None) -> bool:
        """Stage changes for commit.

        Args:
            paths: Optional list of paths to stage (defaults to all changes)

        Returns:
            True if staging succeeded, False on error
        """
        return _git_add(paths)

    def commit(self, message: str) -> bool:
        """Create a commit with the specified message.

        Args:
            message: Commit message (should be in conventional commit format)

        Returns:
            True if commit created successfully, False on error

        Note:
            Automatically invalidates repository cache after successful commit
        """
        return _git_commit(message)

    def push(self, set_upstream: bool = False, force: bool = False) -> bool:
        """Push commits to remote repository.

        Args:
            set_upstream: If True, create remote branch with --set-upstream
            force: If True, force push (overwrites remote history)

        Returns:
            True if push succeeded, False on error
        """
        return _git_push(set_upstream=set_upstream, force=force)

    def pull(self) -> bool:
        """Pull latest changes from remote repository.

        Returns:
            True if pull succeeded, False on error
        """
        return _pull_from_remote()

    def create_tag(self, tag_name: str, message: Optional[str] = None) -> bool:
        """Create a git tag.

        Args:
            tag_name: Name of the tag (e.g., "v1.0.0")
            message: Optional tag message (creates annotated tag if provided)

        Returns:
            True if tag created successfully, False on error
        """
        return _create_tag(tag_name, message)

    def push_tag(self, tag_name: str) -> bool:
        """Push a tag to remote repository.

        Args:
            tag_name: Name of the tag to push

        Returns:
            True if tag pushed successfully, False on error
        """
        return _push_tag(tag_name)

    def edit_commit_message(
        self, commit_hash: str, new_message: str, new_body: Optional[str] = None
    ) -> bool:
        """Edit a commit message.

        Automatically chooses the most efficient method (amend or filter-branch)
        based on whether the commit is the latest or an older one.

        Args:
            commit_hash: Full hash of commit to edit
            new_message: New commit subject line
            new_body: Optional new commit body

        Returns:
            True if edit succeeded, False on error

        Note:
            Editing old commits rewrites history and changes descendant hashes
        """
        return _edit_commit_message(commit_hash, new_message, new_body)

    def delete_commit(self, commit_hash: str) -> bool:
        """Delete a commit.

        Automatically chooses the most efficient method (reset or rebase)
        based on whether the commit is the latest or an older one.

        Args:
            commit_hash: Full or partial hash of commit to delete

        Returns:
            True if deletion succeeded, False on error

        Note:
            DESTRUCTIVE - Commit is permanently removed from history
        """
        return _delete_commit(commit_hash)

    def discard_local_changes(self) -> bool:
        """Discard all local changes and untracked files.

        Returns:
            True if changes discarded successfully, False on error

        Note:
            DESTRUCTIVE - This cannot be undone
        """
        return _discard_local_changes()

    def invalidate_cache(self) -> None:
        """Invalidate repository cache.

        Call this after operations that change repository state.
        """
        invalidate_repository_cache()
