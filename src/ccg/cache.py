"""Repository information cache to reduce redundant git command calls.

This module provides a caching layer for frequently accessed repository information
like current branch, repository name, and root directory. This reduces latency by
eliminating redundant git command executions.
"""

import os
from typing import Callable, Optional


class RepositoryCache:
    """Cache repository information within a single CCG execution.

    This cache automatically invalidates when the working directory changes,
    and can be manually invalidated after operations that modify repository state.
    """

    def __init__(self) -> None:
        """Initialize the repository cache."""
        self._branch: Optional[str] = None
        self._repo_name: Optional[str] = None
        self._repo_root: Optional[str] = None
        self._remote_name: Optional[str] = None
        self._cwd_at_init: str = os.getcwd()

    def invalidate_if_cwd_changed(self) -> None:
        """Invalidate cache if working directory changed."""
        current_cwd = os.getcwd()
        if current_cwd != self._cwd_at_init:
            self.invalidate_all()
            self._cwd_at_init = current_cwd

    def invalidate_all(self) -> None:
        """Clear all cached values."""
        self._branch = None
        self._repo_name = None
        self._repo_root = None
        self._remote_name = None

    def get_or_fetch(self, key: str, fetcher: Callable[[], Optional[str]]) -> Optional[str]:
        """Generic cached getter with lazy loading.

        Args:
            key: The cache key (e.g., 'branch', 'repo_name')
            fetcher: Callable that fetches the value if not cached

        Returns:
            The cached or freshly fetched value
        """
        self.invalidate_if_cwd_changed()

        cached: Optional[str] = getattr(self, f"_{key}", None)
        if cached is not None:
            return cached

        value = fetcher()
        setattr(self, f"_{key}", value)
        return value


# Global cache instance
_repo_cache = RepositoryCache()


def get_cache() -> RepositoryCache:
    """Get the global repository cache instance.

    Returns:
        The global RepositoryCache instance
    """
    return _repo_cache


def invalidate_repository_cache() -> None:
    """Invalidate the repository cache.

    Call this after operations that change repository state (e.g., commit, checkout).
    """
    _repo_cache.invalidate_all()
