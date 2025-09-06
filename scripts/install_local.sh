#!/bin/bash
# Local installation script for Conventional Commits Generator

set -e

echo "🚀 Installing Conventional Commits Generator locally..."
echo

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root directory."
    exit 1
fi

# Check if pipx is available
if command -v pipx &> /dev/null; then
    echo "📦 Installing with pipx (recommended)..."

    # Try installing with pipx
    if pipx install . --force; then
        echo "✅ Successfully installed with pipx!"
        echo
        echo "🎉 CCG is now available globally as 'ccg'"
        echo "   Try: ccg --version"
        exit 0
    else
        echo "⚠️  pipx installation failed, trying alternative method..."
    fi
fi

# Check if pip is available
if command -v pip3 &> /dev/null; then
    echo "📦 Installing with pip (user mode)..."

    # Try installing with pip user mode
    if pip3 install . --user --force-reinstall; then
        echo "✅ Successfully installed with pip!"
        echo
        echo "🎉 CCG is now available globally as 'ccg'"
        echo "   Try: ccg --version"
        echo
        echo "💡 If 'ccg' command is not found, add ~/.local/bin to your PATH:"
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
        exit 0
    else
        echo "⚠️  pip user installation failed, trying with --break-system-packages..."

        if pip3 install . --user --force-reinstall --break-system-packages; then
            echo "✅ Successfully installed with pip (system packages override)!"
            echo
            echo "🎉 CCG is now available globally as 'ccg'"
            echo "   Try: ccg --version"
            exit 0
        fi
    fi
fi

# If all else fails, suggest development mode
echo "❌ Standard installation methods failed."
echo
echo "🔧 You can try development mode installation:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -e ."
echo "   # Then use: ./venv/bin/ccg"
echo
echo "📚 Or check the README.md for more installation options."
exit 1
