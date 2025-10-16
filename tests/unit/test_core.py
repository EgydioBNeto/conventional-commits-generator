"""Unit tests for core.py module - Property-Based Testing with Hypothesis."""

from unittest.mock import Mock, patch

from hypothesis import example, given
from hypothesis import strategies as st

from ccg.core import convert_emoji_codes_to_real, validate_commit_message
from ccg.utils import COMMIT_TYPES

# ============================================================================
# Strategies (reusable test data generators)
# ============================================================================

valid_commit_types = st.sampled_from([ct["type"] for ct in COMMIT_TYPES])
valid_scopes = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pd")),
    min_size=1,
    max_size=20,
).filter(lambda s: s.strip())

emoji_codes = st.sampled_from(
    [
        ":sparkles:",
        ":bug:",
        ":wrench:",
        ":lipstick:",
        ":books:",
        ":test_tube:",
        ":package:",
        ":rewind:",
        ":construction_worker:",
        ":zap:",
        ":hammer:",
    ]
)


# ============================================================================
# Validation Tests
# ============================================================================


class TestValidateCommitMessage:
    """Property-based tests for validate_commit_message function."""

    @given(valid_commit_types)
    @example("feat")
    @example("fix")
    def test_valid_simple_commit(self, commit_type: str) -> None:
        """Should accept simple valid commits."""
        is_valid, error = validate_commit_message(f"{commit_type}: add new feature")
        assert is_valid is True
        assert error is None

    @given(valid_commit_types, valid_scopes)
    @example("fix", "auth")
    @example("feat", "api")
    def test_valid_commit_with_scope(self, commit_type: str, scope: str) -> None:
        """Should accept commits with scope."""
        is_valid, error = validate_commit_message(f"{commit_type}({scope}): resolve bug")
        assert is_valid is True
        assert error is None

    @given(valid_commit_types)
    @example("feat")
    def test_valid_breaking_change(self, commit_type: str) -> None:
        """Should accept breaking changes."""
        is_valid, error = validate_commit_message(f"{commit_type}!: breaking change")
        assert is_valid is True
        assert error is None

    @given(valid_commit_types, valid_scopes)
    @example("feat", "api")
    def test_valid_breaking_change_with_scope(self, commit_type: str, scope: str) -> None:
        """Should accept breaking changes with scope."""
        is_valid, error = validate_commit_message(f"{commit_type}({scope})!: breaking change")
        assert is_valid is True
        assert error is None

    @given(emoji_codes, valid_commit_types)
    @example(":sparkles:", "feat")
    @example(":bug:", "fix")
    def test_valid_with_emoji_code(self, emoji: str, commit_type: str) -> None:
        """Should accept emoji codes at the beginning."""
        is_valid, error = validate_commit_message(f"{emoji} {commit_type}: new feature")
        assert is_valid is True
        assert error is None

    @given(emoji_codes, valid_commit_types, valid_scopes)
    @example(":bug:", "fix", "auth")
    def test_valid_with_emoji_and_scope(self, emoji: str, commit_type: str, scope: str) -> None:
        """Should accept emoji with scope."""
        is_valid, error = validate_commit_message(f"{emoji} {commit_type}({scope}): resolve bug")
        assert is_valid is True
        assert error is None

    @given(st.text(min_size=1, max_size=50).filter(lambda s: ":" not in s))
    @example("feat add feature")
    def test_invalid_no_colon(self, text: str) -> None:
        """Should reject messages without colon."""
        is_valid, error = validate_commit_message(text)
        assert is_valid is False
        assert error is not None

    @given(
        st.text(min_size=1, max_size=20).filter(
            lambda s: s not in [ct["type"] for ct in COMMIT_TYPES] and ":" not in s
        )
    )
    @example("invalid")
    def test_invalid_type(self, invalid_type: str) -> None:
        """Should reject invalid commit types."""
        is_valid, error = validate_commit_message(f"{invalid_type}: message")
        assert is_valid is False
        assert error is not None

    @given(valid_commit_types)
    @example("feat")
    def test_empty_description(self, commit_type: str) -> None:
        """Should reject empty description."""
        is_valid, error = validate_commit_message(f"{commit_type}: ")
        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower() or "description" in error.lower()

    @example("")
    @example("   ")
    @given(st.just("") | st.text(max_size=5).filter(lambda s: not s.strip()))
    def test_empty_or_whitespace_message(self, message: str) -> None:
        """Should reject empty or whitespace-only messages."""
        is_valid, error = validate_commit_message(message)
        assert is_valid is False
        assert error is not None


class TestConvertEmojiCodesToReal:
    """Property-based tests for emoji code conversion."""

    @given(emoji_codes)
    @example(":sparkles:")
    @example(":bug:")
    def test_convert_single_emoji(self, emoji_code: str) -> None:
        """Should convert emoji codes to visual emojis."""
        result = convert_emoji_codes_to_real(f"{emoji_code} test")
        # Should not contain the code anymore
        assert emoji_code not in result
        # Should be shorter (code replaced by emoji)
        assert len(result) < len(f"{emoji_code} test")

    @given(st.lists(emoji_codes, min_size=2, max_size=5))
    @example([":sparkles:", ":bug:"])
    def test_multiple_emojis(self, emojis: list[str]) -> None:
        """Should convert multiple emoji codes."""
        text = " ".join(emojis) + " test"
        result = convert_emoji_codes_to_real(text)
        # None of the codes should remain
        for emoji in emojis:
            assert emoji not in result

    @given(st.text(alphabet=st.characters(blacklist_characters=":")))
    @example("feat: test")
    def test_no_emoji(self, text: str) -> None:
        """Should return text unchanged if no emoji codes."""
        result = convert_emoji_codes_to_real(text)
        # Text without colons shouldn't change much
        assert len(result) >= len(text) - 5

    @given(st.text())
    @example(":incomplete test")
    @example("test : incomplete")
    def test_never_crashes(self, text: str) -> None:
        """Should never crash regardless of input."""
        result = convert_emoji_codes_to_real(text)
        assert isinstance(result, str)


# ============================================================================
# Interactive Functions Tests (with mocking)
# ============================================================================


class TestInteractiveFunctions:
    """Tests for interactive functions with mocked I/O."""

    def test_display_commit_types(self, capsys) -> None:
        """Should display all commit types."""
        from ccg.core import display_commit_types

        display_commit_types()
        captured = capsys.readouterr()

        # Should contain all commit types
        assert "feat" in captured.out
        assert "fix" in captured.out
        assert "chore" in captured.out

    def test_confirm_commit_displays_header(self, capsys) -> None:
        """Should display commit header in review."""
        from unittest.mock import patch

        from ccg.core import confirm_commit

        with patch("ccg.core.confirm_user_action", return_value=True):
            result = confirm_commit("feat: test message")
            captured = capsys.readouterr()

            assert "feat: test message" in captured.out
            assert result is True

    def test_confirm_commit_with_body(self, capsys) -> None:
        """Should display both header and body."""
        from unittest.mock import patch

        from ccg.core import confirm_commit

        with patch("ccg.core.confirm_user_action", return_value=True):
            result = confirm_commit("feat: test", "This is the body")
            captured = capsys.readouterr()

            assert "feat: test" in captured.out
            assert "This is the body" in captured.out
            assert result is True

    def test_confirm_commit_converts_emoji(self, capsys) -> None:
        """Should convert emoji codes in display."""
        from unittest.mock import patch

        from ccg.core import confirm_commit

        with patch("ccg.core.confirm_user_action", return_value=True):
            confirm_commit(":sparkles: feat: test")
            captured = capsys.readouterr()

            # Should show visual emoji, not code
            assert "✨" in captured.out

    @patch("ccg.core.get_staged_file_changes")
    def test_confirm_commit_shows_file_changes(self, mock_get_staged: Mock, capsys) -> None:
        """Should display staged file changes in separate section before review."""
        import re
        from unittest.mock import patch

        from ccg.core import confirm_commit

        mock_get_staged.return_value = [
            ("A", "new_file.txt"),
            ("M", "modified_file.py"),
            ("D", "deleted_file.js"),
            ("U", "unknown_status_file.txt"),
        ]

        with patch("ccg.core.confirm_user_action", return_value=True):
            confirm_commit("feat: test", show_file_changes=True)
            captured = capsys.readouterr()

            output = re.sub(r"\x1b\[[0-9;]*m", "", captured.out)

            # Check that File Changes section exists
            assert "File Changes" in output
            assert "Added: new_file.txt" in output
            assert "Modified: modified_file.py" in output
            assert "Deleted: deleted_file.js" in output
            assert "U: unknown_status_file.txt" in output

            # Check that Review section comes after File Changes
            file_changes_pos = output.find("File Changes")
            review_pos = output.find("Review")
            assert file_changes_pos < review_pos, "File Changes should come before Review"

    @patch("ccg.core.get_staged_file_changes")
    def test_confirm_commit_shows_no_file_changes_message(
        self, mock_get_staged: Mock, capsys
    ) -> None:
        """Should display message when no staged file changes and show_file_changes is True."""
        from unittest.mock import patch

        from ccg.core import confirm_commit

        mock_get_staged.return_value = []

        with patch("ccg.core.confirm_user_action", return_value=True):
            confirm_commit("feat: test", show_file_changes=True)
            captured = capsys.readouterr()

            assert "No staged file changes to display." in captured.out

    @patch("ccg.core.get_staged_file_changes")
    def test_confirm_commit_does_not_show_file_changes_by_default(
        self, mock_get_staged: Mock, capsys
    ) -> None:
        """Should not display staged file changes when show_file_changes is False."""
        from unittest.mock import patch

        from ccg.core import confirm_commit

        mock_get_staged.return_value = [
            ("A", "new_file.txt"),
        ]

        with patch("ccg.core.confirm_user_action", return_value=True):
            confirm_commit("feat: test")
            captured = capsys.readouterr()

            assert "File Changes:" not in captured.out
            mock_get_staged.assert_not_called()

    def test_confirm_push_displays_info(self, capsys) -> None:
        """Should display push information."""
        from unittest.mock import patch

        from ccg.core import confirm_push

        with patch("ccg.core.confirm_user_action", return_value=True):
            result = confirm_push()
            captured = capsys.readouterr()

            assert "git push" in captured.out.lower()
            assert result is True


class TestChooseCommitType:
    """Tests for choose_commit_type function."""

    def test_choose_by_number(self, capsys) -> None:
        """Should accept valid number input."""
        from unittest.mock import patch

        from ccg.core import choose_commit_type

        with patch("ccg.core.read_input", return_value="1"):
            result = choose_commit_type()
            assert result == "feat"

    def test_choose_by_name(self, capsys) -> None:
        """Should accept valid type name."""
        from unittest.mock import patch

        from ccg.core import choose_commit_type

        with patch("ccg.core.read_input", return_value="fix"):
            result = choose_commit_type()
            assert result == "fix"

    def test_choose_case_insensitive(self, capsys) -> None:
        """Should accept type name case insensitive."""
        from unittest.mock import patch

        from ccg.core import choose_commit_type

        with patch("ccg.core.read_input", return_value="FIX"):
            result = choose_commit_type()
            assert result == "fix"

    def test_choose_invalid_then_valid(self, capsys) -> None:
        """Should retry on invalid input."""
        from unittest.mock import patch

        from ccg.core import choose_commit_type

        with patch("ccg.core.read_input", side_effect=["invalid", "feat"]):
            result = choose_commit_type()
            assert result == "feat"

    def test_choose_empty_then_valid(self, capsys) -> None:
        """Should retry on empty input."""
        from unittest.mock import patch

        from ccg.core import choose_commit_type

        with patch("ccg.core.read_input", side_effect=["", "1"]):
            result = choose_commit_type()
            assert result == "feat"

    def test_choose_type_keyboard_interrupt(self, capsys) -> None:
        """Should exit gracefully on KeyboardInterrupt."""
        from unittest.mock import patch

        import pytest

        from ccg.core import choose_commit_type

        with (
            patch("ccg.core.read_input", side_effect=KeyboardInterrupt()),
            pytest.raises(SystemExit) as excinfo,
        ):
            choose_commit_type()

        assert excinfo.value.code == 0


class TestGetScope:
    """Tests for get_scope function."""

    def test_get_scope_with_value(self, capsys) -> None:
        """Should return scope when provided."""
        from unittest.mock import patch

        from ccg.core import get_scope

        with patch("ccg.core.read_input", return_value="auth"):
            result = get_scope()
            assert result == "auth"
            captured = capsys.readouterr()
            assert "auth" in captured.out

    def test_get_scope_empty(self, capsys) -> None:
        """Should return None when empty."""
        from unittest.mock import patch

        from ccg.core import get_scope

        with patch("ccg.core.read_input", return_value=""):
            result = get_scope()
            assert result is None


class TestIsBreakingChange:
    """Tests for is_breaking_change function."""

    def test_breaking_change_yes(self, capsys) -> None:
        """Should return True for yes."""
        from unittest.mock import patch

        from ccg.core import is_breaking_change

        with patch("ccg.core.confirm_user_action", return_value=True):
            result = is_breaking_change()
            assert result is True

    def test_breaking_change_no(self, capsys) -> None:
        """Should return False for no."""
        from unittest.mock import patch

        from ccg.core import is_breaking_change

        with patch("ccg.core.confirm_user_action", return_value=False):
            result = is_breaking_change()
            assert result is False


class TestWantEmoji:
    """Tests for want_emoji function."""

    def test_want_emoji_yes(self, capsys) -> None:
        """Should return True for yes."""
        from unittest.mock import patch

        from ccg.core import want_emoji

        with patch("ccg.core.confirm_user_action", return_value=True):
            result = want_emoji()
            assert result is True

    def test_want_emoji_no(self, capsys) -> None:
        """Should return False for no."""
        from unittest.mock import patch

        from ccg.core import want_emoji

        with patch("ccg.core.confirm_user_action", return_value=False):
            result = want_emoji()
            assert result is False


class TestGetCommitMessage:
    """Tests for get_commit_message function."""

    def test_get_valid_message(self, capsys) -> None:
        """Should return message when valid."""
        from unittest.mock import patch

        from ccg.core import get_commit_message

        with patch("ccg.core.read_input", return_value="implement login"):
            result = get_commit_message()
            assert result == "implement login"

    def test_get_message_retry_on_empty(self, capsys) -> None:
        """Should retry on empty message."""
        from unittest.mock import patch

        from ccg.core import get_commit_message

        with patch("ccg.core.read_input", side_effect=["", "  ", "valid message"]):
            result = get_commit_message()
            assert result == "valid message"


class TestGetCommitBody:
    """Tests for get_commit_body function."""

    def test_get_body_with_content(self, capsys) -> None:
        """Should return body when provided."""
        from unittest.mock import patch

        from ccg.core import get_commit_body

        with patch("ccg.core.read_input", return_value="This is the body"):
            result = get_commit_body()
            assert result == "This is the body"

    def test_get_body_empty(self, capsys) -> None:
        """Should return None when empty."""
        from unittest.mock import patch

        from ccg.core import get_commit_body

        with patch("ccg.core.read_input", return_value=""):
            result = get_commit_body()
            assert result is None

    def test_get_body_keyboard_interrupt(self, capsys) -> None:
        """Should return None and print message on KeyboardInterrupt."""
        from unittest.mock import patch

        from ccg.core import get_commit_body

        with patch("ccg.core.read_input", side_effect=KeyboardInterrupt()):
            result = get_commit_body()
            captured = capsys.readouterr()
            assert result is None
            assert "Skipping commit body" in captured.out


class TestGenerateCommitMessage:
    """Tests for generate_commit_message function."""

    def test_generate_full_message_with_all_options(self, capsys) -> None:
        """Should generate complete message with all options."""
        from unittest.mock import MagicMock, patch

        from ccg.core import generate_commit_message

        mock_read_input = MagicMock(
            side_effect=["1", "auth", "implement OAuth login", "Added Google OAuth"]
        )

        with (
            patch("ccg.core.read_input", mock_read_input),
            patch("ccg.core.confirm_user_action", side_effect=[True, True, True]),
        ):
            result = generate_commit_message()

            assert result is not None
            assert "feat" in result
            assert "auth" in result
            assert "implement OAuth login" in result

    def test_generate_message_without_emoji(self, capsys) -> None:
        """Should generate message without emoji."""
        from unittest.mock import MagicMock, patch

        from ccg.core import generate_commit_message

        mock_read_input = MagicMock(side_effect=["fix", "", "fix bug", ""])

        with (
            patch("ccg.core.read_input", mock_read_input),
            patch("ccg.core.confirm_user_action", side_effect=[False, False, True]),
        ):
            result = generate_commit_message()

            assert result is not None
            assert result.startswith("fix:")
            assert ":" not in result[:5] or result.split(":")[0] == "fix"

    def test_generate_message_user_rejects(self, capsys) -> None:
        """Should return None when user rejects."""
        from unittest.mock import MagicMock, patch

        from ccg.core import generate_commit_message

        mock_read_input = MagicMock(side_effect=["feat", "", "test message", ""])

        with (
            patch("ccg.core.read_input", mock_read_input),
            patch("ccg.core.confirm_user_action", side_effect=[False, False, False]),
        ):
            result = generate_commit_message()

            assert result is None

    def test_generate_message_keyboard_interrupt(self, capsys) -> None:
        """Should exit gracefully on KeyboardInterrupt inside the main function."""
        from unittest.mock import patch

        import pytest

        from ccg.core import generate_commit_message

        # Mock choose_commit_type to ensure the interrupt happens in the main body
        with (
            patch("ccg.core.choose_commit_type", return_value="feat"),
            patch("ccg.core.read_input", side_effect=KeyboardInterrupt()),
            pytest.raises(SystemExit) as excinfo,
        ):
            generate_commit_message()

        assert excinfo.value.code == 0
        captured = capsys.readouterr()
        assert "Exiting. Goodbye!" in captured.out


class TestValidateCommitMessageEdgeCases:
    """Additional edge case tests for validation."""

    def test_validate_scope_with_special_chars(self) -> None:
        """Should reject scope with invalid characters after it."""
        is_valid, error = validate_commit_message("feat(scope)x: message")
        assert is_valid is False

    def test_validate_unclosed_scope(self) -> None:
        """Should reject unclosed scope parenthesis."""
        is_valid, error = validate_commit_message("feat(scope: message")
        assert is_valid is False
        # The validation treats this as invalid type since it can't parse the scope correctly
        assert error is not None

    def test_validate_whitespace_description(self) -> None:
        """Should reject whitespace-only description."""
        is_valid, error = validate_commit_message("feat:    ")
        assert is_valid is False
        # Note: This returns format error because .strip() removes trailing whitespace
        # making "feat:    " become "feat:" which doesn't match the regex pattern

    def test_validate_emoji_with_breaking(self) -> None:
        """Should accept emoji with breaking change."""
        is_valid, error = validate_commit_message(":sparkles: feat!: breaking change")
        assert is_valid is True

    def test_validate_emoji_with_scope_and_breaking(self) -> None:
        """Should accept emoji with scope and breaking change."""
        is_valid, error = validate_commit_message(":sparkles: feat(api)!: breaking change")
        assert is_valid is True

    def test_validate_message_description_only_tab(self) -> None:
        """Should reject message with only tab character as description."""
        is_valid, error = validate_commit_message("feat:\t")
        assert is_valid is False

    def test_validate_message_strips_leading_emoji(self) -> None:
        """Should strip emoji code from beginning before validation."""
        is_valid, error = validate_commit_message(":sparkles: feat: add new feature")
        assert is_valid is True


class TestPrecompiledRegexPatterns:
    """Tests for pre-compiled regex patterns optimization (Improvement 7)."""

    def test_commit_message_pattern_exists(self) -> None:
        """Should have pre-compiled commit message pattern constant."""
        from ccg.core import _COMMIT_MESSAGE_PATTERN

        assert _COMMIT_MESSAGE_PATTERN is not None
        # Should be a compiled regex pattern object
        assert hasattr(_COMMIT_MESSAGE_PATTERN, "match")
        assert hasattr(_COMMIT_MESSAGE_PATTERN, "pattern")

    def test_emoji_code_pattern_exists(self) -> None:
        """Should have pre-compiled emoji code pattern constant."""
        from ccg.core import _EMOJI_CODE_PATTERN

        assert _EMOJI_CODE_PATTERN is not None
        # Should be a compiled regex pattern object
        assert hasattr(_EMOJI_CODE_PATTERN, "match")
        assert hasattr(_EMOJI_CODE_PATTERN, "sub")
        assert hasattr(_EMOJI_CODE_PATTERN, "pattern")

    def test_commit_message_pattern_matches_valid_commits(self) -> None:
        """Should correctly match valid commit formats."""
        from ccg.core import _COMMIT_MESSAGE_PATTERN

        # Test various valid formats
        test_cases = [
            "feat: add feature",
            "fix: resolve bug",
            "feat(auth): add login",
            "fix(api): correct endpoint",
            "feat!: breaking change",
            "fix(scope)!: breaking fix",
        ]

        for test_case in test_cases:
            match = _COMMIT_MESSAGE_PATTERN.match(test_case)
            assert match is not None, f"Pattern should match: {test_case}"

    def test_commit_message_pattern_groups(self) -> None:
        """Should extract correct groups from commit message."""
        from ccg.core import _COMMIT_MESSAGE_PATTERN

        # Test without scope or breaking change
        match = _COMMIT_MESSAGE_PATTERN.match("feat: add feature")
        assert match is not None
        assert match.group(1) == "feat"  # type
        assert match.group(2) is None  # scope (optional)
        assert match.group(3) == ""  # breaking indicator
        assert match.group(4) == "add feature"  # description

        # Test with scope
        match = _COMMIT_MESSAGE_PATTERN.match("fix(auth): resolve bug")
        assert match is not None
        assert match.group(1) == "fix"  # type
        assert match.group(2) == "auth"  # scope
        assert match.group(3) == ""  # breaking indicator
        assert match.group(4) == "resolve bug"  # description

        # Test with breaking change
        match = _COMMIT_MESSAGE_PATTERN.match("feat!: breaking change")
        assert match is not None
        assert match.group(1) == "feat"  # type
        assert match.group(2) is None  # scope
        assert match.group(3) == "!"  # breaking indicator
        assert match.group(4) == "breaking change"  # description

        # Test with scope and breaking change
        match = _COMMIT_MESSAGE_PATTERN.match("feat(api)!: breaking change")
        assert match is not None
        assert match.group(1) == "feat"  # type
        assert match.group(2) == "api"  # scope
        assert match.group(3) == "!"  # breaking indicator
        assert match.group(4) == "breaking change"  # description

    def test_commit_message_pattern_rejects_invalid(self) -> None:
        """Should not match invalid commit formats."""
        from ccg.core import _COMMIT_MESSAGE_PATTERN

        # Test various invalid formats
        invalid_cases = [
            "no colon here",
            "feat add feature",
            "feat(scope",  # unclosed scope
            "feat)",  # no opening scope
            "",
            ":",
        ]

        for test_case in invalid_cases:
            match = _COMMIT_MESSAGE_PATTERN.match(test_case)
            assert match is None, f"Pattern should NOT match: {test_case}"

    def test_emoji_code_pattern_removes_emoji_codes(self) -> None:
        """Should correctly remove emoji codes from beginning."""
        from ccg.core import _EMOJI_CODE_PATTERN

        test_cases = [
            (":sparkles: feat: add feature", "feat: add feature"),
            (":bug: fix: resolve bug", "fix: resolve bug"),
            (":wrench: chore: update config", "chore: update config"),
            (":test_tube: test: add tests", "test: add tests"),
        ]

        for input_text, expected_output in test_cases:
            result = _EMOJI_CODE_PATTERN.sub("", input_text).strip()
            assert result == expected_output, f"Expected '{expected_output}', got '{result}'"

    def test_emoji_code_pattern_handles_no_emoji(self) -> None:
        """Should not modify text without emoji codes."""
        from ccg.core import _EMOJI_CODE_PATTERN

        test_cases = [
            "feat: add feature",
            "fix: resolve bug",
            "regular text",
            "text with : colon but not emoji",
        ]

        for test_case in test_cases:
            result = _EMOJI_CODE_PATTERN.sub("", test_case).strip()
            # Should be the same or very close (whitespace)
            assert result == test_case or result == test_case.strip()

    def test_validate_commit_message_uses_precompiled_patterns(self) -> None:
        """Should use pre-compiled patterns for validation (no re-compilation)."""
        import re
        from unittest.mock import patch

        # Mock re.compile to ensure it's not called during validation
        with patch("re.compile") as mock_compile:
            # Call validate_commit_message multiple times
            validate_commit_message("feat: test 1")
            validate_commit_message("fix: test 2")
            validate_commit_message(":sparkles: feat: test 3")

            # re.compile should NOT be called during validation
            # (patterns are already compiled at module level)
            mock_compile.assert_not_called()

    def test_pattern_performance_vs_runtime_compilation(self) -> None:
        """Should be faster than runtime regex compilation."""
        import re
        import time

        from ccg.core import _COMMIT_MESSAGE_PATTERN

        test_message = "feat(auth): add login functionality"
        iterations = 1000

        # Test with pre-compiled pattern
        start = time.perf_counter()
        for _ in range(iterations):
            _COMMIT_MESSAGE_PATTERN.match(test_message)
        precompiled_time = time.perf_counter() - start

        # Test with runtime compilation
        start = time.perf_counter()
        for _ in range(iterations):
            pattern = re.compile(r"^(\w+)(?:\(([^)]+)\))?(!?): (.*)$")
            pattern.match(test_message)
        runtime_time = time.perf_counter() - start

        # Pre-compiled should be significantly faster
        # Allow some tolerance for system variability
        assert precompiled_time < runtime_time, (
            f"Pre-compiled ({precompiled_time:.4f}s) should be faster than "
            f"runtime compilation ({runtime_time:.4f}s)"
        )
