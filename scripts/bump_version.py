#!/usr/bin/env python3
"""
Script to automatically bump the CCG version.
Updates the necessary files with the new version using shared utilities.
"""

import argparse
import sys

from common_logging import get_logger
from shared_utils import ChangelogUtils, CommitUtils, FileUtils, GitUtils, VersionUtils

logger = get_logger("bump_version")


def generate_changelog_content(new_version: str) -> str:
    """
    Generate changelog content based on actual git commits.

    Analyzes commits since the latest tag and categorizes them
    into conventional commit types for changelog generation.

    Args:
        new_version: Version number to generate changelog for

    Returns:
        Formatted changelog section as string

    Example:
        content = generate_changelog_content("2.3.0")
    """
    latest_tag = GitUtils.get_latest_tag()
    commits = GitUtils.get_commits_since_tag(latest_tag)

    if not commits:
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        return f"""## [{new_version}] - {today}

### Added
- Version {new_version} release

### Changed

### Fixed
"""

    categories = CommitUtils.categorize_commits(commits)
    return ChangelogUtils.format_changelog_section(new_version, categories)


def update_changelog_with_real_content(new_version: str) -> None:
    """
    Update CHANGELOG.md with real content based on git commits.

    Creates or updates the changelog file with automatically generated
    content from conventional commits since the last release.

    Args:
        new_version: Version number to add to changelog
    """
    from pathlib import Path

    changelog_file = Path("CHANGELOG.md")
    new_section_content = generate_changelog_content(new_version)

    if not changelog_file.exists():
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

{new_section_content}
"""
    else:
        content = changelog_file.read_text()

        unreleased_section = "## [Unreleased]"
        new_section = f"## [Unreleased]\n\n{new_section_content}"

        if unreleased_section in content:
            updated_content = content.replace(unreleased_section, new_section, 1)
        else:
            lines = content.split("\n")
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith("##") and "[" in line:
                    header_end = i
                    break

            if header_end > 0:
                lines.insert(header_end, "")
                lines.insert(header_end + 1, new_section_content.strip())
                lines.insert(header_end + 1, "")

            updated_content = "\n".join(lines)

        changelog_content = updated_content

    changelog_file.write_text(changelog_content)
    logger.success(f"Updated {changelog_file} with version {new_version}")


def main():
    """
    Main entry point for the version bumping script.

    Parses command line arguments and performs the version bump operation
    including updating all relevant files and generating changelog content.
    """
    parser = argparse.ArgumentParser(description="Bump version in CCG project")
    parser.add_argument(
        "--type",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Type of version bump (default: patch)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be changed without making changes"
    )

    args = parser.parse_args()

    try:
        current_version = VersionUtils.get_current_version()
        logger.info(f"Current version: {current_version}")

        new_version = VersionUtils.bump_version(current_version, args.type)
        logger.info(f"New version: {new_version} (bump: {args.type})")

        if args.dry_run:
            logger.info("Dry run mode - no files will be modified")
            logger.info(f"Would update version from {current_version} to {new_version}")
            logger.info("Changelog content that would be generated:")
            changelog_content = generate_changelog_content(new_version)
            print("=" * 50)
            print(changelog_content)
            print("=" * 50)
            return

        logger.step("Updating files...")
        FileUtils.update_version_file(new_version)
        FileUtils.update_pyproject_toml(new_version)
        FileUtils.update_security_md(new_version)
        update_changelog_with_real_content(new_version)

        logger.success(f"Successfully bumped version to {new_version}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
