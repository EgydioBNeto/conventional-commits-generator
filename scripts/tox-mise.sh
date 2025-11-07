#!/usr/bin/env bash
# Wrapper script to run tox with mise-installed Python versions
#
# This script verifies all dependencies and helps developers install what's missing.
#
# Usage:
#   ./scripts/tox-mise.sh                  # Run all tests (py39-py313, mypy, quality)
#   ./scripts/tox-mise.sh -e py39          # Run Python 3.9 tests only
#   ./scripts/tox-mise.sh -e mypy          # Run type checking only
#   ./scripts/tox-mise.sh -e quality       # Run all code quality checks
#   ./scripts/tox-mise.sh -e radon-cc      # Run complexity analysis only
#   ./scripts/tox-mise.sh -e bandit        # Run security scan only
#   ./scripts/tox-mise.sh --list           # List all available environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Required Python versions
REQUIRED_VERSIONS=("3.9" "3.10" "3.11" "3.12" "3.13")

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check mise installation
check_mise() {
    print_section "Checking mise installation"

    if command_exists mise; then
        print_success "mise is installed ($(mise --version))"
        return 0
    else
        print_error "mise is not installed"
        echo ""
        print_info "mise is a tool for managing multiple runtime versions (like Python)"
        print_info "Install it with one of these methods:"
        echo ""
        echo "  # Using curl:"
        echo "  curl https://mise.run | sh"
        echo ""
        echo "  # Or using your package manager:"
        echo "  # Arch Linux:"
        echo "  sudo pacman -S mise"
        echo ""
        echo "  # Ubuntu/Debian:"
        echo "  sudo apt install mise"
        echo ""
        echo "  # macOS:"
        echo "  brew install mise"
        echo ""
        print_info "After installation, add mise to your shell:"
        echo "  echo 'eval \"\$(mise activate bash)\"' >> ~/.bashrc"
        echo "  source ~/.bashrc"
        echo ""
        print_info "More info: https://mise.jdx.dev/getting-started.html"
        return 1
    fi
}

# Check tox installation
check_tox() {
    print_section "Checking tox installation"

    if command_exists tox; then
        print_success "tox is installed ($(tox --version | head -n1))"
        return 0
    else
        print_error "tox is not installed"
        echo ""
        print_info "tox is a testing automation tool for Python"
        print_info "Install it with:"
        echo ""
        echo "  pip install tox"
        echo ""
        print_info "Or if you have a virtual environment active:"
        echo "  pip install --upgrade tox"
        echo ""
        return 1
    fi
}

# Check Python versions
check_python_versions() {
    print_section "Checking Python versions"

    local missing_versions=()
    local installed_versions=()

    MISE_PYTHON_DIR="$HOME/.local/share/mise/installs/python"

    for version in "${REQUIRED_VERSIONS[@]}"; do
        # Check if version is installed via mise
        if [ -d "$MISE_PYTHON_DIR" ]; then
            if compgen -G "$MISE_PYTHON_DIR/${version}*/bin/python*" > /dev/null; then
                installed_versions+=("$version")
                local full_version=$(ls -1 "$MISE_PYTHON_DIR/${version}"*/bin/python* 2>/dev/null | head -1 | xargs -I {} {} --version 2>/dev/null | awk '{print $2}')
                print_success "Python $version is installed ($full_version)"
            else
                missing_versions+=("$version")
                print_error "Python $version is NOT installed"
            fi
        else
            missing_versions+=("$version")
            print_error "Python $version is NOT installed (mise directory not found)"
        fi
    done

    if [ ${#missing_versions[@]} -gt 0 ]; then
        echo ""
        print_warning "Missing Python versions: ${missing_versions[*]}"
        echo ""
        print_info "Install missing versions with mise:"
        echo ""
        for version in "${missing_versions[@]}"; do
            echo "  mise install python@${version}"
        done
        echo ""
        print_info "Or install all at once:"
        echo "  mise install python@${REQUIRED_VERSIONS[0]} python@${REQUIRED_VERSIONS[1]} python@${REQUIRED_VERSIONS[2]} python@${REQUIRED_VERSIONS[3]} python@${REQUIRED_VERSIONS[4]}"
        echo ""
        return 1
    else
        echo ""
        print_success "All required Python versions are installed!"
        return 0
    fi
}

# Auto-install missing components
auto_install() {
    local component=$1

    case $component in
        mise)
            print_info "Attempting to install mise..."
            if curl -fsSL https://mise.run | sh; then
                print_success "mise installed successfully!"
                print_warning "Please restart your shell or run: source ~/.bashrc"
                return 0
            else
                print_error "Failed to install mise automatically"
                return 1
            fi
            ;;
        tox)
            print_info "Attempting to install tox..."
            if pip install tox; then
                print_success "tox installed successfully!"
                return 0
            else
                print_error "Failed to install tox automatically"
                return 1
            fi
            ;;
        python)
            print_info "Attempting to install missing Python versions..."
            local failed=0
            for version in "${REQUIRED_VERSIONS[@]}"; do
                MISE_PYTHON_DIR="$HOME/.local/share/mise/installs/python"
                if [ -d "$MISE_PYTHON_DIR" ] && compgen -G "$MISE_PYTHON_DIR/${version}*/bin/python*" > /dev/null; then
                    continue  # Already installed
                fi

                echo ""
                print_info "Installing Python ${version}..."
                if mise install "python@${version}"; then
                    print_success "Python ${version} installed!"
                else
                    print_error "Failed to install Python ${version}"
                    failed=1
                fi
            done
            return $failed
            ;;
    esac
}

# Main verification flow
run_checks() {
    local all_checks_passed=1
    local mise_installed=0
    local tox_installed=0
    local python_installed=0

    # Check mise
    if check_mise; then
        mise_installed=1
    else
        all_checks_passed=0
    fi

    # Check tox
    if check_tox; then
        tox_installed=1
    else
        all_checks_passed=0
    fi

    # Check Python versions (only if mise is installed)
    if [ $mise_installed -eq 1 ]; then
        if check_python_versions; then
            python_installed=1
        else
            all_checks_passed=0
        fi
    fi

    # Offer to auto-install if anything is missing
    if [ $all_checks_passed -eq 0 ]; then
        print_section "Setup Required"
        echo ""
        print_warning "Some dependencies are missing. Would you like to install them automatically?"
        echo ""
        read -p "Install missing dependencies? [y/N]: " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ $mise_installed -eq 0 ]; then
                auto_install mise
                mise_installed=$?
            fi

            if [ $tox_installed -eq 0 ]; then
                auto_install tox
                tox_installed=$?
            fi

            if [ $mise_installed -eq 1 ] && [ $python_installed -eq 0 ]; then
                auto_install python
                python_installed=$?
            fi

            # Re-check after installation
            echo ""
            print_section "Verification After Installation"
            run_checks
            return $?
        else
            echo ""
            print_error "Cannot proceed without required dependencies"
            exit 1
        fi
    else
        print_section "All dependencies satisfied!"
        print_success "Ready to run tests"
        return 0
    fi
}

# Only run checks if not passing --help or --version
if [[ "$*" =~ (--help|-h|--version|-v) ]]; then
    exec tox "$@"
fi

# Run all checks
run_checks

# Add all mise Python installations to PATH
MISE_PYTHON_DIR="$HOME/.local/share/mise/installs/python"

if [ -d "$MISE_PYTHON_DIR" ]; then
    # Find all installed Python versions and add their bin directories to PATH
    PYTHON_PATHS=""
    for py_dir in "$MISE_PYTHON_DIR"/3.{9,10,11,12,13}*/bin; do
        if [ -d "$py_dir" ]; then
            PYTHON_PATHS="$py_dir:$PYTHON_PATHS"
        fi
    done
    export PATH="$PYTHON_PATHS$PATH"
fi

# Show available quality checks if running with --list
if [[ "$*" =~ (--list|-l) ]]; then
    print_section "Available Test Environments"
    echo ""
    print_info "Python Test Environments:"
    echo "  py39, py310, py311, py312, py313  - Run tests on specific Python version"
    echo ""
    print_info "Code Quality Environments:"
    echo "  mypy         - Type checking with mypy"
    echo "  radon-cc     - Cyclomatic complexity analysis"
    echo "  radon-mi     - Maintainability index analysis"
    echo "  vulture      - Dead code detection"
    echo "  bandit       - Security vulnerability scanning"
    echo "  pylint       - Comprehensive linting"
    echo "  quality      - Run ALL quality checks (radon, vulture, bandit)"
    echo ""
    print_info "Examples:"
    echo "  ./scripts/tox-mise.sh              # Run all (tests + quality)"
    echo "  ./scripts/tox-mise.sh -e quality   # Quality checks only"
    echo "  ./scripts/tox-mise.sh -e py312     # Python 3.12 tests only"
    echo "  ./scripts/tox-mise.sh -e mypy      # Type checking only"
    echo ""
fi

# Run tox with all arguments passed through
print_section "Running tox"
exec tox "$@"
