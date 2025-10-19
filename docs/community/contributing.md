# Contributing Guide

Thank you for your interest in contributing to CCG! This guide will help you get started.

---

## Quick Start

1. **Fork and clone** the repository
2. **Set up environment**: `./scripts/setup_venv.sh`
3. **Install pre-commit**: `pre-commit install`
4. **Create branch**: `git checkout -b feat/my-feature`
5. **Make changes** and add tests
6. **Test across versions**: `./scripts/tox-mise.sh`
7. **Commit and Push with CCG**: `ccg`

---

## Development Setup

### Automated Setup (Recommended)

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/conventional-commits-generator.git
cd conventional-commits-generator

# Run automated setup
./scripts/setup_venv.sh

# Activate environment
source .venv/bin/activate
```

### Install Pre-commit Hooks

Pre-commit hooks ensure code quality before commits:

```bash
# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

The hooks will check for:

- Trailing whitespace
- File endings
- TOML/YAML syntax
- Debug statements
- Large files

---

## Development Workflow

### 1. Make Changes

```bash
# Create feature branch
git checkout -b feat/new-feature

# Edit code
vim src/ccg/module.py

# Add tests
vim tests/unit/test_module.py
```

### 2. Run Tests

```bash
# Quick test with current Python version
pytest

# Test across all supported versions (3.9-3.13)
./scripts/tox-mise.sh

# Test specific version
./scripts/tox-mise.sh -e py312
```

### 3. Create Commit

Use CCG to create conventional commits:

```bash
# Commit and Push with CCG
ccg

# Follow the interactive prompts
```

### 4. Submit PR

```bash
# Create PR on GitHub
# Use conventional commit format in PR title
# Example: "feat(cli): add verbose output flag"
```

---

## Code Standards

### Style Guidelines

- **Type Hints**: Required for all functions
- **Docstrings**: [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for public functions
- **Line Length**: Maximum 100 characters
- **Formatting**: Use f-strings for string formatting
- **Coverage**: 100% test coverage required

### Docstring Example

```python
def validate_commit_message(message: str) -> tuple[bool, str]:
    """Validate a commit message against Conventional Commits specification.

    Args:
        message: The commit message to validate.

    Returns:
        A tuple containing validation status and error message:
        - bool: True if valid, False otherwise
        - str: Error message if invalid, empty string if valid

    Examples:
        >>> validate_commit_message("feat: add feature")
        (True, "")
        >>> validate_commit_message("invalid")
        (False, "Invalid format")
    """
    # Implementation...
```

**Learn more**: [Google Python Style Guide - Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

---

## Testing Requirements

### Coverage

All code must maintain 100% test coverage:

```bash
# Run tests with coverage
pytest

# View coverage report
pytest --cov-report=html
```

### Multi-version Testing

Test across all supported Python versions:

```bash
# Test all versions
./scripts/tox-mise.sh

# The script handles:
# - mise installation (if needed)
# - tox installation (if needed)
# - Python 3.9-3.13 installation (if needed)
# - Running tests across all versions
```

### Type Checking

```bash
# Run mypy type checker
mypy src/ccg

# Or via tox
./scripts/tox-mise.sh -e mypy
```

---

## Pull Request Process

### Before Submitting

1. **Run full test suite**:

   ```bash
   ./scripts/tox-mise.sh
   pre-commit run --all-files
   mypy src/ccg
   ```

2. **Update documentation** if needed

3. **Ensure 100% coverage** maintained

### PR Guidelines

**Title**: Use conventional commit format

```
feat(cli): add support for custom templates
```

**Description**: Include:

- What changed
- Why it changed
- How to test
- Related issues

**Checklist**:

- [ ] Tests pass across Python 3.9-3.13
- [ ] Pre-commit hooks pass
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] 100% coverage maintained

---

## Project Structure

```
src/ccg/
├── __init__.py      # Version and exports
├── cli.py           # CLI interface and orchestration
├── core.py          # Commit generation logic
├── git.py           # Git operations
├── utils.py         # UI utilities and formatting
└── config.py        # Configuration

tests/               # tests (100% coverage)
scripts/             # Development scripts
docs/                # MkDocs documentation
```

---

## Getting Help

### Resources

- [Full Contributing Guide](https://github.com/EgydioBNeto/conventional-commits-generator/blob/main/.github/CONTRIBUTING.md)
- [Documentation](https://egydioBNeto.github.io/conventional-commits-generator/)
- [Issue Tracker](https://github.com/EgydioBNeto/conventional-commits-generator/issues)

### Questions?

- **Bug Reports**: Use bug report template
- **Feature Requests**: Use feature request template
- **Questions**: Create issue with "question" label
- **Email**: egydiobolonhezi@gmail.com

---

## Code of Conduct

This project follows our [Code of Conduct](code-of-conduct.md). Be respectful and inclusive.
