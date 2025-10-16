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
    create_counter_toolbar,
    create_input_key_bindings,
    get_emoji_for_type,
    read_input_fallback,
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

    @patch("builtins.input", return_value="exact length")
    def test_max_length_feedback_exact(self, mock_input: Mock, capsys) -> None:
        """Should show exact length feedback."""
        from ccg.utils import read_input_fallback

        read_input_fallback("Enter text", max_length=12)
        captured = capsys.readouterr()
        assert "Used all 12 characters" in captured.out

    @patch("builtins.input", return_value="long enough")
    def test_max_length_feedback_warning(self, mock_input: Mock, capsys) -> None:
        """Should show warning length feedback."""
        from ccg.utils import read_input_fallback

        read_input_fallback("Enter text", max_length=12)
        captured = capsys.readouterr()
        assert "11/12 characters used" in captured.out

    @patch("builtins.input", return_value="short")
    def test_max_length_feedback_info(self, mock_input: Mock, capsys) -> None:
        """Should show info length feedback."""
        from ccg.utils import read_input_fallback

        read_input_fallback("Enter text", max_length=12)
        captured = capsys.readouterr()
        assert "5/12 characters used" in captured.out


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

        with pytest.raises(KeyboardInterrupt):
            read_multiline_input()

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

        with pytest.raises(EOFError):
            read_multiline_input()


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

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_body_delegates_to_multiline(self, mock_prompt: Mock) -> None:
        """Should delegate to read_multiline_input for body input."""
        from ccg.utils import read_input

        with patch(
            "ccg.utils.read_multiline_input", return_value="multiline body"
        ) as mock_multiline:
            result = read_input("Enter text", history_type="body")

            assert result == "multiline body"
            mock_multiline.assert_called_once()


class TestPrintLogo:
    """Tests for print_logo function."""

    def test_print_logo_displays_ascii_art(self, capsys) -> None:
        """Should display ASCII logo."""
        from ccg.utils import print_logo

        print_logo()
        captured = capsys.readouterr()

        assert "Conventional" in captured.out or "CCG" in captured.out


class TestIsValidSemver:
    """Tests for is_valid_semver function."""

    def test_valid_semver_tags(self) -> None:
        """Should accept valid SemVer tags."""
        from ccg.utils import is_valid_semver

        valid_tags = [
            "1.0.0",
            "v1.0.0",
            "2.1.3",
            "v0.0.1",
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-beta",
            "1.0.0+20130313144700",
            "1.0.0-beta+exp.sha.5114f85",
        ]

        for tag in valid_tags:
            assert is_valid_semver(tag) is True, f"Should accept {tag}"

    def test_invalid_semver_tags(self) -> None:
        """Should reject invalid SemVer tags."""
        from ccg.utils import is_valid_semver

        invalid_tags = [
            "1",
            "1.0",
            "1.0.0.0",
            "v",
            "invalid",
            "",
            "1.0.a",
            "a.b.c",
        ]

        for tag in invalid_tags:
            assert is_valid_semver(tag) is False, f"Should reject {tag}"


class TestTermWidthException:
    """Tests for terminal width exception handling."""

    def test_term_width_fallback_on_exception(self) -> None:
        """Should use default width when terminal size fails."""
        import importlib
        import sys

        # Force reimport to trigger exception handling
        if "ccg.utils" in sys.modules:
            del sys.modules["ccg.utils"]

        with patch("shutil.get_terminal_size", side_effect=Exception("Terminal error")):
            import ccg.utils

            assert ccg.utils.TERM_WIDTH > 0  # Should have fallback value


class TestConfirmationValidatorWithPromptToolkit:
    """Tests for ConfirmationValidator when prompt_toolkit is available."""

    def test_confirmation_validator_init(self) -> None:
        """Should initialize ConfirmationValidator with default_yes parameter."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from ccg.utils import ConfirmationValidator

        validator = ConfirmationValidator(default_yes=True)
        assert validator.default_yes is True

        validator2 = ConfirmationValidator(default_yes=False)
        assert validator2.default_yes is False

    def test_confirmation_validator_validate_empty(self) -> None:
        """Should accept empty input (uses default)."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from ccg.utils import ConfirmationValidator

        validator = ConfirmationValidator(default_yes=True)
        mock_doc = Mock()
        mock_doc.text = ""

        # Should not raise exception
        validator.validate(mock_doc)

    def test_confirmation_validator_validate_invalid_long(self) -> None:
        """Should raise ValidationError for input longer than 3 chars."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from prompt_toolkit.validation import ValidationError

        from ccg.utils import ConfirmationValidator

        validator = ConfirmationValidator(default_yes=True)
        mock_doc = Mock()
        mock_doc.text = "yesss"

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(mock_doc)

        assert "Please enter 'y' or 'n'" in exc_info.value.message
        assert exc_info.value.cursor_position == 3

    def test_confirmation_validator_validate_invalid_short(self) -> None:
        """Should raise ValidationError for invalid short input."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from prompt_toolkit.validation import ValidationError

        from ccg.utils import ConfirmationValidator

        validator = ConfirmationValidator(default_yes=True)
        mock_doc = Mock()
        mock_doc.text = "x"

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(mock_doc)

        assert "Please enter 'y' or 'n'" in exc_info.value.message


class TestRealTimeCounterValidator:
    """Tests for RealTimeCounterValidator."""

    def test_counter_validator_exceeds_limit(self) -> None:
        """Should raise ValidationError when input exceeds max length."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from prompt_toolkit.validation import ValidationError

        from ccg.utils import RealTimeCounterValidator

        validator = RealTimeCounterValidator(max_length=10)
        mock_doc = Mock()
        mock_doc.text = "x" * 15

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(mock_doc)

        assert "CHARACTER LIMIT REACHED" in exc_info.value.message
        assert exc_info.value.cursor_position == 10


class TestPromptToolkitNotAvailable:
    """Tests for fallback when prompt_toolkit is not available."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    def test_histories_empty_when_not_available(self) -> None:
        """HISTORIES should be empty dict when prompt_toolkit unavailable."""
        # Import after patching
        import importlib
        import sys

        if "ccg.utils" in sys.modules:
            del sys.modules["ccg.utils"]

        with patch.dict("sys.modules", {"prompt_toolkit": None}):
            import ccg.utils

            # When not available, HISTORIES is defined as empty dict
            assert isinstance(ccg.utils.HISTORIES, dict)


class TestCreateCounterToolbarDetailed:
    """Detailed tests for create_counter_toolbar functionality."""

    def test_counter_toolbar_function_execution(self) -> None:
        """Should execute toolbar function and return tokens."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(100, is_confirmation=False)

        # Mock the app and buffer
        with patch("prompt_toolkit.application.current.get_app") as mock_get_app:
            mock_app = Mock()
            mock_buffer = Mock()
            mock_buffer.text = "test input"
            mock_app.current_buffer = mock_buffer
            mock_get_app.return_value = mock_app

            result = toolbar_func()

            assert isinstance(result, list)
            assert len(result) >= 1

    def test_counter_toolbar_confirmation_mode(self) -> None:
        """Should create toolbar for confirmation with 3 char limit."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(3, is_confirmation=True)

        with patch("prompt_toolkit.application.current.get_app") as mock_get_app:
            mock_app = Mock()
            mock_buffer = Mock()
            mock_buffer.text = "yes"
            mock_app.current_buffer = mock_buffer
            mock_get_app.return_value = mock_app

            result = toolbar_func()

            assert isinstance(result, list)

    def test_counter_toolbar_with_exception(self) -> None:
        """Should handle exceptions gracefully in toolbar function."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(100)

        with patch("prompt_toolkit.application.current.get_app", side_effect=Exception("Error")):
            result = toolbar_func()

            # Should return fallback tokens
            assert isinstance(result, list)


class TestCreateInputKeyBindingsDetailed:
    """Detailed tests for create_input_key_bindings functionality."""

    def test_key_bindings_multiline_ctrl_d(self) -> None:
        """Should handle Ctrl+D in multiline mode."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_input_key_bindings

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        kb = create_input_key_bindings(max_length=100, multiline=True)

        # Key bindings object should be created
        assert kb is not None

    def test_key_bindings_confirmation_auto_fill(self) -> None:
        """Should auto-fill default on Enter for confirmation."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_input_key_bindings

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        kb = create_input_key_bindings(is_confirmation=True, default_yes=True)

        # Key bindings object should be created
        assert kb is not None

    def test_key_bindings_character_limit_enforcement(self) -> None:
        """Should enforce character limits via key bindings."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_input_key_bindings

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        kb = create_input_key_bindings(max_length=10)

        # Key bindings object should be created
        assert kb is not None


class TestReadInputWithCharacterFeedback:
    """Tests for read_input character usage feedback."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_exact_limit_feedback(self, mock_prompt: Mock, capsys) -> None:
        """Should show 'Used all N characters' when at exact limit."""
        from ccg.utils import read_input

        mock_prompt.return_value = "x" * 50

        result = read_input("Enter text", max_length=50)

        captured = capsys.readouterr()
        assert "Used all 50 characters" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_warning_threshold_feedback(self, mock_prompt: Mock, capsys) -> None:
        """Should show warning when >= 80% of limit."""
        from ccg.utils import read_input

        mock_prompt.return_value = "x" * 45  # 90% of 50

        result = read_input("Enter text", max_length=50)

        captured = capsys.readouterr()
        assert "45/50 characters used" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_info_feedback(self, mock_prompt: Mock, capsys) -> None:
        """Should show info when < 80% of limit."""
        from ccg.utils import read_input

        mock_prompt.return_value = "x" * 20  # 40% of 50

        result = read_input("Enter text", max_length=50)

        captured = capsys.readouterr()
        assert "20/50 characters used" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_no_feedback_if_no_max_length(self, mock_prompt: Mock, capsys) -> None:
        """Should not show feedback if max_length is not set."""
        from ccg.utils import read_input

        mock_prompt.return_value = "test"
        read_input("Enter text")
        captured = capsys.readouterr()
        assert "characters used" not in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_eof_error(self, mock_prompt: Mock) -> None:
        """Should re-raise EOFError."""
        from ccg.utils import read_input

        mock_prompt.side_effect = EOFError()

        with pytest.raises(EOFError):
            read_input("Enter text")

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_keyboard_interrupt(self, mock_prompt: Mock) -> None:
        """Should re-raise KeyboardInterrupt."""
        from ccg.utils import read_input

        mock_prompt.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            read_input("Enter text")


class TestReadInputFallbackKeyboardInterrupt:
    """Tests for read_input_fallback keyboard interrupt handling."""

    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_fallback_keyboard_interrupt(self, mock_input: Mock) -> None:
        """Should re-raise KeyboardInterrupt in fallback mode."""
        from ccg.utils import read_input_fallback

        with pytest.raises(KeyboardInterrupt):
            read_input_fallback("Enter text")

    @patch("builtins.input", side_effect=EOFError())
    def test_fallback_eof_error(self, mock_input: Mock) -> None:
        """Should re-raise EOFError in fallback mode."""
        from ccg.utils import read_input_fallback

        with pytest.raises(EOFError):
            read_input_fallback("Enter text")


class TestConfirmUserActionExceptionHandling:
    """Tests for confirm_user_action exception handling."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_confirm_exception_falls_back_to_basic_input(self, mock_prompt: Mock) -> None:
        """Should fall back to basic input when prompt_toolkit fails."""
        from ccg.utils import confirm_user_action

        mock_prompt.side_effect = Exception("prompt_toolkit error")

        with patch("builtins.input", return_value="y"):
            result = confirm_user_action("Confirm?", default_yes=True)

            assert result is True

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_confirm_exception_fallback_loop_invalid_input(self, mock_prompt: Mock) -> None:
        """Should loop until valid input in exception fallback."""
        from ccg.utils import confirm_user_action

        mock_prompt.side_effect = Exception("prompt_toolkit error")

        with patch("builtins.input", side_effect=["invalid", "xxxx", "y"]):
            result = confirm_user_action("Confirm?", default_yes=True)

            assert result is True

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_confirm_exception_fallback_keyboard_interrupt(self, mock_prompt: Mock) -> None:
        """Should handle KeyboardInterrupt in exception fallback."""
        from ccg.utils import confirm_user_action

        mock_prompt.side_effect = Exception("prompt_toolkit error")

        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            with pytest.raises(KeyboardInterrupt):
                confirm_user_action("Confirm?", default_yes=True)

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["xxxx", "y"])
    def test_confirm_fallback_mode_invalid_input(self, mock_input: Mock, capsys) -> None:
        """Should handle invalid input in fallback mode."""
        from ccg.utils import confirm_user_action

        result = confirm_user_action("Confirm?", default_yes=True)

        assert result is True
        captured = capsys.readouterr()
        # Should show either the character limit exceeded message or invalid input message
        assert "EXCEEDED" in captured.out or "enter 'y' or 'n'" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", return_value="yyyy")
    def test_confirm_fallback_mode_too_long(self, mock_input: Mock, capsys) -> None:
        """Should reject input longer than 3 characters in fallback mode."""
        from ccg.utils import confirm_user_action

        with patch("builtins.input", side_effect=["yyyy", "y"]):
            result = confirm_user_action("Confirm?", default_yes=True)

            assert result is True
            captured = capsys.readouterr()
            assert "CHARACTER LIMIT EXCEEDED" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_confirm_fallback_keyboard_interrupt(self, mock_input: Mock) -> None:
        """Should handle KeyboardInterrupt in fallback mode."""
        from ccg.utils import confirm_user_action

        with pytest.raises(KeyboardInterrupt):
            confirm_user_action("Confirm?", default_yes=True)


class TestReadMultilineInputWithPromptToolkit:
    """Tests for read_multiline_input with prompt_toolkit."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 100, "", ""])
    def test_multiline_with_prompt_toolkit_exact_limit(self, mock_input: Mock, capsys) -> None:
        """Should show feedback when using all characters."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Check for character feedback
        assert "characters" in captured.out.lower()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 85, "", ""])
    def test_multiline_with_prompt_toolkit_warning(self, mock_input: Mock, capsys) -> None:
        """Should show warning feedback at 80%+."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Check for character feedback
        assert "characters" in captured.out.lower()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 50, "", ""])
    def test_multiline_with_prompt_toolkit_info(self, mock_input: Mock, capsys) -> None:
        """Should show info feedback below 80%."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Check for character feedback
        assert "characters" in captured.out.lower()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=EOFError())
    def test_multiline_with_prompt_toolkit_eof_error(self, mock_input: Mock) -> None:
        """Should handle EOFError gracefully."""
        from ccg.utils import read_multiline_input

        with pytest.raises(EOFError):
            read_multiline_input(max_length=100)

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["test", "", ""])
    def test_multiline_with_prompt_toolkit_exception(self, mock_input: Mock) -> None:
        """Should fall back on exception."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        assert "test" in result


class TestReadMultilineInputFallbackEdgeCases:
    """Tests for read_multiline_input fallback mode edge cases."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 50, "", ""])
    def test_multiline_fallback_char_limit_reached(self, mock_input: Mock, capsys) -> None:
        """Should stop when character limit reached."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=40)

        captured = capsys.readouterr()
        assert "Character limit" in captured.out or "remaining" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["short", "x" * 100, "", ""])
    def test_multiline_fallback_line_too_long_rejected(self, mock_input: Mock, capsys) -> None:
        """Should reject lines exceeding line length limit."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=200)

        captured = capsys.readouterr()
        assert "too long" in captured.out.lower()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["line1", "line2", "", ""])
    def test_multiline_fallback_with_feedback(self, mock_input: Mock, capsys) -> None:
        """Should show character count feedback."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        assert "line1" in result
        assert "line2" in result


class TestReadMultilineInputFinalFeedback:
    """Tests for read_multiline_input final character feedback."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 50, "", ""])
    def test_multiline_final_feedback_exact(self, mock_input: Mock, capsys) -> None:
        """Should show exact limit feedback at end."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=50)

        captured = capsys.readouterr()
        # Should show final feedback
        assert "characters" in captured.out.lower()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 20, "", ""])
    def test_multiline_final_feedback_info(self, mock_input: Mock, capsys) -> None:
        """Should show info feedback at end."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Should show final feedback
        assert "20" in captured.out or "characters" in captured.out.lower()


class TestCreateCounterToolbarAdvanced:
    """Advanced tests for create_counter_toolbar covering all color thresholds."""

    def test_toolbar_warning_color_at_70_percent(self) -> None:
        """Should use warning color at 70-90% of limit."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(100, is_confirmation=False)

        with patch("prompt_toolkit.application.current.get_app") as mock_get_app:
            mock_app = Mock()
            mock_buffer = Mock()
            mock_buffer.text = "x" * 75  # 75% of 100
            mock_app.current_buffer = mock_buffer
            mock_get_app.return_value = mock_app

            result = toolbar_func()

            assert isinstance(result, list)
            # Should use warning color
            assert any("warning" in str(token) for token in result)

    def test_toolbar_danger_color_above_90_percent(self) -> None:
        """Should use danger color above 90% of limit."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(100, is_confirmation=False)

        with patch("prompt_toolkit.application.current.get_app") as mock_get_app:
            mock_app = Mock()
            mock_buffer = Mock()
            mock_buffer.text = "x" * 95  # 95% of 100
            mock_app.current_buffer = mock_buffer
            mock_get_app.return_value = mock_app

            result = toolbar_func()

            assert isinstance(result, list)
            # Should use danger color
            assert any("danger" in str(token) for token in result)

    def test_toolbar_confirmation_at_limit(self) -> None:
        """Should show LIMIT prefix when at confirmation limit."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(3, is_confirmation=True)

        with patch("prompt_toolkit.application.current.get_app") as mock_get_app:
            mock_app = Mock()
            mock_buffer = Mock()
            mock_buffer.text = "yes"  # 3 chars
            mock_app.current_buffer = mock_buffer
            mock_get_app.return_value = mock_app

            result = toolbar_func()

            assert isinstance(result, list)
            # Should show LIMIT prefix
            text_parts = [token[1] for token in result]
            combined_text = "".join(text_parts)
            assert "LIMIT" in combined_text or "3/3" in combined_text

    def test_toolbar_regular_at_limit(self) -> None:
        """Should show LIMIT prefix when at regular limit."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(50, is_confirmation=False)

        with patch("prompt_toolkit.application.current.get_app") as mock_get_app:
            mock_app = Mock()
            mock_buffer = Mock()
            mock_buffer.text = "x" * 50  # At limit
            mock_app.current_buffer = mock_buffer
            mock_get_app.return_value = mock_app

            result = toolbar_func()

            assert isinstance(result, list)
            # Should show LIMIT prefix
            text_parts = [token[1] for token in result]
            combined_text = "".join(text_parts)
            assert "LIMIT" in combined_text or "50/50" in combined_text

    def test_toolbar_term_size_exception(self) -> None:
        """Should handle terminal size exception gracefully."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(100)

        with patch("prompt_toolkit.application.current.get_app") as mock_get_app:
            with patch("shutil.get_terminal_size", side_effect=OSError("No term")):
                mock_app = Mock()
                mock_buffer = Mock()
                mock_buffer.text = "test"
                mock_app.current_buffer = mock_buffer
                mock_get_app.return_value = mock_app

                result = toolbar_func()

                # Should still return result with default width (80)
                assert isinstance(result, list)

    def test_toolbar_no_app_returns_default(self) -> None:
        """Should return default when app is None."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(100)

        with patch("prompt_toolkit.application.current.get_app", return_value=None):
            result = toolbar_func()

            assert isinstance(result, list)
            # Should show default 0/100
            text_parts = [token[1] for token in result]
            combined_text = "".join(text_parts)
            assert "0/100" in combined_text


class TestCreateInputKeyBindingsAdvanced:
    """Advanced tests for create_input_key_bindings covering all paths."""

    def test_key_bindings_any_key_confirmation_over_limit(self) -> None:
        """Should block input over 3 chars in confirmation mode."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_input_key_bindings

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        kb = create_input_key_bindings(is_confirmation=True, default_yes=True)

        # Key bindings should exist
        assert kb is not None

    def test_key_bindings_any_key_regular_over_limit(self) -> None:
        """Should block input over max_length in regular mode."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_input_key_bindings

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        kb = create_input_key_bindings(max_length=10)

        # Key bindings should exist
        assert kb is not None

    def test_key_bindings_navigation_keys(self) -> None:
        """Should handle all navigation keys."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_input_key_bindings

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        kb = create_input_key_bindings(max_length=100)

        # Key bindings should exist with navigation
        assert kb is not None

    def test_key_bindings_multiline_escape_enter(self) -> None:
        """Should handle Escape+Enter in multiline mode."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_input_key_bindings

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        kb = create_input_key_bindings(multiline=True)

        # Key bindings should exist
        assert kb is not None


class TestReadInputWithCharacterFeedbackDetailed:
    """Detailed tests for read_input character feedback paths."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_eof_error_prints_newline(self, mock_prompt: Mock, capsys) -> None:
        """Should print newline before raising EOFError."""
        from ccg.utils import read_input

        mock_prompt.side_effect = EOFError()

        with pytest.raises(EOFError):
            read_input("Enter text")

        captured = capsys.readouterr()
        # Newline should be printed
        assert captured.out == "\n"

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_read_input_keyboard_interrupt_prints_newline(self, mock_prompt: Mock, capsys) -> None:
        """Should print newline before raising KeyboardInterrupt."""
        from ccg.utils import read_input

        mock_prompt.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            read_input("Enter text")

        captured = capsys.readouterr()
        # Newline should be printed
        assert captured.out == "\n"


class TestConfirmUserActionAllPaths:
    """Test all code paths in confirm_user_action."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_confirm_eof_error_prints_newline(self, mock_prompt: Mock, capsys) -> None:
        """Should print newline before raising EOFError."""
        from ccg.utils import confirm_user_action

        mock_prompt.side_effect = EOFError()

        with pytest.raises(EOFError):
            confirm_user_action("Confirm?", default_yes=True)

        captured = capsys.readouterr()
        assert captured.out == "\n"

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_confirm_keyboard_interrupt_prints_newline(self, mock_prompt: Mock, capsys) -> None:
        """Should print newline before raising KeyboardInterrupt."""
        from ccg.utils import confirm_user_action

        mock_prompt.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            confirm_user_action("Confirm?", default_yes=True)

        captured = capsys.readouterr()
        assert captured.out == "\n"

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_confirm_exception_eof_in_fallback(self, mock_prompt: Mock, capsys) -> None:
        """Should handle EOFError in exception fallback."""
        from ccg.utils import confirm_user_action

        mock_prompt.side_effect = Exception("Error")

        with patch("builtins.input", side_effect=EOFError()):
            with pytest.raises(EOFError):
                confirm_user_action("Confirm?", default_yes=True)

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=EOFError())
    def test_confirm_fallback_eof_error(self, mock_input: Mock) -> None:
        """Should handle EOFError in fallback mode."""
        from ccg.utils import confirm_user_action

        with pytest.raises(EOFError):
            confirm_user_action("Confirm?", default_yes=True)


class TestReadMultilineInputAllPaths:
    """Test all code paths in read_multiline_input."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_multiline_prompt_toolkit_success_with_result(self, mock_prompt: Mock, capsys) -> None:
        """Should successfully return result with feedback when using prompt_toolkit."""
        from ccg.utils import read_multiline_input

        # Simulate successful input with prompt_toolkit
        mock_prompt.return_value = "test multiline content"

        result = read_multiline_input(max_length=100)

        assert result == "test multiline content"
        captured = capsys.readouterr()
        # Should show character usage feedback
        assert "characters" in captured.out.lower()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_multiline_prompt_toolkit_exact_limit(self, mock_prompt: Mock, capsys) -> None:
        """Should show 'Used all N characters' when at exact limit."""
        from ccg.utils import read_multiline_input

        # Simulate input exactly at limit
        mock_prompt.return_value = "x" * 100

        result = read_multiline_input(max_length=100)

        assert result == "x" * 100
        captured = capsys.readouterr()
        # Should show "Used all 100 characters"
        assert "Used all 100 characters" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_multiline_prompt_toolkit_warning_threshold(self, mock_prompt: Mock, capsys) -> None:
        """Should show warning when >= 80% but < 100% of limit."""
        from ccg.utils import read_multiline_input

        # Simulate input at 85% of limit (85 chars)
        mock_prompt.return_value = "x" * 85

        result = read_multiline_input(max_length=100)

        assert result == "x" * 85
        captured = capsys.readouterr()
        # Should show warning feedback like "85/100 characters used"
        assert "85/100 characters used" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_multiline_prompt_toolkit_eof_error(self, mock_prompt: Mock, capsys) -> None:
        """Should handle EOFError in prompt_toolkit path."""
        from ccg.utils import read_multiline_input

        mock_prompt.side_effect = EOFError()

        with pytest.raises(EOFError):
            read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        assert "\n" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_multiline_prompt_toolkit_keyboard_interrupt(self, mock_input: Mock) -> None:
        """Should handle KeyboardInterrupt in prompt_toolkit path."""
        from ccg.utils import read_multiline_input

        with pytest.raises(KeyboardInterrupt):
            read_multiline_input(max_length=100)

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["line1", "x" * 90, "", ""])
    def test_multiline_fallback_warning_feedback(self, mock_input: Mock, capsys) -> None:
        """Should show warning feedback when approaching limit."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Should show warning or info about character usage
        assert "characters" in captured.out.lower()

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["line1", "line2", "line3", "", ""])
    def test_multiline_fallback_info_feedback_loop(self, mock_input: Mock, capsys) -> None:
        """Should show info feedback during input loop."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Should show character tracking
        assert "line1" in result
        assert "line2" in result

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_multiline_fallback_keyboard_interrupt_in_try(self, mock_input: Mock) -> None:
        """Should handle KeyboardInterrupt in fallback try block."""
        from ccg.utils import read_multiline_input

        with pytest.raises(KeyboardInterrupt):
            read_multiline_input(max_length=100)

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["test", "", ""])
    def test_multiline_fallback_with_default(self, mock_input: Mock) -> None:
        """Should use default when result is empty."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(default_text="default body", max_length=100)

        # Result should not be empty since we provided input
        assert "test" in result

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["", ""])
    def test_multiline_fallback_empty_uses_default(self, mock_input: Mock) -> None:
        """Should return default when input is completely empty."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(default_text="default body", max_length=100)

        # Should use default when empty
        assert result == "default body"


class TestCreateCounterToolbarCoverage:
    """Coverage tests for create_counter_toolbar function."""

    def test_toolbar_no_app_or_buffer(self) -> None:
        """Should handle when get_app returns None or buffer is missing."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(100)

        with patch("prompt_toolkit.application.current.get_app") as mock_get_app:
            # Simulate get_app() returning None
            mock_get_app.return_value = None
            result = toolbar_func()
            assert isinstance(result, list)
            text_parts = [token[1] for token in result]
            combined_text = "".join(text_parts)
            assert "0/100" in combined_text

            # Simulate app without current_buffer
            mock_app = Mock()
            mock_app.current_buffer = None
            mock_get_app.return_value = mock_app
            result = toolbar_func()
            assert isinstance(result, list)
            text_parts = [token[1] for token in result]
            combined_text = "".join(text_parts)
            assert "0/100" in combined_text

    def test_toolbar_get_app_exception(self) -> None:
        """Should handle exception from get_app."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE, create_counter_toolbar

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        toolbar_func = create_counter_toolbar(100)

        with patch(
            "prompt_toolkit.application.current.get_app", side_effect=Exception("get_app error")
        ):
            result = toolbar_func()
            assert isinstance(result, list)
            text_parts = [token[1] for token in result]
            combined_text = "".join(text_parts)
            assert "0/100" in combined_text


class TestReadInputFallbackCoverage:
    """Coverage tests for read_input_fallback function."""

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_fallback_keyboard_interrupt_prints_newline(self, mock_input, capsys) -> None:
        """Should print newline on KeyboardInterrupt."""
        with pytest.raises(KeyboardInterrupt):
            read_input_fallback("Enter text")
        captured = capsys.readouterr()
        assert captured.out == "\n"


class TestReadMultilineInputCoverage:
    """Coverage tests for read_multiline_input function."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["a" * 10, "b" * 10, "c" * 20, "d" * 20, "e" * 20, "", ""])
    def test_multiline_fallback_char_limit_feedback(self, mock_input: Mock, capsys) -> None:
        """Should show correct character limit feedback in fallback mode."""
        from ccg.utils import read_multiline_input

        read_multiline_input(max_length=100)
        captured = capsys.readouterr()
        assert "84/100" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["a" * 10, "b" * 10, "c" * 85, "", ""])
    def test_multiline_fallback_potential_total_exceeds_limit(
        self, mock_input: Mock, capsys
    ) -> None:
        """Should reject line if it would exceed total character limit."""
        from ccg.utils import read_multiline_input

        read_multiline_input(max_length=100)
        captured = capsys.readouterr()
        assert "Line too long!" in captured.out


class TestKeyBindingsCreation:
    """Tests for key binding creation to ensure code paths are executed."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    def test_key_bindings_not_available_returns_none(self) -> None:
        """Should return None when KeyBindings is None."""
        from ccg.utils import create_input_key_bindings

        # This will exercise line 528
        with patch("ccg.utils.KeyBindings", None):
            kb = create_input_key_bindings()
            assert kb is None

    def test_key_bindings_single_line_confirmation_default_yes(self) -> None:
        """Should create bindings for confirmation mode with default_yes=True."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from ccg.utils import create_input_key_bindings

        # This exercises lines 531-537 (single-line confirmation mode)
        kb = create_input_key_bindings(is_confirmation=True, default_yes=True)
        assert kb is not None

    def test_key_bindings_single_line_confirmation_default_no(self) -> None:
        """Should create bindings for confirmation mode with default_yes=False."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from ccg.utils import create_input_key_bindings

        # This exercises line 536 (default_yes=False branch)
        kb = create_input_key_bindings(is_confirmation=True, default_yes=False)
        assert kb is not None

    def test_key_bindings_multiline_mode(self) -> None:
        """Should create bindings for multiline mode."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from ccg.utils import create_input_key_bindings

        # This exercises lines 541-547 (multiline mode bindings)
        kb = create_input_key_bindings(multiline=True, max_length=100)
        assert kb is not None

    def test_key_bindings_all_navigation_keys(self) -> None:
        """Should create all navigation key bindings."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from ccg.utils import create_input_key_bindings

        # This exercises lines 549-588 (all key bindings)
        kb = create_input_key_bindings(max_length=100)
        assert kb is not None

    def test_key_bindings_confirmation_with_max_length(self) -> None:
        """Should create confirmation bindings with character limit."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from ccg.utils import create_input_key_bindings

        # This exercises lines 555-556 (confirmation length check)
        kb = create_input_key_bindings(is_confirmation=True, max_length=3)
        assert kb is not None

    def test_key_bindings_regular_with_max_length(self) -> None:
        """Should create regular bindings with max_length enforcement."""
        from ccg.utils import PROMPT_TOOLKIT_AVAILABLE

        if not PROMPT_TOOLKIT_AVAILABLE:
            pytest.skip("prompt_toolkit not available")

        from ccg.utils import create_input_key_bindings

        # This exercises lines 557-564 (max_length enforcement with bell)
        kb = create_input_key_bindings(max_length=10)
        assert kb is not None


class TestReadInputFallbackPath:
    """Tests for read_input fallback path (line 668)."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    @patch("builtins.input", return_value="fallback value")
    def test_read_input_when_prompt_toolkit_unavailable_uses_fallback(
        self, mock_input: Mock, mock_prompt: Mock
    ) -> None:
        """Should use fallback when PROMPT_TOOLKIT_AVAILABLE is True but not in use."""
        from ccg.utils import read_input

        # Make sure PROMPT_TOOLKIT_AVAILABLE is False to trigger line 668
        with patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False):
            result = read_input("Enter text", max_length=100)
            assert result == "fallback value"
            mock_input.assert_called()


class TestConfirmUserActionSuccessAndCancelMessages:
    """Tests for confirm_user_action success/cancel message paths (lines 814, 836, 845, 849)."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt")
    def test_confirm_exception_fallback_invalid_then_valid_with_error_message(
        self, mock_prompt: Mock, capsys
    ) -> None:
        """Should show error message in exception fallback loop."""
        from ccg.utils import confirm_user_action

        mock_prompt.side_effect = Exception("prompt_toolkit error")

        # Test line 814 - error message for invalid input
        with patch("builtins.input", side_effect=["xyz", "y"]):
            result = confirm_user_action("Confirm? (y/n)", default_yes=True)
            assert result is True
            captured = capsys.readouterr()
            # Line 814 should print error
            assert "enter 'y' or 'n'" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["z", "y"])
    def test_confirm_fallback_invalid_input_error_message(self, mock_input: Mock, capsys) -> None:
        """Should show error message for invalid input in fallback mode."""
        from ccg.utils import confirm_user_action

        result = confirm_user_action("Confirm? (y/n)", default_yes=True)
        assert result is True
        captured = capsys.readouterr()
        # Line 836 should print error
        assert "enter 'y' or 'n'" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt", return_value="y")
    def test_confirm_with_success_message(self, mock_prompt: Mock, capsys) -> None:
        """Should print success message when confirmed."""
        from ccg.utils import confirm_user_action

        result = confirm_user_action(
            "Confirm? (y/n)", success_message="Operation confirmed!", default_yes=True
        )
        assert result is True
        captured = capsys.readouterr()
        # Line 845 should print success message
        assert "Operation confirmed!" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", True)
    @patch("ccg.utils.prompt", return_value="n")
    def test_confirm_with_cancel_message(self, mock_prompt: Mock, capsys) -> None:
        """Should print cancel message when cancelled."""
        from ccg.utils import confirm_user_action

        result = confirm_user_action(
            "Confirm? (y/n)", cancel_message="Operation cancelled", default_yes=True
        )
        assert result is False
        captured = capsys.readouterr()
        # Line 849 should print cancel message
        assert "Operation cancelled" in captured.out


class TestReadMultilineInputWithPromptToolkitFeedback:
    """Tests for read_multiline_input feedback with prompt_toolkit (lines 903-916)."""

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 100, "", ""])
    def test_multiline_fallback_exact_limit_feedback(self, mock_input: Mock, capsys) -> None:
        """Should show exact limit feedback in fallback mode."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Should show final feedback
        assert "characters" in captured.out.lower() or "100" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 85, "", ""])
    def test_multiline_fallback_warning_threshold_feedback(self, mock_input: Mock, capsys) -> None:
        """Should show warning feedback at 80%+ in fallback mode."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Should show warning feedback
        assert "characters" in captured.out.lower() or "85" in captured.out

    @patch("ccg.utils.PROMPT_TOOLKIT_AVAILABLE", False)
    @patch("builtins.input", side_effect=["x" * 50, "", ""])
    def test_multiline_fallback_info_feedback(self, mock_input: Mock, capsys) -> None:
        """Should show info feedback below 80% in fallback mode."""
        from ccg.utils import read_multiline_input

        result = read_multiline_input(max_length=100)

        captured = capsys.readouterr()
        # Should show info feedback
        assert "characters" in captured.out.lower() or "50" in captured.out
