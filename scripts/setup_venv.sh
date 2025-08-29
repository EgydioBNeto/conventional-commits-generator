#!/bin/bash

# Conventional Commits Generator - Setup Script
# Version with detailed logs and visual feedback

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configurations
PYTHON_VERSION="3.8"
VENV_DIR=".venv"

# Function for logs with timestamp
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date "+%H:%M:%S")

    case $level in
        "INFO")
            echo -e "${BLUE}[${timestamp}] ℹ️  ${message}${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[${timestamp}] ✅ ${message}${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[${timestamp}] ⚠️  ${message}${NC}"
            ;;
        "ERROR")
            echo -e "${RED}[${timestamp}] ❌ ${message}${NC}"
            ;;
        "STEP")
            echo -e "${PURPLE}[${timestamp}] 🔄 ${message}${NC}"
            ;;
    esac
}

# Function to show progress
show_progress() {
    local message="$1"
    local command="$2"

    log "STEP" "$message"

    echo -n "   "
    eval "$command" &
    local pid=$!

    # Progress spinner
    local spin='-\|/'
    local i=0
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) %4 ))
        printf "\r   ${spin:$i:1} Processing... \r"
        sleep 0.2
    done

    wait $pid
    local exit_code=$?

    if [[ $exit_code -eq 1 ]]; then
        printf "\r   ❌ Error!           \n"
        return $exit_code
    fi
}

# Help function
show_help() {
    cat << EOF
🔧 Conventional Commits Generator - Setup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -p, --python     Minimum Python version (default: 3.8)
    -h, --help       Show this help

EXAMPLES:
    $0                # Normal installation
    $0 -p 3.9         # With Python 3.9+

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log "ERROR" "Unknown argument: $1"
            show_help
            exit 1
            ;;
    esac
done

# Banner
cat << 'EOF'

 ________      ________      ________
|\   ____\    |\   ____\    |\   ____\
\ \  \___|    \ \  \___|    \ \  \___|
 \ \  \        \ \  \        \ \  \  ___
  \ \  \____    \ \  \____    \ \  \|\  \
   \ \_______\   \ \_______\   \ \_______\
    \|_______|    \|_______|    \|_______|

🚀 Setting up development environment...

EOF

# 1. Check Python
log "STEP" "Checking Python installation..."

if ! command -v python3 &> /dev/null; then
    log "ERROR" "Python 3 not found. Please install Python 3.${PYTHON_VERSION}+"
    exit 1
fi

CURRENT_PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
log "INFO" "Python found: v${CURRENT_PYTHON_VERSION}"

# Check minimum version
if ! python3 -c "import sys; exit(0 if sys.version_info >= tuple(map(int, '${PYTHON_VERSION}'.split('.'))) else 1)"; then
    log "ERROR" "Python ${PYTHON_VERSION}+ is required. Current version: ${CURRENT_PYTHON_VERSION}"
    exit 1
fi

log "SUCCESS" "Python ${CURRENT_PYTHON_VERSION} is compatible"

# 2. Remove existing virtual environment
if [[ -d "$VENV_DIR" ]]; then
    log "WARNING" "Existing virtual environment found at $VENV_DIR"
    read -p "Do you want to remove and recreate? (Y/n): " -r
    echo
    if [[ -z "$REPLY" || $REPLY =~ ^[Yy]$ ]]; then
        log "STEP" "Removing previous virtual environment..."
        rm -rf "$VENV_DIR"
        log "SUCCESS" "Previous environment removed"
    else
        log "INFO" "Keeping existing environment"
    fi
fi

# 3. Create virtual environment
if [[ ! -d "$VENV_DIR" ]]; then
    show_progress "Creating virtual environment" "python3 -m venv $VENV_DIR"
    log "SUCCESS" "Virtual environment created at $VENV_DIR"
else
    log "INFO" "Using existing virtual environment"
fi

# 4. Activate virtual environment
log "STEP" "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
log "SUCCESS" "Virtual environment activated"

# 5. Upgrade pip
show_progress "Upgrading pip" "python -m pip install --upgrade pip"
log "SUCCESS" "pip upgraded to version $(pip --version | cut -d' ' -f2)"

# 6. Install project in development mode
if [[ -f "setup.py" ]] || [[ -f "pyproject.toml" ]]; then
    show_progress "Installing project in development mode" "pip install -e ."
    log "SUCCESS" "Project installed in development mode"
else
    log "WARNING" "setup.py or pyproject.toml not found"
fi

# 7. Verify installation
log "STEP" "Verifying installation..."

if command -v ccg &> /dev/null; then
    CCG_VERSION=$(ccg --version 2>/dev/null || echo "version not available")
    log "SUCCESS" "CCG installed successfully - $CCG_VERSION"
else
    log "WARNING" "'ccg' command not found in PATH"
fi

# 8. Final information
echo
log "SUCCESS" "Setup completed!"
echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 ENVIRONMENT SUCCESSFULLY CONFIGURED!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo
echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
echo
echo -e "${CYAN}1. Activate the virtual environment:${NC}"
echo -e "   ${BLUE}source $VENV_DIR/bin/activate${NC}"
echo
echo -e "${CYAN}2. Verify installation:${NC}"
echo -e "   ${BLUE}ccg --version${NC}"
echo
echo -e "${CYAN}3. Start using:${NC}"
echo -e "   ${BLUE}ccg${NC}"
echo
echo -e "${CYAN}4. Deactivate the environment (when done):${NC}"
echo -e "   ${BLUE}deactivate${NC}"
echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
