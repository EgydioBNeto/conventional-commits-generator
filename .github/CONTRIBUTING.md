# Contributing to the Project

Thank you for considering contributing to this project! We encourage participation from everyone.

## How to Contribute

### 1. Create an Issue

Before starting work on a new feature or fix, create an issue for discussion and feedback.

### 2. Fork the Repository

Fork the repository to your account.

### 3. Create a Branch

Create a branch for your contribution:

```bash
git checkout -b feature/new-feature
```

### 4. Make Changes

Implement the desired changes following existing coding conventions.

### 5. Test Your Changes

Run the test suite to ensure your changes don't break existing functionality:

```bash
# Run tests with your current Python version
pytest

# Test across all supported Python versions (3.9-3.13)
# The script automatically checks dependencies and helps install missing ones
./scripts/tox-mise.sh

# Test specific Python version
./scripts/tox-mise.sh -e py39

# Test in parallel (faster)
./scripts/tox-mise.sh -p auto
```

The `tox-mise.sh` script will:
- ✓ Check if mise is installed (offers to install if missing)
- ✓ Check if tox is installed (offers to install if missing)
- ✓ Check if Python 3.9-3.13 are installed (offers to install missing versions)
- ✓ Provide clear instructions if auto-installation fails

Make sure all tests pass across all Python versions.

### 6. Commit Changes

Use CCG itself to create standardized commits:

```bash
ccg
```

### 7. Push to Your Fork

```bash
git push origin feature/new-feature
```

### 8. Create Pull Request

Create a PR to the main branch of this repository.

### 9. Await Review

Be willing to make adjustments as requested.

## Development Standards

### Project Structure

```
src/ccg/
├── __init__.py      # Version and exports
├── cli.py          # Command line interface
├── core.py         # Core logic
├── config.py       # Configuration dataclasses
├── git.py          # Git operations
└── utils.py        # Utilities and formatting

tests/
├── unit/           # Unit tests
├── conftest.py     # Pytest fixtures
└── __init__.py
```

### Code Conventions

- Use type hints whenever possible (enforced by mypy strict mode)
- Docstrings for public functions (Google-style)
- Descriptive names for variables and functions
- Maximum 100 characters per line
- Use f-strings for string formatting

### Testing Requirements

- Minimum code coverage (see `pytest.ini`)
- All tests must pass on Python 3.9-3.13
- Use `pytest-mock` for mocking git operations
- Mock user input via `prompt_toolkit.prompt`
- Run `tox` before submitting PRs to verify multi-version compatibility

### Pre-commit Hooks

The project uses pre-commit to ensure quality:

- `trailing-whitespace`: Remove trailing whitespace
- `end-of-file-fixer`: Ensure newline at end of files
- `check-toml`: Validate TOML files
- `debug-statements`: Remove debug statements
- `check-added-large-files`: Prevent large files

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, all contributors and maintainers are expected to uphold this code.

## Need Help?

If you need assistance:

- Create an issue with the "question" tag
- Contact us: egydiobolonhezi@gmail.com

Thank you for your interest in contributing! 🚀
