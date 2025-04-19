# Conventional Commits Generator

<div align="center">
<img src="https://github.com/EgydioBNeto/conventional-commits-generator/assets/84047984/53f38934-16bb-40f6-aff7-a5800c4bd706" width="300px"/>
</div>

## Description

A simple yet powerful interactive CLI tool for creating well-structured and standardized commit messages following the [conventional commit format](https://www.conventionalcommits.org/).

## Overview

```
$ ccg

1. feat       - A new feature for the user or a particular enhancement
2. fix        - A bug fix for the user or a particular issue
3. chore      - Routine tasks, maintenance, or minor updates
...

Choose the commit type: feat

Enter the scope (optional): authentication

Is this a BREAKING CHANGE? (y/n): n

Enter the commit message: implement OAuth login

Commit message:
feat(authentication): implement OAuth login

Confirm this commit? (y/n): y

New commit successfully made.

Do you want to push these changes? (y/n): y

Changes pushed.
```

## Features

- Interactive CLI for creating conventional commits
- Supports git add, commit, and push operations
- Pre-commit hooks integration
- Type checking with mypy
- Linting with pylint

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
# Generate a commit
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

## License

This project is licensed under the [MIT License](LICENSE).

## Author

[EgydioBNeto](https://github.com/EgydioBNeto)
