"""Strategy Pattern implementation for Git commit operations.

This module provides a clean, extensible architecture for handling different
git operations (edit, delete) using the Strategy Pattern. Each strategy
encapsulates a specific git technique (amend, filter-branch, rebase, reset).
"""

import logging
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ccg.cache import invalidate_repository_cache
from ccg.config import GIT_CONFIG
from ccg.platform_utils import (
    get_filter_branch_command,
    set_file_permissions_executable,
    set_file_permissions_secure,
)
from ccg.progress import ProgressSpinner
from ccg.utils import print_error, print_info, print_process

logger = logging.getLogger("ccg.git_strategies")


class CommitEditStrategy(ABC):
    """Abstract base class for commit editing strategies.

    Each concrete strategy implements a specific technique for modifying
    commit messages (e.g., amend for latest, filter-branch for old commits).
    """

    @abstractmethod
    def can_handle(self, commit_hash: str, latest_commit_hash: str) -> bool:
        """Check if this strategy can handle editing the given commit.

        Args:
            commit_hash: Hash of commit to edit
            latest_commit_hash: Hash of the latest commit (HEAD)

        Returns:
            True if strategy can handle this commit, False otherwise
        """
        pass  # pragma: no cover

    @abstractmethod
    def edit(
        self, commit_hash: str, new_message: str, new_body: Optional[str] = None, **kwargs: object
    ) -> bool:
        """Edit the commit message using this strategy's technique.

        Args:
            commit_hash: Full hash of commit to edit
            new_message: New commit subject line
            new_body: Optional new commit body
            **kwargs: Additional strategy-specific parameters

        Returns:
            True if edit succeeded, False on error
        """
        pass  # pragma: no cover

    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of this strategy.

        Returns:
            String describing when/how this strategy is used
        """
        pass  # pragma: no cover


class AmendStrategy(CommitEditStrategy):
    """Edit the latest commit using git commit --amend.

    This is the most efficient method for editing the most recent commit,
    as it doesn't require rewriting history beyond HEAD.
    """

    def can_handle(self, commit_hash: str, latest_commit_hash: str) -> bool:
        """Check if commit is the latest one (HEAD).

        Args:
            commit_hash: Hash of commit to edit
            latest_commit_hash: Hash of HEAD

        Returns:
            True if commit_hash matches latest_commit_hash
        """
        return commit_hash == latest_commit_hash

    def edit(
        self, commit_hash: str, new_message: str, new_body: Optional[str] = None, **kwargs: object
    ) -> bool:
        """Edit latest commit using git commit --amend.

        Args:
            commit_hash: Hash of commit to edit (for verification/display)
            new_message: New commit subject line
            new_body: Optional new commit body
            **kwargs: Ignored (for interface compatibility)

        Returns:
            True if commit amended successfully, False on error
        """
        from ccg.git import run_git_command

        full_commit_message = new_message
        if new_body:
            full_commit_message += f"\n\n{new_body}"

        temp_file = None
        try:
            try:
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                    f.write(full_commit_message)
                    temp_file = f.name
                # Set restrictive permissions (cross-platform)
                set_file_permissions_secure(temp_file)
            except (IOError, OSError, PermissionError) as e:
                logger.error(f"Failed to create temporary file: {str(e)}")
                print_error(f"Failed to create temporary commit message file: {str(e)}")
                return False

            success, _ = run_git_command(
                ["git", "commit", "--amend", "-F", temp_file, "--no-verify"],
                f"Failed to amend commit message for '{commit_hash[:7]}'",
                f"Commit message for '{commit_hash[:7]}' updated successfully",
            )

            if success:
                invalidate_repository_cache()

            return success
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

    def get_description(self) -> str:
        """Get description of amend strategy.

        Returns:
            Human-readable description
        """
        return "Edit latest commit using git commit --amend"


class FilterBranchStrategy(CommitEditStrategy):
    """Edit an old commit using git filter-branch.

    This strategy rewrites git history to modify commits that are not HEAD.
    It's more complex and time-consuming than amending, but necessary for
    editing older commits.
    """

    def can_handle(self, commit_hash: str, latest_commit_hash: str) -> bool:
        """Check if commit is not the latest one.

        Args:
            commit_hash: Hash of commit to edit
            latest_commit_hash: Hash of HEAD

        Returns:
            True if commit_hash differs from latest_commit_hash
        """
        return commit_hash != latest_commit_hash

    def edit(
        self, commit_hash: str, new_message: str, new_body: Optional[str] = None, **kwargs: object
    ) -> bool:
        """Edit old commit using git filter-branch.

        Args:
            commit_hash: Full hash of commit to edit
            new_message: New commit subject line
            new_body: Optional new commit body
            **kwargs: Optional 'is_initial_commit' boolean parameter

        Returns:
            True if commit edited successfully, False on error
        """
        from ccg.git import run_git_command

        is_initial_commit = kwargs.get("is_initial_commit", False)

        full_commit_message = new_message
        if new_body:
            full_commit_message += f"\n\n{new_body}"

        ccg_dir = Path.home() / ".ccg"
        try:
            ccg_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to create CCG directory: {str(e)}")
            print_error(f"Failed to create directory {ccg_dir}: {str(e)}")
            return False

        message_file = None
        script_file = None
        try:
            try:
                message_file = ccg_dir / f"commit_message_{commit_hash[:7]}.tmp"
                message_file.write_text(full_commit_message, encoding="utf-8")
                # Set restrictive permissions (cross-platform)
                set_file_permissions_secure(message_file)
                logger.debug(f"Created message file: {message_file}")
            except (IOError, OSError, PermissionError) as e:
                logger.error(f"Failed to create message file: {str(e)}")
                print_error(f"Failed to create temporary message file: {str(e)}")
                return False

            script_content = f"""#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    ["git", "rev-parse", "--short", "HEAD"],
    capture_output=True,
    text=True
)
current_hash = result.stdout.strip()

if current_hash == "{commit_hash[:7]}":
    with open(r"{message_file}", "r", encoding="utf-8") as f:
        sys.stdout.write(f.read())
else:
    sys.stdout.write(sys.stdin.read())
"""

            try:
                script_file = ccg_dir / f"msg_filter_{commit_hash[:7]}.py"
                script_file.write_text(script_content, encoding="utf-8")
                # Set executable permissions (cross-platform)
                set_file_permissions_executable(script_file)
                logger.debug(f"Created Python script file: {script_file}")
            except (IOError, OSError, PermissionError) as e:
                logger.error(f"Failed to create Python script file: {str(e)}")
                print_error(f"Failed to create temporary Python script file: {str(e)}")
                return False

            # Get platform-appropriate command for invoking the filter script
            filter_command = get_filter_branch_command(script_file)

            command = [
                "git",
                "filter-branch",
                "--force",
                "--msg-filter",
                filter_command,
            ]

            if is_initial_commit:
                command.extend(["--", "--all"])
            else:
                command.append(f"{commit_hash}^..HEAD")

            print_process(f"Updating commit message for '{commit_hash[:7]}'...")
            print_info("This may take a moment for repositories with many commits...")

            with ProgressSpinner("Rewriting git history"):
                success, output = run_git_command(
                    command,
                    f"Failed to edit commit message for '{commit_hash[:7]}'",
                    f"Commit message for '{commit_hash[:7]}' updated successfully",
                    show_output=True,
                    timeout=GIT_CONFIG.FILTER_BRANCH_TIMEOUT,
                )

            if not success:
                print_error("Error details:")
                if output:
                    print(output)
                return False

            invalidate_repository_cache()
            return True

        finally:
            for temp_file in [message_file, script_file]:
                if temp_file and temp_file.exists():
                    try:
                        temp_file.unlink()
                        logger.debug(f"Cleaned up temporary file: {temp_file}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {temp_file}: {str(e)}")

    def get_description(self) -> str:
        """Get description of filter-branch strategy.

        Returns:
            Human-readable description
        """
        return "Edit old commit using git filter-branch (rewrites history)"


EDIT_STRATEGIES: List[CommitEditStrategy] = [
    AmendStrategy(),
    FilterBranchStrategy(),
]


def edit_commit_with_strategy(
    commit_hash: str,
    latest_commit_hash: str,
    new_message: str,
    new_body: Optional[str] = None,
    **kwargs: object,
) -> bool:
    """Edit a commit message using the appropriate strategy.

    Automatically selects the correct strategy based on commit position.
    Tries each registered strategy until one reports it can handle the commit.

    Args:
        commit_hash: Full hash of commit to edit
        latest_commit_hash: Full hash of HEAD
        new_message: New commit subject line
        new_body: Optional new commit body
        **kwargs: Strategy-specific parameters (e.g., is_initial_commit)

    Returns:
        True if edit succeeded, False on error

    Raises:
        ValueError: If no strategy can handle the commit

    Example:
        >>> edit_commit_with_strategy(
        ...     "abc123...",
        ...     "abc123...",
        ...     "feat: new feature"
        ... )
        True
    """
    for strategy in EDIT_STRATEGIES:
        if strategy.can_handle(commit_hash, latest_commit_hash):
            logger.info(f"Using strategy: {strategy.get_description()}")
            return strategy.edit(commit_hash, new_message, new_body, **kwargs)

    logger.error(f"No strategy found to handle commit {commit_hash[:7]}")
    print_error(f"Unable to find appropriate strategy for editing commit {commit_hash[:7]}")
    return False
