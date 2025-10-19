"""Tests for the repository cache module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from ccg.cache import RepositoryCache, get_cache, invalidate_repository_cache


class TestRepositoryCache:
    """Test RepositoryCache class."""

    def test_init(self) -> None:
        """Should initialize cache with None values and current directory."""
        cache = RepositoryCache()

        assert cache._branch is None
        assert cache._repo_name is None
        assert cache._repo_root is None
        assert cache._remote_name is None
        assert cache._cached_cwd == os.getcwd()

    def test_invalidate_all(self) -> None:
        """Should clear all cached values."""
        cache = RepositoryCache()

        # Set some cached values
        cache._branch = "main"
        cache._repo_name = "my-repo"
        cache._repo_root = "/path/to/repo"
        cache._remote_name = "origin"

        # Invalidate
        cache.invalidate_all()

        # All should be None
        assert cache._branch is None
        assert cache._repo_name is None
        assert cache._repo_root is None
        assert cache._remote_name is None

    def test_invalidate_if_cwd_changed_no_change(self) -> None:
        """Should not invalidate if directory hasn't changed."""
        cache = RepositoryCache()

        # Set some cached values
        cache._branch = "main"
        cache._repo_name = "my-repo"

        # Call invalidate check (cwd hasn't changed)
        cache.invalidate_if_cwd_changed()

        # Values should still be cached
        assert cache._branch == "main"
        assert cache._repo_name == "my-repo"

    def test_invalidate_if_cwd_changed_with_change(self, tmp_path) -> None:
        """Should invalidate if directory has changed."""
        cache = RepositoryCache()

        # Set some cached values
        cache._branch = "main"
        cache._repo_name = "my-repo"

        # Save original cwd
        original_cwd = os.getcwd()

        try:
            # Change directory
            os.chdir(tmp_path)

            # Call invalidate check (cwd has changed)
            cache.invalidate_if_cwd_changed()

            # Values should be cleared
            assert cache._branch is None
            assert cache._repo_name is None
            assert cache._cached_cwd == str(tmp_path)

        finally:
            # Restore original directory
            os.chdir(original_cwd)

    def test_get_or_fetch_cached(self) -> None:
        """Should return cached value without calling fetcher."""
        cache = RepositoryCache()

        # Pre-populate cache
        cache._branch = "main"

        # Mock fetcher that should not be called
        fetcher = MagicMock(return_value="new-branch")

        # Get from cache
        result = cache.get_or_fetch("branch", fetcher)

        assert result == "main"
        fetcher.assert_not_called()

    def test_get_or_fetch_not_cached(self) -> None:
        """Should call fetcher and cache result when not cached."""
        cache = RepositoryCache()

        # Mock fetcher
        fetcher = MagicMock(return_value="main")

        # Get from fetcher (not cached yet)
        result = cache.get_or_fetch("branch", fetcher)

        assert result == "main"
        assert cache._branch == "main"
        fetcher.assert_called_once()

    def test_get_or_fetch_fetcher_returns_none(self) -> None:
        """Should cache None value if fetcher returns None."""
        cache = RepositoryCache()

        # Mock fetcher that returns None
        fetcher = MagicMock(return_value=None)

        # Get from fetcher
        result = cache.get_or_fetch("branch", fetcher)

        assert result is None
        assert cache._branch is None
        fetcher.assert_called_once()

    def test_get_or_fetch_checks_cwd(self, tmp_path) -> None:
        """Should invalidate cache if cwd changed before fetching."""
        cache = RepositoryCache()

        # Pre-populate cache
        cache._branch = "main"

        # Mock fetcher
        fetcher = MagicMock(return_value="new-branch")

        # Save original cwd
        original_cwd = os.getcwd()

        try:
            # Change directory
            os.chdir(tmp_path)

            # Get value (should invalidate first and call fetcher)
            result = cache.get_or_fetch("branch", fetcher)

            assert result == "new-branch"
            assert cache._branch == "new-branch"
            fetcher.assert_called_once()

        finally:
            # Restore original directory
            os.chdir(original_cwd)

    def test_get_or_fetch_multiple_keys(self) -> None:
        """Should handle caching for different keys independently."""
        cache = RepositoryCache()

        # Fetch different values for different keys
        branch_fetcher = MagicMock(return_value="main")
        repo_fetcher = MagicMock(return_value="my-repo")

        branch = cache.get_or_fetch("branch", branch_fetcher)
        repo = cache.get_or_fetch("repo_name", repo_fetcher)

        assert branch == "main"
        assert repo == "my-repo"
        assert cache._branch == "main"
        assert cache._repo_name == "my-repo"

        # Fetch again - should use cache
        branch2 = cache.get_or_fetch("branch", branch_fetcher)
        repo2 = cache.get_or_fetch("repo_name", repo_fetcher)

        assert branch2 == "main"
        assert repo2 == "my-repo"

        # Each fetcher should only be called once
        branch_fetcher.assert_called_once()
        repo_fetcher.assert_called_once()


class TestGlobalCache:
    """Test global cache functions."""

    def test_get_cache_returns_same_instance(self) -> None:
        """Should return the same global cache instance."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2

    def test_get_cache_is_repository_cache(self) -> None:
        """Should return RepositoryCache instance."""
        cache = get_cache()

        assert isinstance(cache, RepositoryCache)

    def test_invalidate_repository_cache(self) -> None:
        """Should invalidate the global cache."""
        cache = get_cache()

        # Set some values
        cache._branch = "main"
        cache._repo_name = "my-repo"

        # Invalidate
        invalidate_repository_cache()

        # Values should be cleared
        assert cache._branch is None
        assert cache._repo_name is None


class TestCacheIntegration:
    """Integration tests for cache with git operations."""

    @patch("ccg.git.run_git_command")
    def test_get_current_branch_caches_result(self, mock_run_git) -> None:
        """Should cache branch name and reuse it."""
        from ccg.git import get_current_branch

        # Setup mock
        mock_run_git.return_value = (True, "main")

        # Clear cache first
        invalidate_repository_cache()

        # First call should hit git
        branch1 = get_current_branch()
        assert branch1 == "main"
        assert mock_run_git.call_count == 1

        # Second call should use cache
        branch2 = get_current_branch()
        assert branch2 == "main"
        assert mock_run_git.call_count == 1  # Not called again

    @patch("ccg.git.run_git_command")
    def test_get_repository_name_caches_result(self, mock_run_git) -> None:
        """Should cache repository name and reuse it."""
        from ccg.git import get_repository_name

        # Setup mock
        mock_run_git.return_value = (True, "/path/to/my-repo")

        # Clear cache first
        invalidate_repository_cache()

        # First call should hit git
        name1 = get_repository_name()
        assert name1 == "my-repo"
        assert mock_run_git.call_count == 1

        # Second call should use cache
        name2 = get_repository_name()
        assert name2 == "my-repo"
        assert mock_run_git.call_count == 1  # Not called again

    @patch("ccg.git.run_git_command")
    def test_get_repository_root_caches_result(self, mock_run_git) -> None:
        """Should cache repository root and reuse it."""
        from ccg.git import get_repository_root

        # Setup mock
        mock_run_git.return_value = (True, "/path/to/my-repo")

        # Clear cache first
        invalidate_repository_cache()

        # First call should hit git
        root1 = get_repository_root()
        assert root1 == "/path/to/my-repo"
        assert mock_run_git.call_count == 1

        # Second call should use cache
        root2 = get_repository_root()
        assert root2 == "/path/to/my-repo"
        assert mock_run_git.call_count == 1  # Not called again

    @patch("ccg.git.run_git_command")
    @patch("ccg.git.print_error")
    def test_get_remote_name_caches_result(self, mock_print_error, mock_run_git) -> None:
        """Should cache remote name and reuse it."""
        from ccg.git import get_remote_name

        # Setup mock
        mock_run_git.return_value = (True, "origin")

        # Clear cache first
        invalidate_repository_cache()

        # First call should hit git
        remote1 = get_remote_name()
        assert remote1 == "origin"
        assert mock_run_git.call_count == 1

        # Second call should use cache
        remote2 = get_remote_name()
        assert remote2 == "origin"
        assert mock_run_git.call_count == 1  # Not called again

    @patch("ccg.git.run_git_command")
    @patch("ccg.git.ProgressSpinner")
    @patch("ccg.git.print_process")
    @patch("ccg.git.print_success")
    def test_git_commit_invalidates_cache(
        self, mock_print_success, mock_print_process, mock_spinner, mock_run_git
    ) -> None:
        """Should invalidate cache after successful commit."""
        from ccg.git import get_current_branch, git_commit

        # Setup mock spinner
        mock_spinner_instance = MagicMock()
        mock_spinner.return_value = mock_spinner_instance

        # Setup mock for git commands
        def git_command_side_effect(command, *args, **kwargs):
            if "rev-parse" in command:
                return (True, "main")
            elif "commit" in command:
                return (True, None)
            return (False, None)

        mock_run_git.side_effect = git_command_side_effect

        # Clear cache first
        invalidate_repository_cache()

        # Get branch (should cache it)
        branch1 = get_current_branch()
        assert branch1 == "main"

        # Commit (should invalidate cache)
        result = git_commit("test: commit message")
        assert result is True

        # Cache should be cleared
        cache = get_cache()
        assert cache._branch is None

    @patch("ccg.git.run_git_command")
    def test_cache_invalidates_on_directory_change(self, mock_run_git, tmp_path) -> None:
        """Should invalidate cache when changing directories."""
        from ccg.git import get_current_branch

        # Setup mock
        mock_run_git.side_effect = [
            (True, "main"),  # First call in original directory
            (True, "feature"),  # Second call in new directory
        ]

        # Clear cache first
        invalidate_repository_cache()

        # Save original cwd
        original_cwd = os.getcwd()

        try:
            # Get branch in original directory
            branch1 = get_current_branch()
            assert branch1 == "main"
            assert mock_run_git.call_count == 1

            # Change directory
            os.chdir(tmp_path)

            # Get branch again (should invalidate cache and fetch again)
            branch2 = get_current_branch()
            assert branch2 == "feature"
            assert mock_run_git.call_count == 2  # Called again due to directory change

        finally:
            # Restore original directory
            os.chdir(original_cwd)

    @patch("ccg.git.run_git_command")
    def test_multiple_cached_values_independent(self, mock_run_git) -> None:
        """Should cache multiple values independently."""
        from ccg.git import get_current_branch, get_remote_name, get_repository_name

        # Setup mock
        def git_command_side_effect(command, *args, **kwargs):
            if "rev-parse" in command and "--abbrev-ref" in command:
                return (True, "main")
            elif "rev-parse" in command and "--show-toplevel" in command:
                return (True, "/path/to/my-repo")
            elif "remote" in command:
                return (True, "origin")
            return (False, None)

        mock_run_git.side_effect = git_command_side_effect

        # Clear cache first
        invalidate_repository_cache()

        # Get all values (should cache each)
        branch = get_current_branch()
        repo_name = get_repository_name()
        remote = get_remote_name()

        assert branch == "main"
        assert repo_name == "my-repo"
        assert remote == "origin"
        assert mock_run_git.call_count == 3

        # Reset side effect for second round
        mock_run_git.side_effect = git_command_side_effect

        # Get all values again (should use cache)
        branch2 = get_current_branch()
        repo_name2 = get_repository_name()
        remote2 = get_remote_name()

        assert branch2 == "main"
        assert repo_name2 == "my-repo"
        assert remote2 == "origin"
        assert mock_run_git.call_count == 3  # Not called again
