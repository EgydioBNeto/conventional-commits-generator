# Conventional Commits Generator

<div align="center">
<img src="https://github.com/EgydioBNeto/conventional-commits-generator/assets/84047984/53f38934-16bb-40f6-aff7-a5800c4bd706" width="300px"/>
</div>

## Description

Interactive CLI tool for creating standardized commit messages following the [conventional commits](https://www.conventionalcommits.org/) format. Includes support for commit body, emojis, and advanced commit management features.

## Installation

### Using pipx (recommended)
```bash
pipx install conventional-commits-generator
```

### Using pip
```bash
pip install conventional-commits-generator
```

### Development installation
```bash
# Clone the GitHub repository
git clone https://github.com/EgydioBNeto/conventional-commits-generator.git

# Navigate into the project directory
cd conventional-commits-generator

# Grant execute permission to the virtual environment setup script
chmod +x scripts/setup_venv.sh

# Run the script to create and set up the virtual environment
./scripts/setup_venv.sh

# Activate the virtual environment
source .venv/bin/activate
```

## Usage

### Basic commands

```bash
# Create interactive commit
ccg

# Generate commit message without committing
ccg --commit

# Push only without creating commit
ccg --push

# Edit existing commit
ccg --edit

# Delete existing commit
ccg --delete

# Create and push tag
ccg --tag

# Reset local and pull from remote
ccg --reset

# Show version
ccg --version
```

### Interactive usage example

```
$ ccg

 ________      ________      ________
|\   ____\    |\   ____\    |\   ____\
\ \  \___|    \ \  \___|    \ \  \___|
 \ \  \        \ \  \        \ \  \  ___
  \ \  \____    \ \  \____    \ \  \|\  \
   \ \_______\   \ \_______\   \ \_______\
    \|_______|    \|_______|    \|_______|

 Conventional Commits Generator

┌──────────────────────┐
│ Commit Types         │
└──────────────────────┘

1. ✨ feat     - A new feature
2. 🐛 fix      - A bug fix
3. 🔧 chore    - Maintenance tasks
4. ♻️ refactor - Code refactoring
5. 💄 style    - Style changes
6. 📚 docs     - Documentation
...

Choose the commit type: 1

┌──────────────────────┐
│ Scope                │
└──────────────────────┘
Enter the scope (optional): auth

┌──────────────────────┐
│ Breaking Change      │
└──────────────────────┘
Is this a BREAKING CHANGE? (y/N): n

┌──────────────────────┐
│ Emoji                │
└──────────────────────┘
Include emoji in commit message? (Y/n): n

┌──────────────────────┐
│ Commit Message       │
└──────────────────────┘
Enter the commit message: implement OAuth login

┌──────────────────────┐
│ Commit Body          │
└──────────────────────┘
Commit body (optional): Added Google OAuth 2.0 support
Integration with existing user system

┌──────────────────────┐
│ Review               │
└──────────────────────┘
Commit: feat(auth): implement OAuth login

Body:
Added Google OAuth 2.0 support
Integration with existing user system

Confirm this commit message? (Y/n): y
✓ Commit message confirmed!

┌──────────────────────┐
│ Push Changes         │
└──────────────────────┘
Do you want to push these changes? (Y/n): y
✓ Changes pushed successfully!
```

## Commit Types

| Type | Emoji | Description |
|------|-------|-------------|
| `feat` | ✨ | A new feature |
| `fix` | 🐛 | A bug fix |
| `chore` | 🔧 | Maintenance tasks |
| `refactor` | ♻️ | Code refactoring |
| `style` | 💄 | Style/formatting changes |
| `docs` | 📚 | Documentation changes |
| `test` | 🧪 | Adding or modifying tests |
| `build` | 📦 | Build system changes |
| `revert` | ⏪ | Reverts a previous commit |
| `ci` | 👷 | CI/CD changes |
| `perf` | ⚡ | Performance improvements |

## Requirements

- Python 3.8+
- Git

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for details on how to contribute.

## Code of Conduct

Please read our [Code of Conduct](.github/CODE_OF_CONDUCT.md) for details on our community standards.

## Security

To report security vulnerabilities, see [SECURITY.md](.github/SECURITY.md).

## License

This project is licensed under the [MIT License](LICENSE).

## Author

[EgydioBNeto](https://github.com/EgydioBNeto)
