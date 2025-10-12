# Quick Start

## Prerequisites

Before installing CCG, make sure you have Python 3.9 or higher installed.

!!! info "Installing pip or pipx"
    === "pipx (Recommended)"
        **pipx** installs Python CLI tools in isolated environments. Install it with:

        ```bash
        # On Ubuntu/Debian
        sudo apt install pipx
        pipx ensurepath

        # On macOS
        brew install pipx
        pipx ensurepath

        # On Windows
        python -m pip install --user pipx
        python -m pipx ensurepath

        # Using pip (any OS)
        python -m pip install --user pipx
        python -m pipx ensurepath
        ```

        After installation, restart your terminal.

    === "pip"
        **pip** comes pre-installed with Python. Verify it's available:

        ```bash
        pip --version
        # or
        python -m pip --version
        ```

        If pip is not installed, follow the [official pip installation guide](https://pip.pypa.io/en/stable/installation/).

---

## Installation

=== "pipx (Recommended)"

    ```bash
    pipx install conventional-commits-generator
    ```

=== "pip"

    ```bash
    pip install conventional-commits-generator
    ```

---

## Test CCG command

```bash
# Run CCG
ccg --version
```

That's it! CCG will guide you through an interactive prompt to create a perfect conventional commit.
