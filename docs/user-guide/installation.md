# Installation Guide

This guide will walk you through the different ways to install **Conventional Commits Generator (CCG)**.

---

## Requirements

Before installing CCG, make sure you have:

- **Python 3.9 or higher**
- **Git** (required for git operations)
- **pip** or **pipx** (Python package installers)

### Checking Your Python Version

```bash
python3 --version
# or
python --version
```

If you don't have Python 3.9+, download it from [python.org](https://www.python.org/downloads/).

---

## Installation Methods

### Method 1: pipx (Recommended)

!!! success "Why pipx?"
    pipx installs Python CLI applications in isolated environments, preventing dependency conflicts and making it easy to manage and update tools.

#### Install pipx

=== "Linux"

    ```bash
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    ```

=== "macOS"

    ```bash
    brew install pipx
    pipx ensurepath
    ```

=== "Windows"

    ```powershell
    python -m pip install --user pipx
    python -m pipx ensurepath
    ```

#### Install CCG with pipx

```bash
pipx install conventional-commits-generator
```

#### Verify Installation

```bash
ccg --version
```

---

### Method 2: pip

!!! warning "Global Installation"
Installing with pip globally may cause dependency conflicts with other Python packages. Consider using a virtual environment or pipx instead.

```bash
pip install conventional-commits-generator
```

#### Using a Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv ccg-env

# Activate virtual environment
source ccg-env/bin/activate

# Install CCG
pip install conventional-commits-generator

# Verify installation
ccg --version
```

---

#### Manual Setup (Alternative)

```bash
# Clone the repository
git clone https://github.com/EgydioBNeto/conventional-commits-generator.git
cd conventional-commits-generator

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install in development mode
pip install -e .

# Install with all dependencies (dev + test + docs)
pip install -e ".[dev,test,docs]"
```

---

## Verifying Installation

After installation, verify that CCG is working correctly:

```bash
# Check version
ccg --version

# Display help
ccg --help

# Test in a git repository
cd /path/to/your/git/repo
ccg --commit
```

You should see the CCG ASCII logo and interactive prompts.

---

## Updating CCG

### pipx

```bash
pipx upgrade conventional-commits-generator
```

### pip

```bash
pip install --upgrade conventional-commits-generator
```

---

## Uninstalling CCG

### pipx

```bash
pipx uninstall conventional-commits-generator
```

### pip

```bash
pip uninstall conventional-commits-generator
```

---

## Troubleshooting

### Command not found: ccg

**Problem**: After installation, running `ccg` shows "command not found"

**Solutions**:

1. **Check if the installation directory is in your PATH**:

   ```bash
   # For pipx
   pipx ensurepath

   # For pip (user install)
   export PATH="$HOME/.local/bin:$PATH"  # Add to ~/.bashrc or ~/.zshrc
   ```

2. **Try running with python -m**:

   ```bash
   python -m ccg.cli
   ```

3. **Reinstall with correct method**:

   ```bash
   pipx install conventional-commits-generator
   ```

---

### Permission Denied

**Problem**: Installation fails with permission errors

**Solutions**:

1. **Use user installation** (recommended):

   ```bash
   pip install --user conventional-commits-generator
   ```

2. **Use pipx** (recommended):

   ```bash
   pipx install conventional-commits-generator
   ```

3. **Avoid sudo pip** (not recommended):

   Using `sudo pip` can break your system Python packages.

---

### Dependency Conflicts

**Problem**: Conflicts with `prompt_toolkit` or other dependencies

**Solutions**:

1. **Use pipx** (installs in isolated environment):

   ```bash
   pipx install conventional-commits-generator
   ```

2. **Use virtual environment**:

   ```bash
   python3 -m venv ccg-env
   source ccg-env/bin/activate
   pip install conventional-commits-generator
   ```

---

### Python Version Mismatch

**Problem**: Your Python version is below 3.9

**Solutions**:

1. **Install Python 3.9+** from [python.org](https://www.python.org/downloads/)

2. **Use version managers**:

=== "mise"

    ```bash
    mise install python@3.12
    mise global python@3.12
    ```

=== "pyenv"

    ```bash
    pyenv install 3.12
    pyenv global 3.12
    ```
---

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'ccg'`

**Solutions**:

1. **Ensure installation completed**:

2. **Check if you're in the correct virtual environment**:

   ```bash
   which python
   which ccg
   ```

3. **Reinstall**:

   ```bash
   pip uninstall conventional-commits-generator
   pipx install conventional-commits-generator
   ```

---

## Need Help?

- Check our [FAQ](faq.md)
- Report issues on [GitHub](https://github.com/EgydioBNeto/conventional-commits-generator/issues)
- Read the [Usage Guide](usage.md) for detailed command documentation
