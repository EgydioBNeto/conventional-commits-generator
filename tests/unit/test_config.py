"""Unit tests for config.py module."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ccg.config import (
    GIT_CONFIG,
    INPUT_LIMITS,
    UI_CONFIG,
    GitConfig,
    InputLimits,
    UIConfig,
)


class TestInputLimits:
    """Tests for InputLimits dataclass."""

    def test_input_limits_singleton_exists(self):
        """INPUT_LIMITS singleton should exist."""
        assert INPUT_LIMITS is not None
        assert isinstance(INPUT_LIMITS, InputLimits)

    def test_all_limits_positive(self):
        """All input limits should be positive integers."""
        assert INPUT_LIMITS.TYPE > 0
        assert INPUT_LIMITS.SCOPE > 0
        assert INPUT_LIMITS.MESSAGE > 0
        assert INPUT_LIMITS.BODY > 0
        assert INPUT_LIMITS.TAG > 0
        assert INPUT_LIMITS.TAG_MESSAGE > 0
        assert INPUT_LIMITS.EDIT_MESSAGE > 0
        assert INPUT_LIMITS.CONFIRMATION > 0
        assert INPUT_LIMITS.COMMIT_COUNT > 0

    def test_confirmation_limit_is_three(self):
        """Confirmation limit should be exactly 3 for y/yes or n/no."""
        assert INPUT_LIMITS.CONFIRMATION == 3

    def test_message_limit_reasonable(self):
        """Message limit should be reasonable for commit messages (50-100 chars)."""
        assert 50 <= INPUT_LIMITS.MESSAGE <= 100

    def test_body_larger_than_message(self):
        """Body limit should be larger than message limit."""
        assert INPUT_LIMITS.BODY > INPUT_LIMITS.MESSAGE

    def test_scope_smaller_than_message(self):
        """Scope limit should be smaller than or equal to message limit."""
        assert INPUT_LIMITS.SCOPE <= INPUT_LIMITS.MESSAGE

    def test_type_smaller_than_scope(self):
        """Type limit should be smaller than or equal to scope limit."""
        assert INPUT_LIMITS.TYPE <= INPUT_LIMITS.SCOPE

    def test_input_limits_frozen(self):
        """InputLimits dataclass should be frozen (immutable)."""
        with pytest.raises(AttributeError):
            INPUT_LIMITS.TYPE = 100  # type: ignore

    def test_create_custom_input_limits(self):
        """Should be able to create custom InputLimits instances."""
        custom = InputLimits(
            TYPE=10,
            SCOPE=20,
            MESSAGE=80,
            BODY=600,
            TAG=40,
            TAG_MESSAGE=600,
            EDIT_MESSAGE=150,
            CONFIRMATION=3,
            COMMIT_COUNT=10,
        )

        assert custom.TYPE == 10
        assert custom.SCOPE == 20
        assert custom.MESSAGE == 80

    @given(st.integers(min_value=1, max_value=20))
    def test_type_limit_range(self, limit: int):
        """Type limit should accept reasonable range values."""
        custom = InputLimits(
            TYPE=limit,
            SCOPE=16,
            MESSAGE=64,
            BODY=512,
            TAG=32,
            TAG_MESSAGE=512,
            EDIT_MESSAGE=128,
            CONFIRMATION=3,
            COMMIT_COUNT=6,
        )
        assert custom.TYPE == limit


class TestGitConfig:
    """Tests for GitConfig dataclass."""

    def test_git_config_singleton_exists(self):
        """GIT_CONFIG singleton should exist."""
        assert GIT_CONFIG is not None
        assert isinstance(GIT_CONFIG, GitConfig)

    def test_all_timeouts_positive(self):
        """All timeouts should be positive integers."""
        assert GIT_CONFIG.DEFAULT_TIMEOUT > 0
        assert GIT_CONFIG.PULL_TIMEOUT > 0
        assert GIT_CONFIG.FILTER_BRANCH_TIMEOUT > 0
        assert GIT_CONFIG.PRE_COMMIT_TIMEOUT > 0

    def test_default_timeout_reasonable(self):
        """Default timeout should be reasonable (30-120 seconds)."""
        assert 30 <= GIT_CONFIG.DEFAULT_TIMEOUT <= 120

    def test_pull_timeout_longer_than_default(self):
        """Pull timeout should be longer than default (network operation)."""
        assert GIT_CONFIG.PULL_TIMEOUT >= GIT_CONFIG.DEFAULT_TIMEOUT

    def test_filter_branch_timeout_longest(self):
        """Filter branch timeout should be longest (heavy operation)."""
        assert GIT_CONFIG.FILTER_BRANCH_TIMEOUT >= GIT_CONFIG.PULL_TIMEOUT
        assert GIT_CONFIG.FILTER_BRANCH_TIMEOUT >= GIT_CONFIG.DEFAULT_TIMEOUT
        assert GIT_CONFIG.FILTER_BRANCH_TIMEOUT >= GIT_CONFIG.PRE_COMMIT_TIMEOUT

    def test_precommit_timeout_reasonable(self):
        """Pre-commit timeout should be reasonable for hooks."""
        assert 60 <= GIT_CONFIG.PRE_COMMIT_TIMEOUT <= 300

    def test_git_config_frozen(self):
        """GitConfig dataclass should be frozen (immutable)."""
        with pytest.raises(AttributeError):
            GIT_CONFIG.DEFAULT_TIMEOUT = 100  # type: ignore

    def test_create_custom_git_config(self):
        """Should be able to create custom GitConfig instances."""
        custom = GitConfig(
            DEFAULT_TIMEOUT=90,
            PULL_TIMEOUT=180,
            FILTER_BRANCH_TIMEOUT=600,
            PRE_COMMIT_TIMEOUT=150,
        )

        assert custom.DEFAULT_TIMEOUT == 90
        assert custom.PULL_TIMEOUT == 180
        assert custom.FILTER_BRANCH_TIMEOUT == 600
        assert custom.PRE_COMMIT_TIMEOUT == 150

    @given(st.integers(min_value=30, max_value=600))
    def test_timeout_range_valid(self, timeout: int):
        """Timeouts should accept reasonable range values."""
        custom = GitConfig(
            DEFAULT_TIMEOUT=timeout,
            PULL_TIMEOUT=timeout,
            FILTER_BRANCH_TIMEOUT=timeout,
            PRE_COMMIT_TIMEOUT=timeout,
        )
        assert custom.DEFAULT_TIMEOUT == timeout


class TestUIConfig:
    """Tests for UIConfig dataclass."""

    def test_ui_config_singleton_exists(self):
        """UI_CONFIG singleton should exist."""
        assert UI_CONFIG is not None
        assert isinstance(UI_CONFIG, UIConfig)

    def test_all_dimensions_positive(self):
        """All UI dimensions should be positive integers."""
        assert UI_CONFIG.MIN_BOX_WIDTH > 0
        assert UI_CONFIG.MAX_BOX_WIDTH > 0
        assert UI_CONFIG.DEFAULT_TERM_WIDTH > 0
        assert UI_CONFIG.DEFAULT_TERM_HEIGHT > 0

    def test_max_box_width_greater_than_min(self):
        """Max box width should be greater than min."""
        assert UI_CONFIG.MAX_BOX_WIDTH > UI_CONFIG.MIN_BOX_WIDTH

    def test_min_box_width_reasonable(self):
        """Min box width should be reasonable for UI display."""
        assert 40 <= UI_CONFIG.MIN_BOX_WIDTH <= 80

    def test_max_box_width_reasonable(self):
        """Max box width should be reasonable for UI display."""
        assert 80 <= UI_CONFIG.MAX_BOX_WIDTH <= 150

    def test_default_term_width_standard(self):
        """Default terminal width should be standard (80 columns)."""
        assert UI_CONFIG.DEFAULT_TERM_WIDTH == 80

    def test_default_term_height_reasonable(self):
        """Default terminal height should be reasonable."""
        assert 20 <= UI_CONFIG.DEFAULT_TERM_HEIGHT <= 50

    def test_term_width_within_box_limits(self):
        """Default terminal width should be within box width limits."""
        assert (
            UI_CONFIG.MIN_BOX_WIDTH
            <= UI_CONFIG.DEFAULT_TERM_WIDTH
            <= UI_CONFIG.MAX_BOX_WIDTH
        )

    def test_ui_config_frozen(self):
        """UIConfig dataclass should be frozen (immutable)."""
        with pytest.raises(AttributeError):
            UI_CONFIG.MIN_BOX_WIDTH = 100  # type: ignore

    def test_create_custom_ui_config(self):
        """Should be able to create custom UIConfig instances."""
        custom = UIConfig(
            MIN_BOX_WIDTH=60,
            MAX_BOX_WIDTH=120,
            DEFAULT_TERM_WIDTH=100,
            DEFAULT_TERM_HEIGHT=30,
        )

        assert custom.MIN_BOX_WIDTH == 60
        assert custom.MAX_BOX_WIDTH == 120
        assert custom.DEFAULT_TERM_WIDTH == 100
        assert custom.DEFAULT_TERM_HEIGHT == 30

    @given(
        st.integers(min_value=40, max_value=80),
        st.integers(min_value=80, max_value=150),
    )
    def test_box_width_range_valid(self, min_width: int, max_width: int):
        """Box width ranges should accept reasonable values."""
        custom = UIConfig(
            MIN_BOX_WIDTH=min_width,
            MAX_BOX_WIDTH=max_width,
            DEFAULT_TERM_WIDTH=80,
            DEFAULT_TERM_HEIGHT=24,
        )
        assert custom.MIN_BOX_WIDTH == min_width
        assert custom.MAX_BOX_WIDTH == max_width


class TestConfigIntegration:
    """Integration tests for all config modules."""

    def test_all_configs_exist(self):
        """All config singletons should exist."""
        assert INPUT_LIMITS is not None
        assert GIT_CONFIG is not None
        assert UI_CONFIG is not None

    def test_all_configs_immutable(self):
        """All config objects should be immutable (frozen)."""
        with pytest.raises(AttributeError):
            INPUT_LIMITS.TYPE = 100  # type: ignore

        with pytest.raises(AttributeError):
            GIT_CONFIG.DEFAULT_TIMEOUT = 100  # type: ignore

        with pytest.raises(AttributeError):
            UI_CONFIG.MIN_BOX_WIDTH = 100  # type: ignore

    def test_configs_have_sensible_defaults(self):
        """All configs should have sensible default values."""
        # Input limits should allow reasonable text
        assert INPUT_LIMITS.MESSAGE >= 50
        assert INPUT_LIMITS.BODY >= 200

        # Timeouts should be reasonable
        assert GIT_CONFIG.DEFAULT_TIMEOUT >= 30
        assert GIT_CONFIG.DEFAULT_TIMEOUT <= 180

        # UI should fit standard terminals
        assert UI_CONFIG.DEFAULT_TERM_WIDTH >= 60
        assert UI_CONFIG.DEFAULT_TERM_WIDTH <= 120

    def test_config_relationships(self):
        """Config values should have logical relationships."""
        # Message body should be much larger than header
        assert INPUT_LIMITS.BODY > INPUT_LIMITS.MESSAGE * 2

        # Filter branch should take longer than regular operations
        assert GIT_CONFIG.FILTER_BRANCH_TIMEOUT > GIT_CONFIG.DEFAULT_TIMEOUT * 2

        # Max box should be bigger than min box
        assert UI_CONFIG.MAX_BOX_WIDTH > UI_CONFIG.MIN_BOX_WIDTH

    def test_configs_support_repr(self):
        """Config objects should have readable string representations."""
        input_repr = repr(INPUT_LIMITS)
        git_repr = repr(GIT_CONFIG)
        ui_repr = repr(UI_CONFIG)

        assert "InputLimits" in input_repr
        assert "GitConfig" in git_repr
        assert "UIConfig" in ui_repr

    def test_configs_support_equality(self):
        """Config objects should support equality comparison."""
        custom_input = InputLimits(
            TYPE=INPUT_LIMITS.TYPE,
            SCOPE=INPUT_LIMITS.SCOPE,
            MESSAGE=INPUT_LIMITS.MESSAGE,
            BODY=INPUT_LIMITS.BODY,
            TAG=INPUT_LIMITS.TAG,
            TAG_MESSAGE=INPUT_LIMITS.TAG_MESSAGE,
            EDIT_MESSAGE=INPUT_LIMITS.EDIT_MESSAGE,
            CONFIRMATION=INPUT_LIMITS.CONFIRMATION,
            COMMIT_COUNT=INPUT_LIMITS.COMMIT_COUNT,
        )

        assert custom_input == INPUT_LIMITS
        assert custom_input is not INPUT_LIMITS  # Different instances


class TestConfigPropertyBased:
    """Property-based tests for config validation."""

    @given(st.integers(min_value=1, max_value=1000))
    def test_input_limits_accept_positive_integers(self, value: int):
        """InputLimits should accept any positive integer."""
        custom = InputLimits(
            TYPE=value,
            SCOPE=value,
            MESSAGE=value,
            BODY=value,
            TAG=value,
            TAG_MESSAGE=value,
            EDIT_MESSAGE=value,
            CONFIRMATION=value,
            COMMIT_COUNT=value,
        )

        assert all(
            [
                custom.TYPE == value,
                custom.SCOPE == value,
                custom.MESSAGE == value,
                custom.BODY == value,
                custom.TAG == value,
                custom.TAG_MESSAGE == value,
                custom.EDIT_MESSAGE == value,
                custom.CONFIRMATION == value,
                custom.COMMIT_COUNT == value,
            ]
        )

    @given(st.integers(min_value=1, max_value=3600))
    def test_git_config_accepts_timeout_range(self, timeout: int):
        """GitConfig should accept reasonable timeout values."""
        custom = GitConfig(
            DEFAULT_TIMEOUT=timeout,
            PULL_TIMEOUT=timeout,
            FILTER_BRANCH_TIMEOUT=timeout,
            PRE_COMMIT_TIMEOUT=timeout,
        )

        assert all(
            [
                custom.DEFAULT_TIMEOUT == timeout,
                custom.PULL_TIMEOUT == timeout,
                custom.FILTER_BRANCH_TIMEOUT == timeout,
                custom.PRE_COMMIT_TIMEOUT == timeout,
            ]
        )

    @given(st.integers(min_value=10, max_value=500))
    def test_ui_config_accepts_dimension_range(self, dimension: int):
        """UIConfig should accept reasonable dimension values."""
        custom = UIConfig(
            MIN_BOX_WIDTH=dimension,
            MAX_BOX_WIDTH=dimension,
            DEFAULT_TERM_WIDTH=dimension,
            DEFAULT_TERM_HEIGHT=dimension,
        )

        assert all(
            [
                custom.MIN_BOX_WIDTH == dimension,
                custom.MAX_BOX_WIDTH == dimension,
                custom.DEFAULT_TERM_WIDTH == dimension,
                custom.DEFAULT_TERM_HEIGHT == dimension,
            ]
        )
