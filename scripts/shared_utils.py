#!/usr/bin/env python3
"""
Shared utilities for scripts to avoid code duplication.
Provides common git operations, version handling, and commit processing.
"""

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from common_logging import get_logger

logger = get_logger("shared_utils")


class GitUtils:
    """Git-related utility functions."""

    @staticmethod
    def run_command(command: List[str]) -> str:
        """
        Execute a git command and return its output.

        Args:
            command: Git command as list of strings (e.g., ["git", "status"])

        Returns:
            Command output as string, empty string on failure

        Example:
            output = GitUtils.run_command(["git", "describe", "--tags"])
        """
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(command)}")
            logger.error(f"Error: {e.stderr}")
            return ""

    @staticmethod
    def get_latest_tag() -> str:
        """
        Get the most recent git tag.

        Returns:
            Latest tag name, or "HEAD" if no tags exist

        Example:
            tag = GitUtils.get_latest_tag()  # Returns "v2.2.4" or "HEAD"
        """
        output = GitUtils.run_command(["git", "describe", "--tags", "--abbrev=0"])
        return output if output else "HEAD"

    @staticmethod
    def get_commits_since_tag(tag: str) -> List[Tuple[str, str, str, str]]:
        """
        Get all commits since a specific tag.

        Args:
            tag: Git tag to use as reference point, use "HEAD" for all commits

        Returns:
            List of tuples: (hash, subject, body, date)

        Example:
            commits = GitUtils.get_commits_since_tag("v2.2.3")
        """
        if tag == "HEAD":
            command = ["git", "log", "--pretty=format:%H|%s|%b|%aI"]
        else:
            command = ["git", "log", f"{tag}..HEAD", "--pretty=format:%H|%s|%b|%aI"]

        output = GitUtils.run_command(command)

        if not output:
            return []

        commits = []
        for line in output.split("\n"):
            if line.strip():
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    hash_val, subject, body, date = parts
                    commits.append((hash_val, subject, body, date))

        return commits


class VersionUtils:
    """Version-related utility functions."""

    @staticmethod
    def get_current_version(raise_on_error: bool = True) -> str:
        """
        Read current version from _version.py file.

        Args:
            raise_on_error: If True, raises exception on error. If False, returns "0.0.0"

        Returns:
            Current version string

        Raises:
            FileNotFoundError: If _version.py doesn't exist (when raise_on_error=True)
            ValueError: If version format is invalid (when raise_on_error=True)

        Example:
            version = VersionUtils.get_current_version()  # "2.2.4"
            version = VersionUtils.get_current_version(False)  # "0.0.0" on error
        """
        version_file = Path("src/ccg/_version.py")

        if not version_file.exists():
            if raise_on_error:
                raise FileNotFoundError(f"File not found: {version_file}")
            return "0.0.0"

        content = version_file.read_text()
        match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)

        if not match:
            if raise_on_error:
                raise ValueError("Version not found in _version.py")
            return "0.0.0"

        return match.group(1)

    @staticmethod
    def parse_version_tuple(version_string: str) -> Tuple[int, int, int]:
        """
        Parse version string into major.minor.patch tuple.

        Args:
            version_string: Version in format "major.minor.patch"

        Returns:
            Tuple of (major, minor, patch) as integers

        Raises:
            ValueError: If version format is invalid

        Example:
            major, minor, patch = VersionUtils.parse_version_tuple("2.2.4")
        """
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_string)
        if not match:
            raise ValueError(f"Invalid version format: {version_string}")

        return tuple(map(int, match.groups()))

    @staticmethod
    def bump_version(current_version: str, bump_type: str) -> str:
        """
        Increment version based on semantic versioning rules.

        Args:
            current_version: Current version string (e.g., "2.2.4")
            bump_type: Type of bump ("major", "minor", or "patch")

        Returns:
            New version string

        Raises:
            ValueError: If bump_type is invalid

        Example:
            new_version = VersionUtils.bump_version("2.2.4", "minor")  # "2.3.0"
        """
        major, minor, patch = VersionUtils.parse_version_tuple(current_version)

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}. Use 'major', 'minor', or 'patch'")

        return f"{major}.{minor}.{patch}"


class CommitUtils:
    """Conventional commit processing utilities."""

    # Regex pattern for parsing conventional commits
    COMMIT_PATTERN = r"^(?P<emoji>:\w+:\s+)?(?P<type>\w+)(?P<scope>\([^)]+\))?(?P<breaking>!)?:\s*(?P<description>.+)$"

    # Mapping of commit types to changelog categories
    CATEGORY_MAPPING = {
        ("feat", "feature"): "added",
        ("fix",): "fixed",
        ("docs", "doc"): "documentation",
        ("style", "refactor", "perf"): "changed",
        ("test", "tests"): "tests",
        ("chore", "build", "ci"): "maintenance",
        ("revert",): "reverted",
    }

    @staticmethod
    def parse_commit_message(subject: str, body: str) -> Dict[str, str]:
        """
        Parse a conventional commit message into structured data.

        Args:
            subject: Commit subject line
            body: Commit body (can be empty)

        Returns:
            Dictionary with parsed commit information:
            - type: Commit type (feat, fix, etc.)
            - scope: Optional scope in parentheses
            - breaking: Boolean indicating breaking change
            - description: Main commit description
            - body: Commit body
            - emoji: Optional emoji prefix

        Example:
            info = CommitUtils.parse_commit_message(
                ":sparkles: feat(auth): add OAuth support",
                "Implements Google OAuth 2.0"
            )
        """
        match = re.match(CommitUtils.COMMIT_PATTERN, subject)

        if not match:
            return {
                "type": "other",
                "scope": "",
                "breaking": False,
                "description": subject,
                "body": body,
            }

        groups = match.groupdict()

        return {
            "type": groups["type"],
            "scope": groups["scope"] or "",
            "breaking": bool(groups["breaking"]),
            "description": groups["description"],
            "body": body,
            "emoji": groups["emoji"] or "",
        }

    @staticmethod
    def categorize_commits(commits: List[Tuple[str, str, str, str]]) -> Dict[str, List[Dict]]:
        """
        Group commits by their type for changelog generation.

        Args:
            commits: List of (hash, subject, body, date) tuples

        Returns:
            Dictionary mapping category names to lists of commit info

        Example:
            categories = CommitUtils.categorize_commits(commits)
            # {"added": [...], "fixed": [...], "maintenance": [...]}
        """
        categories = defaultdict(list)

        for commit_hash, subject, body, date in commits:
            # Skip merge commits and version bump commits
            if (
                subject.startswith("Merge ")
                or "bump version" in subject.lower()
                or subject.startswith(":wrench: chore: bump version")
            ):
                continue

            parsed = CommitUtils.parse_commit_message(subject, body)
            commit_type = parsed["type"]

            # Determine category
            if parsed["breaking"]:
                category = "breaking"
            else:
                category = "other"  # default
                for types_tuple, cat in CommitUtils.CATEGORY_MAPPING.items():
                    if commit_type in types_tuple:
                        category = cat
                        break

            categories[category].append(
                {
                    "hash": commit_hash[:7],
                    "description": parsed["description"],
                    "scope": parsed["scope"],
                    "body": parsed["body"],
                    "type": commit_type,
                    "original": subject,
                }
            )

        return categories


class ChangelogUtils:
    """Changelog formatting utilities."""

    # Standard section ordering for changelog
    SECTION_ORDER = [
        ("breaking", "💥 BREAKING CHANGES"),
        ("added", "✨ Added"),
        ("changed", "🔨 Changed"),
        ("fixed", "🐛 Fixed"),
        ("documentation", "📚 Documentation"),
        ("tests", "🧪 Tests"),
        ("maintenance", "🔧 Maintenance"),
        ("reverted", "⏪ Reverted"),
        ("other", "📦 Other"),
    ]

    @staticmethod
    def format_changelog_section(version: str, categories: Dict[str, List[Dict]]) -> str:
        """
        Format a changelog section for a specific version.

        Args:
            version: Version number (e.g., "2.2.4")
            categories: Categorized commits from CommitUtils.categorize_commits()

        Returns:
            Formatted changelog section as string

        Example:
            section = ChangelogUtils.format_changelog_section("2.2.4", categories)
        """
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        lines = [f"## [{version}] - {today}", ""]

        has_changes = any(categories.get(cat, []) for cat, _ in ChangelogUtils.SECTION_ORDER)

        if not has_changes:
            lines.append("### Added")
            lines.append(f"- Version {version} release")
            lines.append("")
        else:
            for category, title in ChangelogUtils.SECTION_ORDER:
                if category in categories and categories[category]:
                    lines.append(f"### {title}")
                    lines.append("")

                    for commit in categories[category]:
                        scope_text = (
                            f"**{commit['scope'].strip('()')}**: " if commit["scope"] else ""
                        )
                        lines.append(f"- {scope_text}{commit['description']} ([{commit['hash']}])")

                        # Add body lines if present and meaningful
                        if commit["body"] and len(commit["body"]) > 10:
                            body_lines = commit["body"].split("\n")[:3]  # Limit to 3 lines
                            for body_line in body_lines:
                                if body_line.strip():
                                    lines.append(f"  {body_line.strip()}")

                    lines.append("")

        return "\n".join(lines)


class FileUtils:
    """File system utilities for version and changelog management."""

    @staticmethod
    def update_version_file(new_version: str) -> None:
        """
        Update the version in src/ccg/_version.py.

        Args:
            new_version: New version string to write

        Raises:
            FileNotFoundError: If _version.py doesn't exist

        Example:
            FileUtils.update_version_file("2.3.0")
        """
        version_file = Path("src/ccg/_version.py")
        content = version_file.read_text()

        updated_content = re.sub(
            r'__version__ = ["\'][^"\']+["\']', f'__version__ = "{new_version}"', content
        )

        version_file.write_text(updated_content)
        logger.success(f"Updated {version_file} with version {new_version}")

    @staticmethod
    def update_pyproject_toml(new_version: str) -> None:
        """
        Update version in pyproject.toml if it exists.

        Args:
            new_version: New version string to write

        Example:
            FileUtils.update_pyproject_toml("2.3.0")
        """
        pyproject_file = Path("pyproject.toml")

        if not pyproject_file.exists():
            logger.warning(f"{pyproject_file} not found, skipping")
            return

        content = pyproject_file.read_text()

        updated_content = re.sub(
            r'^version = ["\'][^"\']+["\']',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE,
        )

        pyproject_file.write_text(updated_content)
        logger.success(f"Updated {pyproject_file} with version {new_version}")

    @staticmethod
    def update_security_md(new_version: str) -> None:
        """
        Update supported versions table in .github/SECURITY.md.

        Args:
            new_version: New version string to update in security policy

        Example:
            FileUtils.update_security_md("2.3.0")
        """
        security_file = Path(".github/SECURITY.md")

        if not security_file.exists():
            logger.warning(f"{security_file} not found, skipping")
            return

        content = security_file.read_text()
        major_version = new_version.split(".")[0]

        # Update supported version range
        updated_content = re.sub(
            r"\| >= \d+\.\d+\.\d+\s*\| ✅\s*\|", f"| >= {major_version}.0.0   | ✅     |", content
        )

        # Update unsupported version range
        if major_version != "1":
            prev_major = str(int(major_version) - 1)
            updated_content = re.sub(
                r"\| <= \d+\.\d+\.\d+\s*\| ❌\s*\|",
                f"| <= {prev_major}.x.x   | ❌     |",
                updated_content,
            )

        security_file.write_text(updated_content)
        logger.success(f"Updated {security_file} with version {new_version}")


# Convenience functions for backward compatibility
def run_git_command(command: List[str]) -> str:
    """Backward compatibility wrapper for GitUtils.run_command()."""
    return GitUtils.run_command(command)


def get_current_version() -> str:
    """Backward compatibility wrapper for VersionUtils.get_current_version()."""
    return VersionUtils.get_current_version(raise_on_error=False)


def get_latest_tag() -> str:
    """Backward compatibility wrapper for GitUtils.get_latest_tag()."""
    return GitUtils.get_latest_tag()


def get_commits_since_tag(tag: str) -> List[Tuple[str, str, str, str]]:
    """Backward compatibility wrapper for GitUtils.get_commits_since_tag()."""
    return GitUtils.get_commits_since_tag(tag)


def parse_commit_message(subject: str, body: str) -> Dict[str, str]:
    """Backward compatibility wrapper for CommitUtils.parse_commit_message()."""
    return CommitUtils.parse_commit_message(subject, body)


def categorize_commits(commits: List[Tuple[str, str, str, str]]) -> Dict[str, List[Dict]]:
    """Backward compatibility wrapper for CommitUtils.categorize_commits()."""
    return CommitUtils.categorize_commits(commits)
