#!/bin/bash
# Script to set up a virtual environment for CCG development on Linux/macOS

# Set the virtual environment name
VENV_NAME=.venv

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for reinstall flag
REINSTALL=0
if [ "$1" = "--reinstall" ] || [ "$1" = "-r" ]; then
    REINSTALL=1
fi

# Check if venv exists
if [ -d "$VENV_NAME" ]; then
    echo -e "${YELLOW}Virtual environment already exists.${NC}"

    if [ $REINSTALL -eq 1 ]; then
        echo -e "${GREEN}Reinstalling CCG within existing virtual environment...${NC}"

        # Activate the virtual environment
        source $VENV_NAME/bin/activate

        # Reinstall the package in development mode
        echo -e "${YELLOW}Reinstalling CCG in development mode...${NC}"
        pip uninstall -y ccg
        pip install -e .[dev]

        echo -e "${GREEN}CCG has been reinstalled successfully.${NC}"

        # Show completion message and exit
        echo
        echo -e "${GREEN}Setup complete! Virtual environment is ready.${NC}"
        echo
        echo -e "To activate the virtual environment:"
        echo -e "  source $VENV_NAME/bin/activate"
        echo -e "To reinstall after changes:"
        echo -e "  $0 --reinstall"
        echo -e "To deactivate:"
        echo -e "  deactivate"

        exit 0
    else
        echo -e "${YELLOW}Use '--reinstall' or '-r' flag to reinstall CCG without recreating the venv.${NC}"
        echo -e "Example: $0 --reinstall"

        # Ask if user wants to continue with full setup
        read -p "Do you want to continue with full setup? (y/n): " CONTINUE
        if [[ $CONTINUE =~ ^[Nn]$ ]]; then
            exit 0
        fi
    fi
fi

echo -e "${GREEN}Setting up a virtual environment for CCG development...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed or not in PATH. Please install Python first.${NC}"
    exit 1
fi

# Create the virtual environment if it doesn't exist
if [ ! -d "$VENV_NAME" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv $VENV_NAME
else
    echo -e "${YELLOW}Using existing virtual environment.${NC}"
fi

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source $VENV_NAME/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip

# Install the package in development mode with dev dependencies
echo -e "${YELLOW}Installing CCG in development mode...${NC}"
pip install -e .[dev]

# Install pre-commit hooks
echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
pre-commit install

echo
echo -e "${GREEN}Setup complete! Virtual environment is ready.${NC}"
echo
echo -e "To activate the virtual environment:"
echo -e "  source $VENV_NAME/bin/activate"
echo -e "To reinstall after changes:"
echo -e "  $0 --reinstall"
echo -e "To deactivate:"
echo -e "  deactivate"

# Keep the environment active
