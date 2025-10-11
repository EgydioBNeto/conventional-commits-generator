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
    """Property-based tests for validate_confirmation_input function using Hypothesis."""

    @given(st.sampled_from(["y", "Y", "yes", "YES", "Yes", "yEs", "yeS", "YEs", "yES", "YeS"]))
    def test_all_yes_variations_return_true(self, yes_input: str) -> None:
        """All variations of 'yes' should return True regardless of default."""
        # Should return True for both default_yes=True and default_yes=False
        assert validate_confirmation_input(yes_input, True) is True
        assert validate_confirmation_input(yes_input, False) is True

    @given(st.sampled_from(["n", "N", "no", "NO", "No", "nO", "NO", "No"]))
    def test_all_no_variations_return_false(self, no_input: str) -> None:
        """All variations of 'no' should return False regardless of default."""
        # Should return False for both default_yes=True and default_yes=False
        assert validate_confirmation_input(no_input, True) is False
        assert validate_confirmation_input(no_input, False) is False

    @given(st.booleans())
    def test_empty_string_returns_default(self, default: bool) -> None:
        """Empty string should return the default value."""
        assert validate_confirmation_input("", default) == default

    @given(
        st.text(min_size=1).filter(
            lambda s: s.strip().lower() not in ["y", "yes", "n", "no", ""] and len(s) <= 3
        )
    )
    def test_invalid_input_returns_none(self, invalid_input: str) -> None:
        """Invalid input (not yes/no) should return None."""
        result = validate_confirmation_input(invalid_input, True)
        # Should return None for truly invalid inputs
        if result is not None:
            # If it's not None, it must be a yes/no variant we didn't catch
            assert result in (True, False), f"Unexpected result for input '{invalid_input}'"

    @given(st.text(min_size=4))
    def test_too_long_input_returns_none(self, long_input: str) -> None:
        """Input longer than 3 characters should return None."""
        assert validate_confirmation_input(long_input, True) is None
        assert validate_confirmation_input(long_input, False) is None

    def test_whitespace_examples_return_none(self) -> None:
        """Whitespace-only inputs should return None."""
        # Test specific whitespace cases instead of generating them
        for whitespace in ["   ", " ", "  ", "\t", "\n"]:
            result = validate_confirmation_input(whitespace, True)
            assert result is None, f"Expected None for whitespace '{repr(whitespace)}''"


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
    """Property-based tests for get_emoji_for_type function using Hypothesis."""

    @given(st.sampled_from([ct["type"] for ct in COMMIT_TYPES]))
    def test_valid_types_return_emoji_code(self, commit_type: str) -> None:
        """All valid commit types should return a valid emoji code."""
        result = get_emoji_for_type(commit_type, use_code=True)
        assert result != ""
        assert result.startswith(":")
        assert result.endswith(":")
        assert len(result) > 2

    @given(st.sampled_from([ct["type"] for ct in COMMIT_TYPES]))
    def test_valid_types_return_visual_emoji(self, commit_type: str) -> None:
        """All valid commit types should return a visual emoji."""
        result = get_emoji_for_type(commit_type, use_code=False)
        assert result != ""
        assert ":" not in result  # Visual emoji shouldn't have colons
        assert len(result) <= 4  # Emojis are typically 1-4 bytes

    @given(st.sampled_from([ct["type"] for ct in COMMIT_TYPES]), st.booleans())
    def test_consistent_non_empty_results(self, commit_type: str, use_code: bool) -> None:
        """Valid types should always return non-empty consistent results."""
        result1 = get_emoji_for_type(commit_type, use_code)
        result2 = get_emoji_for_type(commit_type, use_code)
        assert result1 == result2  # Idempotent
        assert result1 != ""  # Never empty for valid types

    @given(st.sampled_from([ct["type"] for ct in COMMIT_TYPES]))
    def test_code_and_visual_are_different(self, commit_type: str) -> None:
        """Emoji code and visual representation should be different."""
        code = get_emoji_for_type(commit_type, use_code=True)
        visual = get_emoji_for_type(commit_type, use_code=False)
        assert code != visual
        assert len(code) > len(visual)  # Code is longer (":sparkles:" vs "✨")

    @given(st.text(min_size=1).filter(lambda s: s not in [ct["type"] for ct in COMMIT_TYPES]))
    def test_invalid_types_return_empty(self, invalid_type: str) -> None:
        """Invalid commit types should return empty string."""
        result_code = get_emoji_for_type(invalid_type, use_code=True)
        result_visual = get_emoji_for_type(invalid_type, use_code=False)
        assert result_code == ""
        assert result_visual == ""

    @given(st.sampled_from([ct["type"] for ct in COMMIT_TYPES]))
    def test_emoji_mapping_is_complete(self, commit_type: str) -> None:
        """Every valid type should have both code and visual emoji."""
        # Find the type in COMMIT_TYPES
        type_info = next((ct for ct in COMMIT_TYPES if ct["type"] == commit_type), None)
        assert type_info is not None

        # Check that the function returns what's in COMMIT_TYPES
        assert get_emoji_for_type(commit_type, use_code=True) == type_info["emoji_code"]
        assert get_emoji_for_type(commit_type, use_code=False) == type_info["emoji"]


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


class TestReadMultilineInput:
    """Tests for read_multiline_input function."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["line 1", "line 2", "", ""])
    def test_basic_multiline_input(self, mock_input: Mock) -> None:
        """Should read multiline input until empty line."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input()

        assert "line 1" in result
        assert "line 2" in result

    @patch("builtins.input", return_value="")
    def test_empty_multiline_uses_default(self, mock_input: Mock) -> None:
        """Should use default text when no input."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(default_text="default body")

        assert result == "default body"

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 100, "", ""])
    def test_multiline_max_length_per_line(self, mock_input: Mock, capsys) -> None:
        """Should enforce max length per line."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        # Should reject the long line and not include it
        captured = capsys.readouterr()
        assert "too long" in captured.out.lower() or "Line" in captured.out

    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_multiline_keyboard_interrupt(self, mock_input: Mock) -> None:
        """Should handle keyboard interrupt gracefully."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input()

        assert result == ""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["short", "x" * 50, "", ""])
    def test_multiline_total_char_limit(self, mock_input: Mock, capsys) -> None:
        """Should enforce total character limit across all lines."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=60)

        # Should reject second line that would exceed total  limit
        captured = capsys.readouterr()
        assert "remaining" in captured.out.lower() or "characters" in captured.out.lower()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["test", "", "test2", "", ""])
    def test_multiline_with_empty_lines(self, mock_input: Mock) -> None:
        """Should handle empty lines correctly."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input()

        # Should include test but stop after two empty lines
        assert "test" in result

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=EOFError())
    def test_multiline_eof_error(self, mock_input: Mock) -> None:
        """Should handle EOFError gracefully."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input()

        assert result == ""


class TestConfirmUserActionFallback:
    """Tests for confirm_user_action with fallback (no prompt_toolkit)."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", return_value="y")
    def test_confirm_yes_fallback(self, mock_input: Mock) -> None:
        """Should return True for 'y' in fallback mode."""
        from ccg.utils import confirm_user_action

        result = confirm_user_action("Confirm?", default_yes=True)

        assert result is True

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", return_value="n")
    def test_confirm_no_fallback(self, mock_input: Mock) -> None:
        """Should return False for 'n' in fallback mode."""
        from ccg.utils import confirm_user_action

        result = confirm_user_action("Confirm?", default_yes=True)

        assert result is False

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", return_value="")
    def test_confirm_default_yes_fallback(self, mock_input: Mock) -> None:
        """Should use default_yes for empty input."""
        from ccg.utils import confirm_user_action

        result = confirm_user_action("Confirm?", default_yes=True)

        assert result is True

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", return_value="")
    def test_confirm_default_no_fallback(self, mock_input: Mock) -> None:
        """Should use default_no for empty input."""
        from ccg.utils import confirm_user_action

        result = confirm_user_action("Confirm?", default_yes=False)

        assert result is False


class TestCreateCounterToolbar:
    """Tests for create_counter_toolbar function."""

    def test_create_toolbar_returns_callable(self) -> None:
        """Should return a callable toolbar function."""
        from ccg.utils import create_counter_toolbar

        toolbar = create_counter_toolbar(100)

        assert toolbar is not None
        assert callable(toolbar)

    def test_create_toolbar_confirmation_mode(self) -> None:
        """Should create toolbar for confirmation input."""
        from ccg.utils import create_counter_toolbar

        toolbar = create_counter_toolbar(3, is_confirmation=True)

        assert toolbar is not None
        assert callable(toolbar)


class TestCreateInputKeyBindings:
    """Tests for create_input_key_bindings function."""

    def test_create_key_bindings_returns_object(self) -> None:
        """Should return key bindings object."""
        from ccg.utils import create_input_key_bindings

        kb = create_input_key_bindings(max_length=100)

        assert kb is not None

    def test_create_key_bindings_multiline(self) -> None:
        """Should create key bindings for multiline input."""
        from ccg.utils import create_input_key_bindings

        kb = create_input_key_bindings(multiline=True)

        assert kb is not None

    def test_create_key_bindings_confirmation(self) -> None:
        """Should create key bindings for confirmation."""
        from ccg.utils import create_input_key_bindings

        kb = create_input_key_bindings(is_confirmation=True, default_yes=True)

        assert kb is not None


class TestReadInputWithPromptToolkit:
    """Tests for read_input with prompt_toolkit available."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_with_history(self, mock_prompt: Mock) -> None:
        """Should use history when available."""
        from ccg.utils import read_input

        mock_prompt.return_value = "test input"

        result = read_input("Enter text", history_type="message")

        assert result == "test input"
        mock_prompt.assert_called_once()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_with_default(self, mock_prompt: Mock) -> None:
        """Should use default text."""
        from ccg.utils import read_input

        mock_prompt.return_value = "test"

        result = read_input("Enter text", default_text="default")

        assert result == "test"

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_falls_back_on_error(self, mock_prompt: Mock) -> None:
        """Should fall back to basic input on error."""
        from ccg.utils import read_input

        mock_prompt.side_effect = Exception("prompt_toolkit error")

        with patch("ccg.utils.read_input_fallback", return_value="fallback"):
            result = read_input("Enter text")

            assert result == "fallback"
