#!/usr/bin/env python3
"""
Script to generate an automatic changelog based on commits.
Analyzes commits since the last tag and categorizes them by type.
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Import shared utilities
from changelog_utils import (
    CHANGELOG_SECTION_ORDER,
    categorize_commits,
    get_commits_since_tag,
    get_current_version,
    get_latest_tag,
)


def format_changelog_section(version: str, categories: Dict[str, List[Dict]]) -> str:
    """Format changelog section for a version."""
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [f"## [{version}] - {today}", ""]

    for category, title in CHANGELOG_SECTION_ORDER:
        if category in categories and categories[category]:
            lines.append(f"### {title}")
            lines.append("")

            for commit in categories[category]:
                scope_text = f"**{commit['scope'].strip('()')}**: " if commit["scope"] else ""
                lines.append(f"- {scope_text}{commit['description']} ([{commit['hash']}])")

                if commit["body"] and len(commit["body"]) > 10:
                    body_lines = commit["body"].split("\n")[:3]
                    for body_line in body_lines:
                        if body_line.strip():
                            lines.append(f"  {body_line.strip()}")

            lines.append("")

    return "\n".join(lines)


def generate_full_changelog() -> str:
    """Generate complete changelog."""
    current_version = get_current_version()
    latest_tag = get_latest_tag()

    commits = get_commits_since_tag(latest_tag)

    if not commits:
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

    categories = categorize_commits(commits)

    changelog_header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

"""

    current_section = format_changelog_section(current_version, categories)

    changelog_file = Path("CHANGELOG.md")

    if changelog_file.exists():
        existing_content = changelog_file.read_text()

        version_pattern = r"## \[\d+\.\d+\.\d+\].*?(?=## \[|\Z)"
        old_versions = re.findall(version_pattern, existing_content, re.DOTALL)

        full_changelog = changelog_header + current_section

        if old_versions:
            filtered_versions = [
                v for v in old_versions if not v.startswith(f"## [{current_version}]")
            ]
            if filtered_versions:
                full_changelog += "\n" + "\n".join(filtered_versions)
    else:
        full_changelog = changelog_header + current_section

    return full_changelog


def main():
    """Generate and output changelog."""
    try:
        changelog = generate_full_changelog()
        print(changelog)

    except Exception as e:
        print(f"Error generating changelog: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
