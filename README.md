# Conventional Commits Generator

<div align="center">
<img src="https://github.com/EgydioBNeto/conventional-commits-generator/assets/84047984/53f38934-16bb-40f6-aff7-a5800c4bd706" width="300px"/>
</div>

## Description

A simple yet powerful interactive CLI tool for creating well-structured and standardized commit messages following the [conventional commit format](https://www.conventionalcommits.org/).

## Overview

```
$ ccg

┌────────────────────────────────────────────────────────────────────────────────┐
│                                 Commit Types                                   │
└────────────────────────────────────────────────────────────────────────────────┘

1. ★ feat       - A new feature for the user or a particular enhancement
2. ♥ fix        - A bug fix for the user or a particular issue
3. • chore      - Routine tasks, maintenance, or minor updates
...

┌──────────────────────┐
│ Scope                │
└──────────────────────┘

ℹ The scope provides context for the commit (e.g., module or file name)
ℹ Examples: auth, ui, api, database
Enter the scope (optional, press Enter to skip): authentication

✓ Scope set to: authentication

┌──────────────────────┐
│ Breaking Change      │
└──────────────────────┘

ℹ A breaking change means this commit includes incompatible changes
ℹ Examples: changing function signatures, removing features, etc.
Is this a BREAKING CHANGE? (y/n): n

ℹ Not a breaking change

┌──────────────────────┐
│ Commit Message       │
└──────────────────────┘

ℹ Provide a clear, concise description of the change
ℹ Examples: 'implement OAuth login', 'fix navigation bug', 'update documentation'
Enter the commit message: implement OAuth login

✓ Message: implement OAuth login

┌──────────────────────┐
│ Review               │
└──────────────────────┘

┌────────────────────────────────────────────────┐
│                                                │
│  feat(authentication): implement OAuth login   │
│                                                │
└────────────────────────────────────────────────┘

Confirm this commit message? (y/n): y

✓ Commit message confirmed!

┌──────────────────────┐
│ Commit               │
└──────────────────────┘

→ Committing changes...
✓ New commit successfully created!

┌──────────────────────┐
│ Push Changes         │
└──────────────────────┘

ℹ This will execute 'git push' command
Do you want to push these changes? (y/n): y

┌──────────────────────┐
│ Remote Push          │
└──────────────────────┘

→ Pushing changes to remote repository...
✓ Changes pushed successfully!
```

## Features

- Interactive CLI with colored output and user-friendly prompts
- Complete conventional commit format support:
  - Type selection with detailed descriptions
  - Optional scope field
  - Breaking change indicator
  - Descriptive commit message
- Git integration:
  - Automatic `git add` to stage changes
  - Commit with formatted message
  - Optional push to remote
- Advanced features:
  - Pre-commit hooks integration
  - Push-only mode
  - Dry-run mode for testing
  - Command history for easier input

## Installation

### Using pipx (recommended)

[pipx](https://pypa.github.io/pipx/) is the recommended way to install command-line tools written in Python:

```bash
# Install pipx if you don't have it
pip install --user pipx
pipx ensurepath

# Install ccg
pipx install ccg
```

### Using pip

```bash
pip install ccg
```

### Development Installation

Clone the repository:
```bash
git clone https://github.com/EgydioBNeto/conventional-commits-generator.git
cd conventional-commits-generator
```

#### Using a Virtual Environment (Recommended)

On Linux/macOS:
```bash
# Run the setup script
chmod +x scripts/setup_venv.sh
./scripts/setup_venv.sh

# Activate the virtual environment
source .venv/bin/activate
```

On Windows:
```bash
# Run the setup script
scripts\setup_venv.bat

# Activate the virtual environment
.venv\Scripts\activate
```

#### Manual Installation
```bash
# Create a virtual environment
python -m venv .venv

# Activate it (Linux/macOS)
source .venv/bin/activate
# Or on Windows
# .venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Usage

### Basic Usage

```bash
# Generate a commit interactively
ccg

# Just push without creating a new commit
ccg --push

# Generate a commit message without actually committing (dry run)
ccg --dry-run

# Show version
ccg --version
```

## Requirements

- Python 3.7+
- Git

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for details on how to contribute to this project.

## Code of Conduct

Please read the [Code of Conduct](.github/CODE_OF_CONDUCT.md) for details on our code of conduct.

## Security

For details about reporting security vulnerabilities, see [SECURITY.md](.github/SECURITY.md).

## License

This project is licensed under the [MIT License](LICENSE).

## Author

[EgydioBNeto](https://github.com/EgydioBNeto)
