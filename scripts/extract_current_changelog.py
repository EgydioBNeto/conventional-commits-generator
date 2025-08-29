#!/usr/bin/env python3
"""
Script to extract only the changelog section of the current version.
Used to create the release body on GitHub.
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def get_current_version() -> str:
    """Get current version from __init__.py."""
    init_file = Path("src/ccg/__init__.py")

    if not init_file.exists():
        return "0.0.0"

    content = init_file.read_text()
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)

    return match.group(1) if match else "0.0.0"


def get_repository_name() -> str:
    """Get repository name from git remote or environment variables."""
    github_repo = os.environ.get("GITHUB_REPOSITORY")
    if github_repo:
        return github_repo

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True
        )
        remote_url = result.stdout.strip()

        if "github.com" in remote_url:
            if remote_url.startswith("git@github.com:"):
                repo_part = remote_url.split("git@github.com:")[1]
            elif "github.com/" in remote_url:
                repo_part = remote_url.split("github.com/")[1]
            else:
                return "EgydioBNeto/conventional-commits-generator"

            if repo_part.endswith(".git"):
                repo_part = repo_part[:-4]

            return repo_part
    except subprocess.CalledProcessError:
        pass

    return "EgydioBNeto/conventional-commits-generator"


def extract_current_version_changelog(changelog_content: str, version: str) -> str:
    """Extract changelog section for current version."""
    version_pattern = rf"## \[{re.escape(version)}\].*?(?=## \[|\Z)"

    match = re.search(version_pattern, changelog_content, re.DOTALL)

    repo_name = get_repository_name()

    if not match:
        return f"""## What's Changed in v{version}

This release includes various improvements and fixes.

### Installation

```bash
pip install --upgrade conventional-commits-generator
```

**Full Changelog**: https://github.com/{repo_name}/compare/{get_previous_version_tag()}...v{version}
"""

    section = match.group(0)
    lines = section.split("\n")

    content_start = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith("## ["):
            content_start = i
            break

    content_lines = lines[content_start:]

    while content_lines and not content_lines[-1].strip():
        content_lines.pop()

    content = "\n".join(content_lines).strip()
    if content:
        meaningful_content = content and not (
            content == f"Version {version} release"
            or "Version " in content
            and " release" in content
            and len(content) < 30
        )

        if meaningful_content:
            enhanced_content = f"""## What's Changed in v{version}

{content}

### Installation

```bash
pip install --upgrade conventional-commits-generator
```

**Full Changelog**: https://github.com/{repo_name}/compare/{get_previous_version_tag()}...v{version}
"""
        else:
            enhanced_content = f"""## What's Changed in v{version}

This release includes various improvements and bug fixes.

### Installation

```bash
pip install --upgrade conventional-commits-generator
```

### Verification

```bash
ccg --version
```

**Full Changelog**: https://github.com/{repo_name}/compare/{get_previous_version_tag()}...v{version}
"""
    else:
        enhanced_content = f"""## What's Changed in v{version}

This release includes various improvements and bug fixes.

### Installation

```bash
pip install --upgrade conventional-commits-generator
```

**Full Changelog**: https://github.com/{repo_name}/compare/{get_previous_version_tag()}...v{version}
"""

    return enhanced_content


def get_previous_version_tag() -> str:
    """Get previous version tag for comparison link."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-version:refname", "-l", "v*"],
            capture_output=True,
            text=True,
            check=True,
        )

        tags = result.stdout.strip().split("\n")
        tags = [tag for tag in tags if tag.strip()]

        if len(tags) >= 2:
            return tags[1]
        elif len(tags) == 1:
            try:
                first_commit = subprocess.run(
                    ["git", "rev-list", "--max-parents=0", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                return first_commit[:7] if first_commit else tags[0]
            except subprocess.CalledProcessError:
                return tags[0]
        else:
            try:
                first_commit = subprocess.run(
                    ["git", "rev-list", "--max-parents=0", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                return first_commit[:7] if first_commit else "HEAD"
            except subprocess.CalledProcessError:
                return "HEAD"

    except subprocess.CalledProcessError:
        return "HEAD"


def get_previous_version(changelog_content: str) -> str:
    """Get previous version from changelog for fallback."""
    version_matches = re.findall(r"## \[(\d+\.\d+\.\d+)\]", changelog_content)

    if len(version_matches) >= 2:
        return version_matches[1]
    elif len(version_matches) == 1:
        current = version_matches[0]
        parts = current.split(".")
        if parts[-1] != "0":
            parts[-1] = str(int(parts[-1]) - 1)
        elif parts[1] != "0":
            parts[1] = str(int(parts[1]) - 1)
            parts[2] = "0"
        elif parts[0] != "0":
            parts[0] = str(int(parts[0]) - 1)
            parts[1] = "0"
            parts[2] = "0"

        return ".".join(parts)
    else:
        return "0.0.0"


def main():
    """Extract and output current version changelog."""
    try:
        current_version = get_current_version()
        repo_name = get_repository_name()

        changelog_file = Path("CHANGELOG.md")

        if not changelog_file.exists():
            print(
                f"""## What's Changed in v{current_version}

This is an automated release of the Conventional Commits Generator.

### Features
- Interactive CLI for creating conventional commits
- Support for commit types, scopes, and breaking changes
- Automated emoji integration
- Git workflow automation

### Installation

```bash
pip install conventional-commits-generator
```

### Usage

```bash
ccg
```

**Full Changelog**: https://github.com/{repo_name}/releases/tag/v{current_version}
"""
            )
            return

        changelog_content = changelog_file.read_text()

        current_changelog = extract_current_version_changelog(changelog_content, current_version)

        print(current_changelog)

    except Exception as e:
        print(f"Error extracting changelog: {e}", file=sys.stderr)

        current_version = get_current_version()
        repo_name = get_repository_name()

        print(
            f"""## What's Changed in v{current_version}

This release includes various improvements and bug fixes.

### Installation

```bash
pip install --upgrade conventional-commits-generator
```

### Verification

```bash
ccg --version
```

**Full Changelog**: https://github.com/{repo_name}/compare/HEAD...v{current_version}
"""
        )


if __name__ == "__main__":
    main()
