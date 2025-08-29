#!/usr/bin/env python3
"""
Script to generate an automatic changelog based on commits.
Analyzes commits since the last tag and categorizes them by type.
"""

import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def run_git_command(command: List[str]) -> str:
    """Execute git command and return output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {' '.join(command)}")
        print(f"Error: {e.stderr}")
        return ""


def get_latest_tag() -> str:
    """Get the latest git tag."""
    output = run_git_command(["git", "describe", "--tags", "--abbrev=0"])
    return output if output else "HEAD"


def get_current_version() -> str:
    """Get current version from __init__.py."""
    init_file = Path("src/ccg/__init__.py")

    if not init_file.exists():
        return "0.0.0"

    content = init_file.read_text()
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)

    return match.group(1) if match else "0.0.0"


def get_commits_since_tag(tag: str) -> List[Tuple[str, str, str, str]]:
    """Get commits since the given tag."""
    if tag == "HEAD":
        command = ["git", "log", "--pretty=format:%H|%s|%b|%aI"]
    else:
        command = ["git", "log", f"{tag}..HEAD", "--pretty=format:%H|%s|%b|%aI"]

    output = run_git_command(command)

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


def parse_commit_message(subject: str, body: str) -> Dict[str, str]:
    """Parse conventional commit message."""
    pattern = r"^(?P<emoji>:\w+:\s+)?(?P<type>\w+)(?P<scope>\([^)]+\))?(?P<breaking>!)?:\s*(?P<description>.+)$"

    match = re.match(pattern, subject)

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


def categorize_commits(commits: List[Tuple[str, str, str, str]]) -> Dict[str, List[Dict]]:
    """Categorize commits by type."""
    categories = defaultdict(list)

    for commit_hash, subject, body, date in commits:
        if (
            subject.startswith("Merge ")
            or "bump version" in subject.lower()
            or subject.startswith("🔧 chore: bump version")
        ):
            continue

        parsed = parse_commit_message(subject, body)

        commit_type = parsed["type"]

        if parsed["breaking"]:
            category = "breaking"
        elif commit_type in ["feat", "feature"]:
            category = "added"
        elif commit_type == "fix":
            category = "fixed"
        elif commit_type in ["docs", "doc"]:
            category = "documentation"
        elif commit_type in ["style", "refactor", "perf"]:
            category = "changed"
        elif commit_type in ["test", "tests"]:
            category = "tests"
        elif commit_type in ["chore", "build", "ci"]:
            category = "maintenance"
        elif commit_type == "revert":
            category = "reverted"
        else:
            category = "other"

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


def format_changelog_section(version: str, categories: Dict[str, List[Dict]]) -> str:
    """Format changelog section for a version."""
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [f"## [{version}] - {today}", ""]

    section_order = [
        ("breaking", "💥 BREAKING CHANGES"),
        ("added", "✨ Added"),
        ("changed", "♻️ Changed"),
        ("fixed", "🐛 Fixed"),
        ("documentation", "📚 Documentation"),
        ("tests", "🧪 Tests"),
        ("maintenance", "🔧 Maintenance"),
        ("reverted", "⏪ Reverted"),
        ("other", "📦 Other"),
    ]

    for category, title in section_order:
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
