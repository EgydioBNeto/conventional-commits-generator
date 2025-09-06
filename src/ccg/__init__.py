"""Conventional Commits Generator - A CLI tool for standardized commit messages."""

from ._version import __version__
from .cli import main
from .core import (
    confirm_commit,
    confirm_push,
    generate_commit_message,
    handle_commit_operation,
    handle_git_workflow,
)
from .git import get_current_branch, get_repository_name
from .ui import print_info, print_logo, print_success

__all__ = [
    "main",
    "confirm_commit",
    "confirm_push",
    "generate_commit_message",
    "handle_commit_operation",
    "handle_git_workflow",
    "get_current_branch",
    "get_repository_name",
    "print_info",
    "print_logo",
    "print_success",
]
