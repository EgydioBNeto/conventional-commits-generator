#!/usr/bin/env python3
"""
Script to generate an automatic changelog based on commits.
Analyzes commits since the last tag and categorizes them by type using shared utilities.
"""

import re
import sys
from pathlib import Path

from common_logging import get_logger
from shared_utils import ChangelogUtils, CommitUtils, GitUtils, VersionUtils

logger = get_logger("generate_changelog")


def generate_full_changelog() -> str:
    """
    Generate complete changelog content from git commit history.

    Creates a full changelog by analyzing all commits since the latest tag,
    categorizing them by conventional commit types, and formatting them
    into a standardized changelog format.

    Returns:
        Complete changelog content as formatted string

    Example:
        changelog = generate_full_changelog()
        print(changelog)  # Full markdown changelog
    """
    current_version = VersionUtils.get_current_version(raise_on_error=False)
    latest_tag = GitUtils.get_latest_tag()

    commits = GitUtils.get_commits_since_tag(latest_tag)

    if not commits:
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        return f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{current_version}] - {today}

### Added
- Initial automated changelog generation
"""

    categories = CommitUtils.categorize_commits(commits)

    changelog_header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

"""

    current_section = ChangelogUtils.format_changelog_section(current_version, categories)

    changelog_file = Path("CHANGELOG.md")

    if changelog_file.exists():
        existing_content = changelog_file.read_text()

        # Extract existing version sections to preserve them
        version_pattern = r"## \[\d+\.\d+\.\d+\].*?(?=## \[|\Z)"
        old_versions = re.findall(version_pattern, existing_content, re.DOTALL)

        full_changelog = changelog_header + current_section

        if old_versions:
            # Filter out the current version if it already exists to avoid duplicates
            filtered_versions = [
                v for v in old_versions if not v.startswith(f"## [{current_version}]")
            ]
            if filtered_versions:
                full_changelog += "\n" + "\n".join(filtered_versions)
    else:
        full_changelog = changelog_header + current_section

    return full_changelog


def main():
    """
    Generate and output complete changelog content.

    Main entry point that generates the full changelog and prints it to stdout.
    This output can be redirected to a file or used in other scripts.

    Example usage:
        python generate_changelog.py > CHANGELOG.md
    """
    try:
        changelog = generate_full_changelog()
        print(changelog)

    except Exception as e:
        logger.error(f"Error generating changelog: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
