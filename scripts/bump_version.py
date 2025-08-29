#!/usr/bin/env python3
"""
Script to automatically bump the CCG version.
Updates the necessary files with the new version.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple


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


def update_changelog_placeholder(new_version: str) -> None:
    """Update changelog with new version placeholder."""
    changelog_file = Path("CHANGELOG.md")

    if not changelog_file.exists():
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{new_version}] - {get_current_date()}

### Added
- Automatic version bumping and release process

### Changed
- Improved CI/CD pipeline with automated PyPI deployment

### Fixed
- Version consistency across all project files
"""
    else:
        content = changelog_file.read_text()

        unreleased_section = "## [Unreleased]"
        new_section = f"""## [Unreleased]

## [{new_version}] - {get_current_date()}

### Added
- Version {new_version} release

### Changed

### Fixed
"""

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
                lines.insert(header_end, f"\n## [{new_version}] - {get_current_date()}")
                lines.insert(header_end + 1, "\n### Added")
                lines.insert(header_end + 2, f"- Version {new_version} release\n")

            updated_content = "\n".join(lines)

        changelog_content = updated_content

    changelog_file.write_text(changelog_content)
    print(f"✅ Updated {changelog_file} with version {new_version}")


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d")


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
            return

        print("\n📝 Updating files...")
        update_init_file(new_version)
        update_pyproject_toml(new_version)
        update_security_md(new_version)
        update_changelog_placeholder(new_version)

        print(f"\n🎉 Successfully bumped version to {new_version}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
