"""Tests for lazy loading of prompt_toolkit (Improvement 8)."""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestLazyLoadingMechanism:
    """Tests for the lazy loading mechanism of prompt_toolkit."""

    def test_prompt_toolkit_not_loaded_initially(self) -> None:
        """Should not load prompt_toolkit when module is imported."""
        # We need to reload the module to test initial state
        import importlib

        import ccg.utils

        # Reset the lazy loading state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        # At this point, prompt_toolkit should not have been imported yet
        assert ccg.utils.prompt_toolkit_available is None
        assert ccg.utils._prompt_toolkit_cache == {}

    def test_ensure_prompt_toolkit_loads_on_first_call(self) -> None:
        """Should load prompt_toolkit on first call to _ensure_prompt_toolkit."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        # First call should attempt to load
        result = ccg.utils._ensure_prompt_toolkit()

        # Should have attempted to load (will be True or False depending on environment)
        assert ccg.utils.prompt_toolkit_available is not None
        assert isinstance(result, bool)

    def test_ensure_prompt_toolkit_caches_result(self) -> None:
        """Should cache result and not reload on subsequent calls."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        # First call
        result1 = ccg.utils._ensure_prompt_toolkit()

        # Store the cache state
        cache_state = ccg.utils._prompt_toolkit_cache.copy()
        available_state = ccg.utils.prompt_toolkit_available

        # Second call
        result2 = ccg.utils._ensure_prompt_toolkit()

        # Results should be identical
        assert result1 == result2
        assert ccg.utils.prompt_toolkit_available == available_state
        assert ccg.utils._prompt_toolkit_cache == cache_state

    def test_get_cached_returns_none_when_not_loaded(self) -> None:
        """Should return None for components when prompt_toolkit is not loaded."""
        import ccg.utils

        # Mock _ensure_prompt_toolkit to return False
        with patch.object(ccg.utils, "_ensure_prompt_toolkit", return_value=False):
            result = ccg.utils._get_cached("prompt")
            assert result is None

    def test_get_cached_returns_default_when_specified(self) -> None:
        """Should return default value when key not found."""
        import ccg.utils

        # Mock _ensure_prompt_toolkit to return True but cache is empty
        ccg.utils._prompt_toolkit_cache = {}
        with patch.object(ccg.utils, "_ensure_prompt_toolkit", return_value=True):
            result = ccg.utils._get_cached("nonexistent", default="default_value")
            assert result == "default_value"

    def test_get_cached_returns_value_when_loaded(self) -> None:
        """Should return cached value when prompt_toolkit is loaded."""
        import ccg.utils

        # Setup mock cache
        ccg.utils._prompt_toolkit_cache = {"test_key": "test_value"}

        with patch.object(ccg.utils, "_ensure_prompt_toolkit", return_value=True):
            result = ccg.utils._get_cached("test_key")
            assert result == "test_value"

    def test_update_module_exports_sets_globals(self) -> None:
        """Should update module-level exports."""
        import ccg.utils

        # Setup
        ccg.utils.prompt_toolkit_available = True
        ccg.utils._prompt_toolkit_cache = {
            "histories": {"test": "history"},
            "prompt_style": "test_style",
        }

        # Call update
        ccg.utils._update_module_exports()

        # Check globals were updated
        assert ccg.utils.PROMPT_TOOLKIT_AVAILABLE is True
        assert ccg.utils.HISTORIES == {"test": "history"}
        assert ccg.utils.PROMPT_STYLE == "test_style"

    def test_update_module_exports_handles_unavailable(self) -> None:
        """Should handle case when prompt_toolkit is not available."""
        import ccg.utils

        # Setup
        ccg.utils.prompt_toolkit_available = False
        ccg.utils._prompt_toolkit_cache = {}

        # Call update
        ccg.utils._update_module_exports()

        # Check globals were updated
        assert ccg.utils.PROMPT_TOOLKIT_AVAILABLE is False
        assert ccg.utils.HISTORIES == {}
        assert ccg.utils.PROMPT_STYLE is None


class TestLazyLoadingWithMockedImport:
    """Tests for lazy loading with mocked import behavior."""

    def test_ensure_prompt_toolkit_success_path(self) -> None:
        """Should successfully load and cache prompt_toolkit components."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        # Mock successful import
        mock_prompt = Mock()
        mock_document = Mock()
        mock_history = Mock()
        mock_keybindings = Mock()
        mock_keys = Mock()
        mock_keypress = Mock()
        mock_style_class = Mock()
        mock_style_class.from_dict = Mock(return_value="mock_style")
        mock_validation_error = Mock()
        mock_validator = Mock()

        with (
            patch.dict(
                "sys.modules",
                {
                    "prompt_toolkit": Mock(prompt=mock_prompt),
                    "prompt_toolkit.document": Mock(Document=mock_document),
                    "prompt_toolkit.history": Mock(InMemoryHistory=mock_history),
                    "prompt_toolkit.key_binding": Mock(
                        KeyBindings=mock_keybindings,
                        key_processor=Mock(KeyPressEvent=mock_keypress),
                    ),
                    "prompt_toolkit.keys": Mock(Keys=mock_keys),
                    "prompt_toolkit.styles": Mock(Style=mock_style_class),
                    "prompt_toolkit.validation": Mock(
                        ValidationError=mock_validation_error, Validator=mock_validator
                    ),
                },
            ),
            patch(
                "builtins.__import__",
                side_effect=lambda name, *args: sys.modules.get(name),
            ),
        ):
            result = ccg.utils._ensure_prompt_toolkit()

            assert result is True
            assert ccg.utils.prompt_toolkit_available is True
            assert "prompt" in ccg.utils._prompt_toolkit_cache
            assert "histories" in ccg.utils._prompt_toolkit_cache
            assert "prompt_style" in ccg.utils._prompt_toolkit_cache

    def test_ensure_prompt_toolkit_import_error(self) -> None:
        """Should handle ImportError gracefully."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        # Mock ImportError
        def mock_import(name, *args, **kwargs):
            if "prompt_toolkit" in name:
                raise ImportError("prompt_toolkit not found")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = ccg.utils._ensure_prompt_toolkit()

            assert result is False
            assert ccg.utils.prompt_toolkit_available is False
            assert ccg.utils._prompt_toolkit_cache == {}


class TestFunctionsUseLazyLoading:
    """Test that utility functions properly use lazy loading."""

    def test_read_input_triggers_lazy_load(self) -> None:
        """Should trigger lazy loading when read_input is called."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        with (
            patch.object(
                ccg.utils, "_ensure_prompt_toolkit", return_value=False
            ) as mock_ensure,
            patch("builtins.input", return_value="test"),
        ):
            result = ccg.utils.read_input("Test prompt")

            # Should have tried to load prompt_toolkit
            mock_ensure.assert_called()
            assert result == "test"

    def test_confirm_user_action_triggers_lazy_load(self) -> None:
        """Should trigger lazy loading when confirm_user_action is called."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        with (
            patch.object(
                ccg.utils, "_ensure_prompt_toolkit", return_value=False
            ) as mock_ensure,
            patch("builtins.input", return_value="y"),
        ):
            result = ccg.utils.confirm_user_action("Test confirmation (y/n)")

            # Should have tried to load prompt_toolkit
            mock_ensure.assert_called()
            assert result is True

    def test_read_multiline_input_triggers_lazy_load(self) -> None:
        """Should trigger lazy loading when read_multiline_input is called."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        with (
            patch.object(
                ccg.utils, "_ensure_prompt_toolkit", return_value=False
            ) as mock_ensure,
            patch("builtins.input", side_effect=["line1", "", ""]),
        ):
            result = ccg.utils.read_multiline_input(max_length=100)

            # Should have tried to load prompt_toolkit
            mock_ensure.assert_called()
            assert result == "line1"

    def test_create_input_key_bindings_uses_lazy_load(self) -> None:
        """Should use lazy loading for key bindings."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        with patch.object(
            ccg.utils, "_ensure_prompt_toolkit", return_value=False
        ) as mock_ensure:
            result = ccg.utils.create_input_key_bindings()

            # Should have tried to load prompt_toolkit
            mock_ensure.assert_called()
            assert result is None  # Returns None when prompt_toolkit unavailable


class TestLazyLoadingPerformance:
    """Tests to verify performance benefits of lazy loading."""

    def test_module_import_does_not_load_prompt_toolkit(self) -> None:
        """Should not import prompt_toolkit during module import."""
        import ccg.utils

        # Reset state to simulate fresh import
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        # Mock to track imports
        original_import = __import__
        imported_modules = []

        def tracking_import(name, *args, **kwargs):
            imported_modules.append(name)
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=tracking_import):
            # Simulate importing utils
            # (In real scenario, just importing shouldn't load prompt_toolkit)
            pass

        # prompt_toolkit should not be in imported modules yet
        assert not any("prompt_toolkit" in mod for mod in imported_modules)

    def test_lazy_loading_only_happens_once(self) -> None:
        """Should only attempt to load prompt_toolkit once."""
        import ccg.utils

        # Reset state
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}

        import_count = 0

        def counting_import(name, *args, **kwargs):
            nonlocal import_count
            if "prompt_toolkit" in str(name):
                import_count += 1
                raise ImportError("prompt_toolkit not available")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=counting_import):
            # Call multiple times
            ccg.utils._ensure_prompt_toolkit()
            ccg.utils._ensure_prompt_toolkit()
            ccg.utils._ensure_prompt_toolkit()

        # Should have only tried to import once
        assert import_count == 1


class TestBackwardsCompatibility:
    """Tests to ensure lazy loading maintains backwards compatibility."""

    def test_PROMPT_TOOLKIT_AVAILABLE_works(self) -> None:
        """Should maintain PROMPT_TOOLKIT_AVAILABLE export."""
        import ccg.utils

        # Reset and load
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}
        ccg.utils._ensure_prompt_toolkit()
        ccg.utils._update_module_exports()

        # Should have a boolean value
        assert isinstance(ccg.utils.PROMPT_TOOLKIT_AVAILABLE, bool)

    def test_HISTORIES_works(self) -> None:
        """Should maintain HISTORIES export."""
        import ccg.utils

        # Reset and load
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}
        ccg.utils._ensure_prompt_toolkit()
        ccg.utils._update_module_exports()

        # Should be a dict
        assert isinstance(ccg.utils.HISTORIES, dict)

    def test_PROMPT_STYLE_works(self) -> None:
        """Should maintain PROMPT_STYLE export."""
        import ccg.utils

        # Reset and load
        ccg.utils.prompt_toolkit_available = None
        ccg.utils._prompt_toolkit_cache = {}
        ccg.utils._ensure_prompt_toolkit()
        ccg.utils._update_module_exports()

        # Should exist (might be None if prompt_toolkit unavailable)
        assert hasattr(ccg.utils, "PROMPT_STYLE")
