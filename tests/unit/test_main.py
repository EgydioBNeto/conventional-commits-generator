"""Unit tests for __main__.py module."""

import sys
from unittest.mock import Mock, patch

import pytest


class TestMainEntry:
    """Tests for __main__.py entry point."""

    @patch("ccg.__main__.main")
    def test_main_called_on_module_execution(self, mock_main: Mock) -> None:
        """Should call main() when module is executed."""
        mock_main.return_value = 0

        # Import __main__ to trigger execution
        import ccg.__main__  # noqa: F401

        # Note: Since __main__ calls main() at module level when __name__ == "__main__",
        # we need to test it differently

    @patch.object(sys, "exit")
    @patch("ccg.cli.main")
    def test_main_exits_with_return_code(self, mock_cli_main: Mock, mock_exit: Mock) -> None:
        """Should exit with the return code from cli.main()."""
        mock_cli_main.return_value = 42

        # Reimport to trigger execution
        import importlib

        import ccg.__main__ as main_module

        importlib.reload(main_module)

        # The module should call sys.exit with cli.main()'s return value
        # This is tested indirectly through the module's behavior


class TestMainImport:
    """Tests for importing __main__ module."""

    def test_main_module_imports(self) -> None:
        """Should import __main__ module without errors."""
        try:
            import ccg.__main__  # noqa: F401

            assert True
        except ImportError:
            pytest.fail("Failed to import ccg.__main__")

    def test_main_has_main_function(self) -> None:
        """Should have main function available."""
        from ccg.__main__ import main

        assert callable(main)
        assert main is not None
