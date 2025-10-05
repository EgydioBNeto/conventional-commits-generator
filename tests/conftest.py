"""Pytest configuration and shared fixtures."""

from typing import Any, Dict
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_subprocess_success() -> Mock:
    """Mock for successful subprocess run.

    Returns:
        Mock object configured to simulate successful subprocess execution
    """
    mock = Mock()
    mock.return_value = Mock(returncode=0, stdout="success output", stderr="")
    return mock


@pytest.fixture
def mock_subprocess_failure() -> Mock:
    """Mock for failed subprocess run.

    Returns:
        Mock object configured to simulate failed subprocess execution
    """
    mock = Mock()
    mock.return_value = Mock(returncode=1, stdout="", stderr="error output")
    return mock


@pytest.fixture
def valid_commit_messages() -> Dict[str, str]:
    """Collection of valid commit messages for testing.

    Returns:
        Dictionary mapping test cases to valid commit messages
    """
    return {
        "simple": "feat: add new feature",
        "with_scope": "fix(auth): resolve login bug",
        "breaking": "feat!: breaking change",
        "breaking_with_scope": "feat(api)!: breaking API change",
        "with_emoji": ":sparkles: feat: add sparkles",
        "all_types": [
            "feat: new feature",
            "fix: bug fix",
            "chore: maintenance",
            "refactor: code refactor",
            "style: formatting",
            "docs: documentation",
            "test: add tests",
            "build: build changes",
            "revert: revert changes",
            "ci: CI changes",
            "perf: performance",
        ],
    }


@pytest.fixture
def invalid_commit_messages() -> Dict[str, str]:
    """Collection of invalid commit messages for testing.

    Returns:
        Dictionary mapping test cases to invalid commit messages
    """
    return {
        "no_colon": "feat add feature",
        "invalid_type": "invalid: message",
        "empty_description": "feat: ",
        "only_type": "feat:",
        "no_space_after_colon": "feat:message",
        "invalid_scope": "feat(: invalid scope",
    }


@pytest.fixture
def emoji_conversions() -> Dict[str, str]:
    """Emoji code to real emoji mappings.

    Returns:
        Dictionary mapping emoji codes to their visual representation
    """
    return {
        ":sparkles:": "✨",
        ":bug:": "🐛",
        ":wrench:": "🔧",
        ":lipstick:": "💄",
        ":books:": "📚",
        ":rocket:": "🚀",
        ":recycle:": "♻️",
        ":white_check_mark:": "✅",
        ":hammer:": "🔨",
        ":rewind:": "⏪",
        ":construction_worker:": "👷",
        ":zap:": "⚡",
    }


@pytest.fixture
def mock_git_config() -> Dict[str, Any]:
    """Mock git configuration.

    Returns:
        Dictionary with mock git configuration values
    """
    return {
        "user.name": "Test User",
        "user.email": "test@example.com",
        "remote.origin.url": "https://github.com/test/repo.git",
        "branch": "main",
    }
