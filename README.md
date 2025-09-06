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

# Option 1: Use the automated installer (recommended)
chmod +x scripts/install_local.sh
./scripts/install_local.sh

# Option 2: Manual virtual environment setup
chmod +x scripts/setup_venv.sh
./scripts/setup_venv.sh
source .venv/bin/activate

# Option 3: Direct local installation
pipx install . --force
# or
pip install . --user
```

## Usage

### Basic commands

```bash
# Create interactive commit
ccg

# Generate and preview commit message without committing
ccg --commit

# Push committed changes to remote without creating new commit
ccg --push

# Fetch and pull latest changes from remote repository
ccg --pull

# Edit existing commit message (recent or by hash)
ccg --edit

# Compare two commits and show detailed differences
ccg --diff

# Show detailed working directory status
ccg --status

# Create annotated or lightweight Git tag and push to remote
ccg --tag

# Discard all local changes, reset to HEAD, and pull from remote
ccg --reset

# Run CCG in a specific directory
ccg --dir /path/to/repository

# Add specific file or directory to staging before committing
ccg --add file.py
ccg --add src/

# Combine options for complex workflows
ccg --commit --add src/main.py
ccg --dir /path/to/repo --add docs/

# Show version information
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
4. 🔨 refactor - Code refactoring
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
Is this a BREAKING CHANGE? (y/n): n

┌──────────────────────┐
│ Emoji                │
└──────────────────────┘
Include emoji in commit message? (y/n): n

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

┌─────────────────────────────────────────────────────────┐
│                                                         │
│  feat(auth): implement OAuth login                      │
│                                                         │
│  Added Google OAuth 2.0 support                         │
│  Integration with existing user system                  │
│                                                         │
└─────────────────────────────────────────────────────────┘

Confirm this commit message? (y/n): y
✓ New commit successfully created!

Do you want to push these changes? (y/n): y
✓ Changes pushed successfully!
```

## Commit Types

| Type | Emoji | Description |
|------|-------|-------------|
| `feat` | ✨ | A new feature |
| `fix` | 🐛 | A bug fix |
| `chore` | 🔧 | Maintenance tasks |
| `refactor` | 🔨 | Code refactoring |
| `style` | 💄 | Style/formatting changes |
| `docs` | 📚 | Documentation changes |
| `test` | 🧪 | Adding or modifying tests |
| `build` | 📦 | Build system changes |
| `revert` | ⏪ | Reverts a previous commit |
| `ci` | 👷 | CI/CD changes |
| `perf` | ⚡ | Performance improvements |

## Advanced Features

### Repository Management

- **Directory Support**: Use `--dir` to run CCG in any git repository without changing your current directory
- **File/Folder Selection**: Use `--add` to stage and commit one specific file or folder (path must be within the working directory)
- **Status Checking**: Use `--status` to view detailed working directory status
- **Remote Operations**: Pull changes with `--pull`, reset with `--reset`

### Commit Operations

- **Commit Editing**: Edit any commit message with `--edit` (supports both recent and historical commits)
- **Interactive Diff**: Compare commits with `--diff` for detailed change analysis

### Tag Management

- **Tag Creation**: Create annotated or lightweight tags with `--tag`
- **Automatic Push**: Tags are automatically pushed to remote repository
- **Message Support**: Add custom messages to annotated tags

### Interactive Features

- **Multi-line Support**: Full support for commit body with multi-line input
- **History**: Command history for faster input (type, scope, message, body)
- **Visual Feedback**: Real-time character count and validation
- **Smart Validation**: Conventional commit format validation

## Requirements

- Python 3.8+ (recommended: Python 3.10+)
- Git 2.0+
- Terminal with Unicode support (for emojis and symbols)

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
