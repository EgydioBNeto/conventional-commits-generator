# Contributing to Conventional Commits Generator

Thank you for your interest in contributing to CCG! We welcome contributions from everyone, whether you're fixing a bug, adding a feature, improving documentation, or sharing ideas.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Standards](#code-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Getting Help](#getting-help)

## Getting Started

### Before You Begin

1. **Check existing issues**: Search the [issue tracker](https://github.com/EgydioBNeto/conventional-commits-generator/issues) to see if your bug or feature request already exists
2. **Create an issue**: For significant changes, create an issue first to discuss your approach
3. **Read the docs**: Familiarize yourself with the [documentation](https://egydioBNeto.github.io/conventional-commits-generator/)

### Prerequisites

- **Python 3.9+**: Required for development
- **Git**: For version control
- **pipx or pip**: For installing dependencies

## Development Setup

### Quick Setup (Recommended)

We provide an automated setup script that handles everything:

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/conventional-commits-generator.git
cd conventional-commits-generator

# Run automated setup
./scripts/setup_venv.sh

# Activate virtual environment
source .venv/bin/activate
```

The setup script will:

- Check Python version compatibility (3.9+)
- Create `.venv` virtual environment
- Upgrade pip
- Install project in development mode with all dependencies
- Verify CCG installation

### Manual Setup (Alternative)

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/conventional-commits-generator.git
cd conventional-commits-generator

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS

# Install in development mode with all dependencies
pip install -e ".[dev,test,docs]"
```

### Installing Pre-commit Hooks

We use pre-commit hooks to maintain code quality. Install them after setting up your environment:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files to verify setup
pre-commit run --all-files
```

Pre-commit hooks will automatically run on every commit and check:

- Trailing whitespace removal
- End-of-file fixer (ensures newline at end)
- TOML file validation
- No debug statements (prevents accidental commits)
- Large file prevention
- Python syntax validation
- YAML syntax validation

If hooks fail, fix the issues and try committing again. Many issues are auto-fixed by the hooks.

## Making Changes

### 1. Create a Branch

Use conventional commit naming for branches:

```bash
# For new features
git checkout -b feat/add-new-feature

# For bug fixes
git checkout -b fix/resolve-issue-123

# For documentation
git checkout -b docs/update-readme

# For refactoring
git checkout -b refactor/improve-module
```

### 2. Make Your Changes

Follow the project's code standards (see [Code Standards](#code-standards)).

**Key principles:**

- One feature/fix per branch
- Keep changes focused and atomic
- Write tests for new functionality
- Update documentation when needed

### 3. Write Tests

All new code must have tests:

```python
# tests/unit/test_new_feature.py
def test_new_feature():
    """Test description following Google style docstrings."""
    result = new_feature_function("input")
    assert result == expected_output
```

### 4. Run Tests Locally

Before pushing, ensure all tests pass:

```bash
# Quick test with current Python version
pytest

# Test across all supported versions (3.9-3.13)
./scripts/tox-mise.sh

# Test specific version
./scripts/tox-mise.sh -e py312
```

### 5. Run Code Quality Checks

Before submitting a PR, run quality checks:

```bash
# Run all quality checks at once
./scripts/tox-mise.sh -e quality

# List all available environments
./scripts/tox-mise.sh --list
```

## Testing

### Testing Across Multiple Python Versions

**We strongly recommend testing with all supported Python versions before submitting a PR.**

Use our `tox-mise.sh` script for easy multi-version testing:

```bash
# Test all Python versions (3.9-3.13)
./scripts/tox-mise.sh

# Test specific version
./scripts/tox-mise.sh -e py39
./scripts/tox-mise.sh -e py312

# Run type checking
./scripts/tox-mise.sh -e mypy
```

**First-time setup**: The script will automatically:

- Check if `mise` is installed (offers to install if missing)
- Check if `tox` is installed (offers to install if missing)
- Check if Python 3.9-3.13 are installed (offers to install missing versions)
- Provide clear instructions if auto-installation isn't possible

### Manual Testing with Tox

If you prefer to set up tox manually:

```bash
# Install tox
pip install tox

# Install Python versions with mise
mise install python@3.9
mise install python@3.10
mise install python@3.11
mise install python@3.12
mise install python@3.13

# Run tox
tox
```

### Type Checking

We enforce strict type checking with mypy:

```bash
# Run mypy type checker
mypy src/ccg

# Via tox
tox -e mypy
```

## Code Standards

### Style Guidelines

- **Type Hints**: Required for all function signatures
- **Docstrings**: [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for all public functions and classes
- **Line Length**: Maximum 100 characters
- **String Formatting**: Use f-strings
- **Imports**: Organized by standard library, third-party, local
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

### Docstring Example

```python
def validate_commit_message(message: str) -> tuple[bool, str]:
    """Validate a commit message against Conventional Commits specification.

    Args:
        message: The commit message to validate.

    Returns:
        A tuple containing:
        - bool: True if valid, False otherwise
        - str: Error message if invalid, empty string if valid

    Raises:
        ValueError: If message is None or empty.

    Examples:
        >>> validate_commit_message("feat: add new feature")
        (True, "")
        >>> validate_commit_message("invalid message")
        (False, "Invalid format")
    """
    if not message:
        raise ValueError("Message cannot be empty")
    # Implementation...
```

**Reference**: [Google Python Style Guide - Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

### Testing Standards

- **Coverage**: 100% required (enforced by pytest configuration)
- **Test Isolation**: Each test should be independent
- **Mocking**: Use `pytest-mock` for external dependencies
- **Property Testing**: Use `hypothesis` for complex validation functions
- **Test Names**: Descriptive and follow `test_<functionality>_<condition>` pattern

Example:

```python
def test_validate_commit_message_with_valid_format():
    """Test that valid conventional commit messages are accepted."""
    assert validate_commit_message("feat: add feature")[0] is True

def test_validate_commit_message_with_invalid_format():
    """Test that invalid messages are rejected with error."""
    is_valid, error = validate_commit_message("not valid")
    assert is_valid is False
    assert "Invalid format" in error
```

## Commit Guidelines

### Use CCG Itself!

The best way to create commits is to use CCG

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style/formatting (no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes

## Pull Request Process

### 1. Update Your Branch

Before creating a PR, sync with the main branch:

```bash
git checkout main
git pull upstream main
git checkout your-feature-branch
git rebase main
```

### 2. Run Full Test Suite

Ensure everything passes:

```bash
# Run tests across all Python versions
./scripts/tox-mise.sh

# Run pre-commit checks
pre-commit run --all-files

# Verify type checking
mypy src/ccg
```

### 3. Push Your Changes

```bash
git push origin your-feature-branch
```

### 4. Create Pull Request

On GitHub, create a PR with:

**Title**: Use conventional commit format

```
feat(cli): add support for custom commit templates
```

**Description**: Include:

- What changes were made
- Why these changes were needed
- How to test the changes
- Screenshots/examples (if applicable)
- Related issue numbers (e.g., "Closes #123")

**PR Template Example:**

```markdown
## Description

Brief description of changes

## Motivation

Why is this change needed?

## Changes

- Change 1
- Change 2

## Testing

- [ ] All tests pass
- [ ] Tested across Python 3.9-3.13
- [ ] Pre-commit hooks pass
- [ ] Documentation updated

## Related Issues

Closes #123
```

### 5. Respond to Review Feedback

- Be open to feedback and suggestions
- Make requested changes promptly
- Push additional commits to the same branch
- Request re-review after addressing feedback

## Getting Help

### Resources

- **Issue Tracker**: [GitHub Issues](https://github.com/EgydioBNeto/conventional-commits-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/EgydioBNeto/conventional-commits-generator/discussions)

### Questions?

- **Bug Reports**: Use the bug report template in issues
- **Feature Requests**: Use the feature request template
- **Questions**: Create an issue with the "question" label
- **Email**: egydiobolonhezi@gmail.com

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code. Please report unacceptable behavior to egydiobolonhezi@gmail.com.

## License

By contributing, you agree that your contributions will be licensed under the same [MIT License](../LICENSE) that covers this project.
