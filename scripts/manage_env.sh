#!/bin/bash

# CCG Environment Manager

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

VENV_DIR=".venv"

is_venv_active() {
    [[ "$VIRTUAL_ENV" != "" ]]
}
venv_exists() {
    [[ -d "$VENV_DIR" ]]
}

show_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🔍 CCG ENVIRONMENT STATUS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo

    # Check if environment exists
    if venv_exists; then
        echo -e "${GREEN}✅ Virtual environment: Exists ($VENV_DIR)${NC}"
    else
        echo -e "${RED}❌ Virtual environment: Not found${NC}"
    fi

    # Check if it's active
    if is_venv_active; then
        echo -e "${GREEN}✅ Status: ACTIVE${NC}"
        echo -e "${CYAN}📍 Location: $VIRTUAL_ENV${NC}"
    else
        echo -e "${YELLOW}⚠️  Status: INACTIVE${NC}"
    fi

    # Check Python
    if is_venv_active; then
        PYTHON_VERSION=$(python --version 2>&1)
        PYTHON_PATH=$(which python)
        echo -e "${CYAN}🐍 Python: $PYTHON_VERSION${NC}"
        echo -e "${CYAN}📁 Path: $PYTHON_PATH${NC}"
    fi

    # Check CCG
    if command -v ccg &> /dev/null; then
        CCG_VERSION=$(ccg --version 2>/dev/null || echo "version not available")
        echo -e "${GREEN}✅ CCG: $CCG_VERSION${NC}"
    else
        echo -e "${RED}❌ CCG: Not installed or not available${NC}"
    fi

    echo
}

# Function to activate environment
activate_env() {
    if ! venv_exists; then
        echo -e "${RED}❌ Virtual environment not found!${NC}"
        echo -e "${YELLOW}💡 Run: ./scripts/setup_venv.sh${NC}"
        return 1
    fi

    if is_venv_active; then
        echo -e "${YELLOW}⚠️  Environment is already active${NC}"
        return 0
    fi

    echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✅ Environment activated!${NC}"
    echo -e "${PURPLE}💡 Use 'deactivate' to deactivate${NC}"
}

# Function to deactivate environment
deactivate_env() {
    if ! is_venv_active; then
        echo -e "${YELLOW}⚠️  Environment is already inactive${NC}"
        return 0
    fi

    echo -e "${BLUE}🔄 Deactivating virtual environment...${NC}"
    deactivate
    echo -e "${GREEN}✅ Environment deactivated!${NC}"
}

# Function to reinstall dependencies
reinstall_deps() {
    if ! is_venv_active; then
        echo -e "${RED}❌ Virtual environment is not active${NC}"
        echo -e "${YELLOW}💡 Run: source $VENV_DIR/bin/activate${NC}"
        return 1
    fi

    echo -e "${BLUE}🔄 Reinstalling dependencies...${NC}"

    if [[ -f "requirements.txt" ]]; then
        pip install --upgrade -r requirements.txt
    fi

    if [[ -f "setup.py" ]] || [[ -f "pyproject.toml" ]]; then
        pip install -e .
    fi

    echo -e "${GREEN}✅ Dependencies reinstalled!${NC}"
}

# Function to clean and recreate environment
recreate_env() {
    echo -e "${YELLOW}⚠️  This will completely remove the current environment${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Operation cancelled${NC}"
        return 0
    fi

    if is_venv_active; then
        echo -e "${BLUE}🔄 Deactivating current environment...${NC}"
        deactivate
    fi

    if venv_exists; then
        echo -e "${BLUE}🗑️  Removing old environment...${NC}"
        rm -rf "$VENV_DIR"
    fi

    echo -e "${BLUE}🔧 Recreating environment...${NC}"
    ./scripts/setup_venv.sh
}

# Function to show environment info
show_info() {
    if ! is_venv_active; then
        echo -e "${YELLOW}⚠️  Environment is not active${NC}"
        echo -e "${YELLOW}💡 Run: source $VENV_DIR/bin/activate${NC}"
        return 1
    fi

    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}📋 DETAILED INFORMATION${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo

    echo -e "${CYAN}🐍 Python Info:${NC}"
    python --version
    echo -e "   📁 $(which python)"
    echo

    echo -e "${CYAN}📦 Pip Info:${NC}"
    pip --version
    echo

    echo -e "${CYAN}📚 Installed Packages:${NC}"
    pip list --format=columns
    echo

    if command -v ccg &> /dev/null; then
        echo -e "${CYAN}⚙️  CCG Info:${NC}"
        ccg --version
    fi
}

# Help function
show_help() {
    cat << EOF
🔧 CCG Environment Manager

COMMANDS:
    status      Show current environment status
    activate    Activate virtual environment
    deactivate  Deactivate virtual environment
    reinstall   Reinstall dependencies
    recreate    Clean and fully recreate environment
    info        Show detailed information
    help        Show this help

EXAMPLES:
    $0 status           # Check status
    $0 activate         # Activate environment
    $0 reinstall        # Reinstall dependencies
    $0 recreate         # Recreate environment

QUICK SHORTCUTS:
    source $VENV_DIR/bin/activate    # Activate
    deactivate                       # Deactivate
    ccg --version                    # Test CCG

EOF
}

# Main menu
case "${1:-status}" in
    "status"|"st")
        show_status
        ;;
    "activate"|"on")
        activate_env
        ;;
    "deactivate"|"off")
        deactivate_env
        ;;
    "reinstall"|"update")
        reinstall_deps
        ;;
    "recreate"|"reset")
        recreate_env
        ;;
    "info"|"details")
        show_info
        ;;
    "help"|"h"|"-h"|"--help")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unrecognized command: $1${NC}"
        echo
        show_help
        exit 1
        ;;
esac
