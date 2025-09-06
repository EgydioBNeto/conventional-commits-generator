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
Make sure your changes don't break the project

### 6. Commit Changes
Use CCG itself to create standardized commits:
```bash
ccg
```

You can also commit a specific file or folder:
```bash
ccg --add src/file1.py
```

Or run CCG in a different directory:
```bash
ccg --dir /path/to/repository
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
├── __init__.py           # Main entry point and exports
├── __main__.py           # Module execution entry point
├── _version.py           # Version information
├── cli.py                # Command line interface
│
├── core/                 # 🎯 Core business logic
│   ├── __init__.py
│   ├── interactive.py    # Interactive commit generation
│   ├── operations.py     # Commit operations (edit/diff)
│   └── workflows.py      # CLI workflows and handlers
│
├── git/                  # 🔧 Git operations
│   ├── __init__.py
│   └── operations.py     # Git commands and repository management
│
├── ui/                   # 🖥️ User interface
│   ├── __init__.py
│   ├── display.py        # Output formatting and display
│   ├── input.py          # Interactive input handling
│   └── validation.py     # Input validation
│
├── common/               # 📦 Shared utilities
│   ├── __init__.py
│   ├── config.py         # Configuration constants
│   ├── decorators.py     # Utility decorators
│   └── helpers.py        # Helper functions
│
scripts/
├── bump_version.py            # Version management script
├── extract_current_changelog.py  # Changelog extraction
└── generate_changelog.py     # Changelog generation
```

### Code Conventions
- Use type hints whenever possible
- Docstrings for public functions
- Descriptive names for variables and functions
- Maximum 100 characters per line
- Use f-strings for string formatting
- Avoid bare `except:` clauses - use `except Exception:` instead
- Import organization: external imports first, then internal imports
- No print() statements in production code - use utility functions from utils.py

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
