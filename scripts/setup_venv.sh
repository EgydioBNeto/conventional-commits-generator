#!/bin/bash
# Script to set up a virtual environment for CCG development

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set the virtual environment name
VENV_NAME=".venv"

echo -e "${YELLOW}Setting up a virtual environment for CCG development...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 first.${NC}"
    exit 1
fi

# Create the virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv $VENV_NAME

# Activate the virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source $VENV_NAME/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install the package in development mode with dev dependencies
echo -e "${YELLOW}Installing CCG in development mode...${NC}"
pip install -e ".[dev]"

# Install pre-commit hooks
echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
pre-commit install

echo -e "${GREEN}Setup complete! Virtual environment is ready.${NC}"
echo -e "${YELLOW}To activate the virtual environment:${NC}"
echo -e "  source $VENV_NAME/bin/activate"
echo -e "${YELLOW}To deactivate:${NC}"
echo -e "  deactivate"
