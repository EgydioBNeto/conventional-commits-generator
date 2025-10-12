#!/usr/bin/env python3
"""Shared utilities for changelog and version management scripts."""

import re
import subprocess
from collections import defaultdict
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


def get_current_version() -> str:
    """Get current version from __init__.py."""
    init_file = Path("src/ccg/__init__.py")

    if not init_file.exists():
        return "0.0.0"

    content = init_file.read_text()
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)

    return match.group(1) if match else "0.0.0"


def get_latest_tag() -> str:
    """Get the latest git tag."""
    output = run_git_command(["git", "describe", "--tags", "--abbrev=0"])
    return output if output else "HEAD"


def get_commits_since_tag(tag: str) -> List[Tuple[str, str, str, str]]:
    """Get commits since the given tag.

    Returns:
        List of tuples containing (hash, subject, body, date)
    """
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
    """Parse conventional commit message.

    Args:
        subject: Commit subject line
        body: Commit body

    Returns:
        Dictionary with parsed commit information
    """
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


def categorize_commits(
    commits: List[Tuple[str, str, str, str]],
) -> Dict[str, List[Dict]]:
    """Categorize commits by type.

    Args:
        commits: List of commit tuples (hash, subject, body, date)

    Returns:
        Dictionary mapping category names to lists of commit info
    """
    categories = defaultdict(list)

    for commit_hash, subject, body, date in commits:
        # Skip merge commits and version bumps
        if (
            subject.startswith("Merge ")
            or "bump version" in subject.lower()
            or subject.startswith(":wrench: chore: bump version")
        ):
            continue

        parsed = parse_commit_message(subject, body)
        commit_type = parsed["type"]

        # Determine category
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


# Changelog section order - used by multiple scripts
CHANGELOG_SECTION_ORDER = [
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
