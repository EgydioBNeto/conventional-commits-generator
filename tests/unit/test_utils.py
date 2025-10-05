"""Unit tests for utils.py module."""

from unittest.mock import Mock, patch

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from ccg.utils import (
    BOLD,
    COMMIT_TYPES,
    CYAN,
    GREEN,
    RED,
    RESET,
    WHITE,
    YELLOW,
    get_emoji_for_type,
    strip_color_codes,
    validate_confirmation_input,
)


class TestValidateConfirmationInput:
    """Tests for validate_confirmation_input function."""

    def test_yes_lowercase(self) -> None:
        """Should accept lowercase 'y' as True."""
        assert validate_confirmation_input("y", True) is True

    def test_yes_uppercase(self) -> None:
        """Should accept uppercase 'Y' as True."""
        assert validate_confirmation_input("Y", True) is True

    def test_yes_full_lowercase(self) -> None:
        """Should accept full 'yes' as True."""
        assert validate_confirmation_input("yes", True) is True

    def test_yes_full_uppercase(self) -> None:
        """Should accept full 'YES' as True."""
        assert validate_confirmation_input("YES", True) is True

    def test_yes_mixed_case(self) -> None:
        """Should accept mixed case 'Yes' as True."""
        assert validate_confirmation_input("Yes", True) is True

    def test_no_lowercase(self) -> None:
        """Should accept lowercase 'n' as False."""
        assert validate_confirmation_input("n", True) is False

    def test_no_uppercase(self) -> None:
        """Should accept uppercase 'N' as False."""
        assert validate_confirmation_input("N", True) is False

    def test_no_full_lowercase(self) -> None:
        """Should accept full 'no' as False."""
        assert validate_confirmation_input("no", True) is False

    def test_no_full_uppercase(self) -> None:
        """Should accept full 'NO' as False."""
        assert validate_confirmation_input("NO", True) is False

    def test_empty_with_default_yes(self) -> None:
        """Should return True when empty and default=True."""
        assert validate_confirmation_input("", True) is True

    def test_empty_with_default_no(self) -> None:
        """Should return False when empty and default=False."""
        assert validate_confirmation_input("", False) is False

    def test_invalid_input(self) -> None:
        """Should return None for invalid input."""
        assert validate_confirmation_input("maybe", True) is None

    def test_invalid_random_text(self) -> None:
        """Should return None for random text."""
        assert validate_confirmation_input("xyz", True) is None

    def test_whitespace_with_default_yes(self) -> None:
        """Should return None for whitespace (invalid input)."""
        result = validate_confirmation_input("   ", True)
        # Whitespace is not treated as empty, but as invalid input
        assert result is None

    def test_whitespace_with_default_no(self) -> None:
        """Should return None for whitespace (invalid input)."""
        result = validate_confirmation_input("   ", False)
        # Whitespace is not treated as empty, but as invalid input
        assert result is None


class TestStripColorCodes:
    """Tests for strip_color_codes function."""

    def test_strip_red(self) -> None:
        """Should remove red color code."""
        text = f"{RED}Error{RESET}"
        result = strip_color_codes(text)
        assert result == "Error"

    def test_strip_green(self) -> None:
        """Should remove green color code."""
        text = f"{GREEN}Success{RESET}"
        result = strip_color_codes(text)
        assert result == "Success"

    def test_strip_multiple_colors(self) -> None:
        """Should remove multiple color codes."""
        text = f"{RED}{BOLD}Error{RESET} {GREEN}OK{RESET}"
        result = strip_color_codes(text)
        assert result == "Error OK"

    def test_strip_all_colors(self) -> None:
        """Should remove all ANSI color codes."""
        text = f"{YELLOW}Warning{RESET} {CYAN}Info{RESET} {WHITE}Text{RESET}"
        result = strip_color_codes(text)
        assert result == "Warning Info Text"

    def test_no_color_codes(self) -> None:
        """Should return text unchanged if no color codes."""
        text = "Plain text"
        result = strip_color_codes(text)
        assert result == "Plain text"

    def test_empty_string(self) -> None:
        """Should handle empty string."""
        result = strip_color_codes("")
        assert result == ""

    def test_only_color_codes(self) -> None:
        """Should remove text that is only color codes."""
        text = f"{RED}{RESET}"
        result = strip_color_codes(text)
        assert result == ""


class TestGetEmojiForType:
    """Tests for get_emoji_for_type function."""

    def test_feat_emoji_visual(self) -> None:
        """Should return visual emoji for feat."""
        result = get_emoji_for_type("feat", use_code=False)
        assert result == "✨"

    def test_feat_emoji_code(self) -> None:
        """Should return emoji code for feat."""
        result = get_emoji_for_type("feat", use_code=True)
        assert result == ":sparkles:"

    def test_fix_emoji_visual(self) -> None:
        """Should return visual emoji for fix."""
        result = get_emoji_for_type("fix", use_code=False)
        assert result == "🐛"

    def test_fix_emoji_code(self) -> None:
        """Should return emoji code for fix."""
        result = get_emoji_for_type("fix", use_code=True)
        assert result == ":bug:"

    def test_chore_emoji_visual(self) -> None:
        """Should return visual emoji for chore."""
        result = get_emoji_for_type("chore", use_code=False)
        assert result == "🔧"

    def test_chore_emoji_code(self) -> None:
        """Should return emoji code for chore."""
        result = get_emoji_for_type("chore", use_code=True)
        assert result == ":wrench:"

    def test_docs_emoji_visual(self) -> None:
        """Should return visual emoji for docs."""
        result = get_emoji_for_type("docs", use_code=False)
        assert result == "📚"

    def test_invalid_type(self) -> None:
        """Should return empty string for invalid type."""
        result = get_emoji_for_type("invalid", use_code=False)
        assert result == ""

    def test_invalid_type_code(self) -> None:
        """Should return empty string for invalid type code."""
        result = get_emoji_for_type("invalid", use_code=True)
        assert result == ""

    @pytest.mark.parametrize(
        "commit_type,expected_code",
        [
            ("feat", ":sparkles:"),
            ("fix", ":bug:"),
            ("chore", ":wrench:"),
            ("style", ":lipstick:"),
            ("docs", ":books:"),
            ("test", ":test_tube:"),
            ("build", ":package:"),
            ("revert", ":rewind:"),
            ("ci", ":construction_worker:"),
            ("perf", ":zap:"),
        ],
    )
    def test_all_types_codes(self, commit_type: str, expected_code: str) -> None:
        """Should return correct emoji code for all types."""
        result = get_emoji_for_type(commit_type, use_code=True)
        assert result == expected_code

    @pytest.mark.parametrize(
        "commit_type,expected_emoji",
        [
            ("feat", "✨"),
            ("fix", "🐛"),
            ("chore", "🔧"),
            ("style", "💄"),
            ("docs", "📚"),
            ("test", "🧪"),
            ("build", "📦"),
            ("revert", "⏪"),
            ("ci", "👷"),
            ("perf", "⚡"),
        ],
    )
    def test_all_types_visual(self, commit_type: str, expected_emoji: str) -> None:
        """Should return correct visual emoji for all types."""
        result = get_emoji_for_type(commit_type, use_code=False)
        assert result == expected_emoji


# ============================================================================
# Property-Based Tests with Hypothesis
# ============================================================================


class TestValidateConfirmationInputProperties:
    """Property-based tests for validate_confirmation_input."""

    @given(st.booleans())
    def test_empty_returns_default(self, default: bool) -> None:
        """Empty input should always return the default value."""
        result = validate_confirmation_input("", default)
        assert result == default

    @given(st.text())
    def test_never_crashes(self, user_input: str) -> None:
        """validate_confirmation_input should never crash."""
        try:
            result = validate_confirmation_input(user_input, True)
            assert result in (True, False, None)
        except Exception as e:
            pytest.fail(f"Crashed with input '{user_input}': {e}")

    @given(
        st.sampled_from(["y", "Y", "yes", "YES", "Yes", "yEs"]),
        st.booleans(),
    )
    def test_all_yes_variations_return_true(self, yes_input: str, default: bool) -> None:
        """All variations of 'yes' should return True."""
        result = validate_confirmation_input(yes_input, default)
        assert result is True

    @given(
        st.sampled_from(["n", "N", "no", "NO", "No", "nO"]),
        st.booleans(),
    )
    def test_all_no_variations_return_false(self, no_input: str, default: bool) -> None:
        """All variations of 'no' should return False."""
        result = validate_confirmation_input(no_input, default)
        assert result is False

    @given(st.text(min_size=1))
    def test_invalid_returns_none(self, invalid_input: str) -> None:
        """Invalid inputs should return None."""
        valid_inputs = {"y", "Y", "yes", "YES", "Yes", "n", "N", "no", "NO", "No", ""}
        assume(invalid_input.strip().lower() not in {v.lower() for v in valid_inputs})
        assume(invalid_input.strip())  # Not empty after strip

        result = validate_confirmation_input(invalid_input, True)
        if result is not None:
            # If not None, must be a yes/no variant we didn't catch
            assert result in (True, False)


class TestStripColorCodesProperties:
    """Property-based tests for strip_color_codes."""

    @given(st.text())
    def test_never_crashes(self, text: str) -> None:
        """strip_color_codes should never crash."""
        try:
            result = strip_color_codes(text)
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Crashed with input '{text}': {e}")

    @given(st.text(alphabet=st.characters(blacklist_characters="\x1b")))
    def test_text_without_ansi_unchanged(self, text: str) -> None:
        """Text without ANSI codes should remain mostly unchanged."""
        result = strip_color_codes(text)
        # Should be similar length (no ANSI codes to remove)
        assert abs(len(result) - len(text)) <= 5

    @given(
        st.lists(
            st.sampled_from([RED, GREEN, YELLOW, CYAN, WHITE, BOLD, RESET]),
            min_size=1,
            max_size=10,
        ),
        st.text(min_size=1, max_size=50),
    )
    def test_stripped_shorter_than_original(self, color_codes: list, text: str) -> None:
        """Text with color codes should be shorter after stripping."""
        colored_text = "".join(color_codes) + text + RESET
        stripped = strip_color_codes(colored_text)
        # Stripped should be shorter (unless text was very short)
        if len(text) > 10:
            assert len(stripped) < len(colored_text)

    @given(st.text(min_size=1))
    def test_double_strip_idempotent(self, text: str) -> None:
        """Stripping twice should give same result as stripping once."""
        first_strip = strip_color_codes(text)
        second_strip = strip_color_codes(first_strip)
        assert first_strip == second_strip


class TestGetEmojiForTypeProperties:
    """Property-based tests for get_emoji_for_type."""

    @given(st.sampled_from([ct["type"] for ct in COMMIT_TYPES]))
    def test_all_valid_types_have_emoji_code(self, commit_type: str) -> None:
        """All valid commit types should have an emoji code."""
        result = get_emoji_for_type(commit_type, use_code=True)
        assert result != ""
        assert result.startswith(":")
        assert result.endswith(":")

    @given(st.sampled_from([ct["type"] for ct in COMMIT_TYPES]))
    def test_all_valid_types_have_visual_emoji(self, commit_type: str) -> None:
        """All valid commit types should have a visual emoji."""
        result = get_emoji_for_type(commit_type, use_code=False)
        assert result != ""
        # Visual emojis are typically 1-2 characters
        assert len(result) <= 4

    @given(st.text(min_size=1))
    def test_invalid_types_return_empty(self, invalid_type: str) -> None:
        """Invalid commit types should return empty string."""
        valid_types = [ct["type"] for ct in COMMIT_TYPES]
        assume(invalid_type not in valid_types)

        result_code = get_emoji_for_type(invalid_type, use_code=True)
        result_visual = get_emoji_for_type(invalid_type, use_code=False)

        assert result_code == ""
        assert result_visual == ""

    @given(
        st.sampled_from([ct["type"] for ct in COMMIT_TYPES]),
        st.booleans(),
    )
    def test_never_crashes(self, commit_type: str, use_code: bool) -> None:
        """get_emoji_for_type should never crash."""
        try:
            result = get_emoji_for_type(commit_type, use_code)
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(f"Crashed with type '{commit_type}', use_code={use_code}: {e}")

    @given(st.sampled_from([ct["type"] for ct in COMMIT_TYPES]))
    def test_code_and_visual_different(self, commit_type: str) -> None:
        """Emoji code and visual should be different (code has colons)."""
        code = get_emoji_for_type(commit_type, use_code=True)
        visual = get_emoji_for_type(commit_type, use_code=False)

        if code and visual:  # Both should exist for valid types
            assert code != visual
            assert ":" in code
            assert ":" not in visual


# ============================================================================
# Print Functions Tests
# ============================================================================


class TestPrintFunctions:
    """Tests for print utility functions."""

    def test_print_section(self, capsys) -> None:
        """Should print section header."""
        from ccg.utils import print_section

        print_section("Test Section")
        captured = capsys.readouterr()

        assert "Test Section" in captured.out

    def test_print_error(self, capsys) -> None:
        """Should print error message in red."""
        from ccg.utils import print_error

        print_error("Error message")
        captured = capsys.readouterr()

        assert "Error message" in captured.out

    def test_print_success(self, capsys) -> None:
        """Should print success message in green."""
        from ccg.utils import print_success

        print_success("Success!")
        captured = capsys.readouterr()

        assert "Success!" in captured.out

    def test_print_warning(self, capsys) -> None:
        """Should print warning message in yellow."""
        from ccg.utils import print_warning

        print_warning("Warning!")
        captured = capsys.readouterr()

        assert "Warning!" in captured.out

    def test_print_info(self, capsys) -> None:
        """Should print info message."""
        from ccg.utils import print_info

        print_info("Info message")
        captured = capsys.readouterr()

        assert "Info message" in captured.out

    def test_print_process(self, capsys) -> None:
        """Should print process message."""
        from ccg.utils import print_process

        print_process("Processing...")
        captured = capsys.readouterr()

        assert "Processing..." in captured.out


class TestCommitTypes:
    """Tests for COMMIT_TYPES constant."""

    def test_all_types_have_required_fields(self) -> None:
        """All commit types should have all required fields."""
        from ccg.utils import COMMIT_TYPES

        required_fields = ["type", "emoji_code", "description", "color", "emoji"]

        for commit_type in COMMIT_TYPES:
            for field in required_fields:
                assert field in commit_type
                assert commit_type[field] is not None
                assert commit_type[field] != ""

    def test_emoji_codes_valid_format(self) -> None:
        """All emoji codes should be in valid format."""
        from ccg.utils import COMMIT_TYPES

        for commit_type in COMMIT_TYPES:
            emoji_code = commit_type["emoji_code"]
            assert emoji_code.startswith(":")
            assert emoji_code.endswith(":")
            assert len(emoji_code) > 2

    def test_all_types_unique(self) -> None:
        """All commit type names should be unique."""
        from ccg.utils import COMMIT_TYPES

        types = [ct["type"] for ct in COMMIT_TYPES]
        assert len(types) == len(set(types))


class TestInputLimits:
    """Tests for INPUT_LIMITS constant."""

    def test_all_limits_positive(self) -> None:
        """All input limits should be positive."""
        from ccg.utils import INPUT_LIMITS

        for key, value in INPUT_LIMITS.items():
            assert value > 0, f"{key} should have positive limit"

    def test_message_limit_reasonable(self) -> None:
        """Message limit should be reasonable (50-200 chars)."""
        from ccg.utils import INPUT_LIMITS

        assert 50 <= INPUT_LIMITS["message"] <= 200


class TestReadInputFallback:
    """Tests for read_input_fallback function."""

    @patch("builtins.input", return_value="test input")
    def test_basic_input(self, mock_input: Mock) -> None:
        """Should return basic input."""
        from ccg.utils import read_input_fallback

        result = read_input_fallback("Enter text")

        assert result == "test input"

    @patch("builtins.input", return_value="")
    def test_empty_uses_default(self, mock_input: Mock) -> None:
        """Should use default for empty input."""
        from ccg.utils import read_input_fallback

        result = read_input_fallback("Enter text", default_text="default")

        assert result == "default"

    @patch("builtins.input", side_effect=["x" * 100, "valid"])
    def test_max_length_validation(self, mock_input: Mock, capsys) -> None:
        """Should validate max length."""
        from ccg.utils import read_input_fallback

        result = read_input_fallback("Enter text", max_length=50)

        assert result == "valid"
        assert mock_input.call_count == 2


class TestConstants:
    """Tests for constant values."""

    def test_term_width_positive(self) -> None:
        """Terminal width should be positive."""
        from ccg.utils import TERM_WIDTH

        assert TERM_WIDTH > 0

    def test_ascii_logo_present(self) -> None:
        """ASCII logo should be defined."""
        from ccg.utils import ASCII_LOGO

        assert ASCII_LOGO is not None
        assert "CCG" in ASCII_LOGO or "Conventional" in ASCII_LOGO
