"""Decorators for common validations and operations."""

import functools
import sys
from typing import Callable, List, Optional

from .config import ERROR_MESSAGES


def require_git_repo(func: Callable) -> Callable:
    """Decorator that ensures the function is called within a git repository."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from ..git import check_is_git_repo
        from ..ui.display import print_error

        if not check_is_git_repo():
            print_error(ERROR_MESSAGES["NOT_GIT_REPO"])
            return 1
        return func(*args, **kwargs)

    return wrapper


def require_remote_access(func: Callable) -> Callable:
    """Decorator that ensures remote access is available."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from ..git import check_remote_access

        if not check_remote_access():
            return 1
        return func(*args, **kwargs)

    return wrapper


def handle_keyboard_interrupt(exit_message: str = "Operation cancelled by user") -> Callable:
    """Decorator to handle KeyboardInterrupt exceptions consistently."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                from ..ui.display import print_warning

                print_warning(exit_message)
                return 130

        return wrapper

    return decorator


def validate_changes_exist(paths: Optional[List[str]] = None) -> Callable:
    """Decorator that ensures there are changes to commit."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from ..git import check_has_changes
            from ..ui.display import print_error

            if not check_has_changes(paths):
                print_error(
                    "No changes to commit in the specified path(s). Make some changes before running the tool."
                )
                return False
            return func(*args, **kwargs)

        return wrapper

    return decorator


def section_header(title: str) -> Callable:
    """Decorator to add section headers to functions."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from ..ui.display import print_section

            print_section(title)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def with_error_handling(default_return=None) -> Callable:
    """Decorator for consistent error handling."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                import traceback

                from ..ui.display import print_error

                print_error("An unexpected error occurred")
                print(f"\033[91m{str(e)}\033[0m")
                traceback.print_exc()
                return default_return

        return wrapper

    return decorator
