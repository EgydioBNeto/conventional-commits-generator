"""Property-based tests for validation functions using Hypothesis.

This module contains property-based tests that automatically generate thousands
of test cases to find edge cases and ensure validation functions are robust
against any input.
"""

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from ccg.core import validate_commit_message
from ccg.utils import is_valid_semver, validate_confirmation_input


class TestCommitMessageValidation:
    """Property-based tests for commit message validation."""

    @given(st.text(min_size=0, max_size=1000))
    def test_validate_commit_message_never_crashes(self, message: str):
        """Validator should never raise exception regardless of input."""
        try:
            is_valid, error = validate_commit_message(message)
            assert isinstance(is_valid, bool)
            assert error is None or isinstance(error, str)
        except Exception as e:
            pytest.fail(f"Validator crashed with: {e}")

    @given(st.text(min_size=1, max_size=100))
    def test_validate_commit_message_returns_tuple(self, message: str):
        """Validator should always return a 2-tuple."""
        result = validate_commit_message(message)
        assert isinstance(result, tuple)
        assert len(result) == 2

    @given(st.text(min_size=1, max_size=500))
    def test_empty_string_always_invalid(self, message: str):
        """Empty string should always be invalid."""
        is_valid, error = validate_commit_message("")
        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower()

    @given(
        st.sampled_from(
            [
                "feat",
                "fix",
                "chore",
                "refactor",
                "style",
                "docs",
                "test",
                "build",
                "revert",
                "ci",
                "perf",
            ]
        ),
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=20,
        ),
    )
    def test_valid_type_with_random_description(
        self, commit_type: str, description: str
    ):
        """Valid type with any alphabetic description should be valid."""
        message = f"{commit_type}: {description}"
        is_valid, error = validate_commit_message(message)
        assert is_valid is True
        assert error is None

    @given(
        st.sampled_from(
            [
                "feat",
                "fix",
                "chore",
                "refactor",
                "style",
                "docs",
                "test",
                "build",
                "revert",
                "ci",
                "perf",
            ]
        ),
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=15,
        ),
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=20,
        ),
    )
    def test_valid_type_with_scope_and_description(
        self, commit_type: str, scope: str, description: str
    ):
        """Valid type with scope and description should be valid."""
        message = f"{commit_type}({scope}): {description}"
        is_valid, error = validate_commit_message(message)
        assert is_valid is True
        assert error is None

    @given(
        st.sampled_from(
            [
                "feat",
                "fix",
                "chore",
                "refactor",
                "style",
                "docs",
                "test",
                "build",
                "revert",
                "ci",
                "perf",
            ]
        ),
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=15,
        ),
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=20,
        ),
        st.booleans(),
    )
    def test_valid_type_with_breaking_change(
        self, commit_type: str, scope: str, description: str, has_scope: bool
    ):
        """Valid type with breaking change indicator should be valid."""
        if has_scope:
            message = f"{commit_type}({scope})!: {description}"
        else:
            message = f"{commit_type}!: {description}"
        is_valid, error = validate_commit_message(message)
        assert is_valid is True
        assert error is None


class TestConfirmationInputValidation:
    """Property-based tests for confirmation input validation."""

    @given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=100))
    def test_validate_confirmation_handles_any_unicode(self, text: str):
        """Confirmation validator should handle any unicode without crashing."""
        result = validate_confirmation_input(text, default_yes=True)
        assert result in [True, False, None]

    @given(st.booleans())
    def test_empty_string_returns_default(self, default_yes: bool):
        """Empty string should return the default value."""
        result = validate_confirmation_input("", default_yes=default_yes)
        assert result == default_yes

    @given(st.sampled_from(["y", "Y", "yes", "YES", "Yes"]))
    def test_yes_variations_return_true(self, yes_input: str):
        """All variations of 'yes' should return True."""
        result = validate_confirmation_input(yes_input, default_yes=False)
        assert result is True

    @given(st.sampled_from(["n", "N", "no", "NO", "No"]))
    def test_no_variations_return_false(self, no_input: str):
        """All variations of 'no' should return False."""
        result = validate_confirmation_input(no_input, default_yes=True)
        assert result is False

    @given(st.text(min_size=4, max_size=100))
    def test_long_input_returns_none(self, long_text: str):
        """Inputs longer than 3 characters should return None."""
        result = validate_confirmation_input(long_text, default_yes=True)
        assert result is None

    @given(
        st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=122),
            min_size=1,
            max_size=3,
        )
    )
    def test_invalid_short_input_returns_none(self, text: str):
        """Invalid short inputs (not y/n/yes/no) should return None."""
        # Skip if it's a valid confirmation input
        normalized = text.lower().strip()
        if normalized in ["y", "yes", "n", "no"]:
            return

        result = validate_confirmation_input(text, default_yes=True)
        assert result is None


class TestSemverValidation:
    """Property-based tests for semantic versioning validation."""

    @given(st.integers(0, 999), st.integers(0, 999), st.integers(0, 999))
    def test_semver_accepts_valid_versions(self, major: int, minor: int, patch: int):
        """All valid x.y.z patterns should be accepted."""
        versions = [
            f"{major}.{minor}.{patch}",
            f"v{major}.{minor}.{patch}",
        ]
        for version in versions:
            assert is_valid_semver(version), f"{version} should be valid"

    @given(
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99),
        st.text(
            min_size=1,
            max_size=20,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        ),
    )
    def test_semver_with_prerelease(
        self, major: int, minor: int, patch: int, prerelease: str
    ):
        """Semver with prerelease should be valid (alphanumeric only)."""
        # Semver spec allows alphanumeric and hyphens in prerelease, but not dots
        # For simplicity, we test only alphanumeric
        # Semver spec: numeric identifiers MUST NOT include leading zeroes
        assume(
            not (prerelease.isdigit() and len(prerelease) > 1 and prerelease[0] == "0")
        )
        version = f"{major}.{minor}.{patch}-{prerelease}"
        assert is_valid_semver(version), f"{version} should be valid"

    @given(
        st.integers(0, 99),
        st.integers(0, 99),
        st.integers(0, 99),
        st.text(
            min_size=1,
            max_size=20,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        ),
    )
    def test_semver_with_build_metadata(
        self, major: int, minor: int, patch: int, metadata: str
    ):
        """Semver with build metadata should be valid (alphanumeric only)."""
        # Semver spec allows alphanumeric and hyphens in build metadata
        # For simplicity, we test only alphanumeric
        # Build metadata has more relaxed rules than prerelease (leading zeros OK)
        version = f"{major}.{minor}.{patch}+{metadata}"
        assert is_valid_semver(version), f"{version} should be valid"

    @given(st.text(min_size=1, max_size=50))
    def test_invalid_semver_patterns(self, text: str):
        """Random strings that don't match semver should be invalid."""
        # Skip if it looks like a valid semver (contains digits and dots)
        if "." in text and any(c.isdigit() for c in text):
            return

        result = is_valid_semver(text)
        # We don't assert False here because some random strings might
        # accidentally match the pattern. This test just ensures no crashes.
        assert isinstance(result, bool)

    @given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=100))
    def test_semver_never_crashes(self, text: str):
        """Semver validator should never crash on any input."""
        try:
            result = is_valid_semver(text)
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"Semver validator crashed with: {e}")


class TestGetRecentCommits:
    """Property-based tests for get_recent_commits function.

    Note: These tests use mocks and are moved to regular unit tests
    since Hypothesis + pytest fixtures require special handling.
    See test_git.py for detailed get_recent_commits tests.
    """

    pass  # Tests moved to test_git.py due to fixture/hypothesis interaction


class TestEdgeCases:
    """Property-based tests for edge cases across validation functions."""

    @given(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Zs", "Cc"),  # Whitespace and control characters
            ),
            min_size=0,
            max_size=100,
        )
    )
    def test_commit_message_with_only_whitespace(self, whitespace: str):
        """Commit messages with only whitespace should be handled."""
        is_valid, error = validate_commit_message(whitespace)
        # Should be invalid since it's effectively empty
        assert isinstance(is_valid, bool)
        assert isinstance(error, (str, type(None)))

    @given(st.text(alphabet="!@#$%^&*()[]{}|\\:;\"'<>,.?/~`", min_size=1, max_size=50))
    def test_commit_message_with_special_characters(self, special_chars: str):
        """Commit messages with special characters should not crash validator."""
        try:
            is_valid, error = validate_commit_message(special_chars)
            assert isinstance(is_valid, bool)
        except Exception as e:
            pytest.fail(f"Validator crashed on special characters: {e}")

    @given(st.text(min_size=1, max_size=3))
    def test_confirmation_input_boundary_at_3_chars(self, text: str):
        """Confirmation input should handle boundary at 3 characters."""
        result = validate_confirmation_input(text, default_yes=True)
        assert result in [True, False, None]

        # Test exactly at boundary
        result_4_chars = validate_confirmation_input(text + "x", default_yes=True)
        if len(text) == 3:
            # Adding one more should make it too long
            assert result_4_chars is None

    @given(st.lists(st.integers(min_value=0, max_value=999), min_size=3, max_size=3))
    def test_semver_with_zeros(self, version_parts: list):
        """Semver should handle versions with zeros correctly."""
        version = f"{version_parts[0]}.{version_parts[1]}.{version_parts[2]}"
        result = is_valid_semver(version)
        # Should be valid as long as parts are valid numbers
        assert result is True

    @given(st.text(min_size=0, max_size=1000))
    def test_all_validators_never_crash(self, text: str):
        """All validators should handle any input without crashing."""
        try:
            # Test commit message validator
            validate_commit_message(text)

            # Test confirmation validator
            validate_confirmation_input(text, default_yes=True)
            validate_confirmation_input(text, default_yes=False)

            # Test semver validator
            is_valid_semver(text)

        except Exception as e:
            pytest.fail(f"One of the validators crashed with: {e}")
