#!/usr/bin/env python3
"""
Script to automatically bump the CCG version.
Updates the necessary files with the new version.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Import shared utilities
from changelog_utils import (
    CHANGELOG_SECTION_ORDER,
    categorize_commits,
    get_commits_since_tag,
    get_current_version,
    get_latest_tag,
)


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


def format_changelog_section(version: str, categories: Dict[str, List[Dict]]) -> str:
    """Format changelog section for a version."""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")

    lines = [f"## [{version}] - {today}", ""]

    has_changes = any(categories.get(cat, []) for cat, _ in CHANGELOG_SECTION_ORDER)

    if not has_changes:
        lines.append("### Added")
        lines.append(f"- Version {version} release")
        lines.append("")
    else:
        # Remove duplicates - keep only the latest commit for each description
        seen_descriptions = {}
        for category, title in CHANGELOG_SECTION_ORDER:
            if category in categories and categories[category]:
                # Filter duplicates by keeping last occurrence
                unique_commits = []
                for commit in reversed(categories[category]):
                    desc_key = f"{commit['description'].lower().strip()}"
                    if desc_key not in seen_descriptions:
                        seen_descriptions[desc_key] = True
                        unique_commits.insert(0, commit)

                if unique_commits:
                    lines.append(f"### {title}")
                    lines.append("")

                    for commit in unique_commits:
                        scope_text = (
                            f"**{commit['scope'].strip('()')}**: " if commit["scope"] else ""
                        )
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
        r'^version = ["\'][^"\']+["\']',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE,
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
        r"\| >= \d+\.\d+\.\d+\s*\| ✅\s*\|",
        f"| >= {major_version}.0.0   | ✅     |",
        content,
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
    docs_changelog_file = Path("docs/community/changelog.md")

    new_section_content = generate_changelog_content(new_version)

    if not changelog_file.exists():
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

{new_section_content}
"""
    else:
        content = changelog_file.read_text()

        # Find the first release section (after header)
        lines = content.split("\n")
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("##") and "[" in line:
                header_end = i
                break

        if header_end > 0:
            # Insert new section with --- separator before existing releases
            lines.insert(header_end, "---")
            lines.insert(header_end + 1, "")
            lines.insert(header_end + 2, new_section_content.strip())
            lines.insert(header_end + 3, "")
        else:
            # No existing releases, add after header
            for i, line in enumerate(lines):
                if line.strip() == "":
                    header_end = i
                    break
            if header_end > 0:
                lines.insert(header_end + 1, "---")
                lines.insert(header_end + 2, "")
                lines.insert(header_end + 3, new_section_content.strip())
                lines.insert(header_end + 4, "")

        changelog_content = "\n".join(lines)

    # Write to root changelog
    changelog_file.write_text(changelog_content)
    print(f"✅ Updated {changelog_file} with version {new_version}")

    # Sync to docs changelog
    if docs_changelog_file.parent.exists():
        docs_changelog_file.write_text(changelog_content)
        print(f"✅ Synced changelog to {docs_changelog_file}")


def main():
    parser = argparse.ArgumentParser(description="Bump version in CCG project")
    parser.add_argument(
        "--type",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Type of version bump (default: patch)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
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
