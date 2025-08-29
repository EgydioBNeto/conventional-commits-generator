#!/usr/bin/env python3
"""
Script to automatically bump the CCG version.
Updates the necessary files with the new version.
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def parse_version(version_string: str) -> Tuple[int, int, int]:
    """Parse version string into major.minor.patch tuple."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_string)
    if not match:
        raise ValueError(f"Invalid version format: {version_string}")

    return tuple(map(int, match.groups()))


def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version based on type."""
    major, minor, patch = parse_version(current_version)

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
        raise ValueError(f"Invalid bump type: {bump_type}")

    return f"{major}.{minor}.{patch}"


def get_current_version() -> str:
    """Get current version from __init__.py."""
    init_file = Path("src/ccg/__init__.py")

    if not init_file.exists():
        raise FileNotFoundError(f"File not found: {init_file}")

    content = init_file.read_text()
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)

    if not match:
        raise ValueError("Version not found in __init__.py")

    return match.group(1)


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
    from datetime import datetime

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

    has_changes = any(categories.get(cat, []) for cat, _ in section_order)

    if not has_changes:
        lines.append("### Added")
        lines.append(f"- Version {version} release")
        lines.append("")
    else:
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


def generate_changelog_content(new_version: str) -> str:
    """Generate changelog content based on actual commits."""
    latest_tag = get_latest_tag()
    commits = get_commits_since_tag(latest_tag)

    if not commits:
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        return f"""## [{new_version}] - {today}

### Added
- Version {new_version} release

### Changed

### Fixed
"""

    categories = categorize_commits(commits)
    return format_changelog_section(new_version, categories)


def update_init_file(new_version: str) -> None:
    """Update version in __init__.py."""
    init_file = Path("src/ccg/__init__.py")
    content = init_file.read_text()

    updated_content = re.sub(
        r'__version__ = ["\'][^"\']+["\']', f'__version__ = "{new_version}"', content
    )

    init_file.write_text(updated_content)
    print(f"✅ Updated {init_file} with version {new_version}")


def update_pyproject_toml(new_version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_file = Path("pyproject.toml")

    if not pyproject_file.exists():
        print(f"⚠️  {pyproject_file} not found, skipping")
        return

    content = pyproject_file.read_text()

    updated_content = re.sub(
        r'^version = ["\'][^"\']+["\']', f'version = "{new_version}"', content, flags=re.MULTILINE
    )

    pyproject_file.write_text(updated_content)
    print(f"✅ Updated {pyproject_file} with version {new_version}")


def update_security_md(new_version: str) -> None:
    """Update supported versions table in SECURITY.md."""
    security_file = Path(".github/SECURITY.md")

    if not security_file.exists():
        print(f"⚠️  {security_file} not found, skipping")
        return

    content = security_file.read_text()

    major_version = new_version.split(".")[0]

    updated_content = re.sub(
        r"\| >= \d+\.\d+\.\d+\s*\| ✅\s*\|", f"| >= {major_version}.0.0   | ✅     |", content
    )

    if major_version != "1":
        prev_major = str(int(major_version) - 1)
        updated_content = re.sub(
            r"\| <= \d+\.\d+\.\d+\s*\| ❌\s*\|",
            f"| <= {prev_major}.x.x   | ❌     |",
            updated_content,
        )

    security_file.write_text(updated_content)
    print(f"✅ Updated {security_file} with version {new_version}")


def update_changelog_with_real_content(new_version: str) -> None:
    """Update changelog with real content based on commits."""
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
    print(f"✅ Updated {changelog_file} with version {new_version}")


def main():
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
        current_version = get_current_version()
        print(f"📋 Current version: {current_version}")

        new_version = bump_version(current_version, args.type)
        print(f"🚀 New version: {new_version} (bump: {args.type})")

        if args.dry_run:
            print("🔍 Dry run mode - no files will be modified")
            print(f"Would update version from {current_version} to {new_version}")
            print("\n📝 Changelog content that would be generated:")
            changelog_content = generate_changelog_content(new_version)
            print("=" * 50)
            print(changelog_content)
            print("=" * 50)
            return

        print("\n📝 Updating files...")
        update_init_file(new_version)
        update_pyproject_toml(new_version)
        update_security_md(new_version)
        update_changelog_with_real_content(new_version)

        print(f"\n🎉 Successfully bumped version to {new_version}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
