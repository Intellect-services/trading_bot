#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print error messages
print_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

echo -e "${YELLOW}Starting workflow verification...${NC}"

# Check if Python 3.10 is installed
if ! command_exists python3.10; then
    print_error "Python 3.10 is not installed. Please install it first."
fi

# Create and activate virtual environment
echo -e "${YELLOW}Setting up virtual environment...${NC}"
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip and install setuptools
echo -e "${YELLOW}Upgrading pip and installing setuptools...${NC}"
pip install --upgrade pip setuptools wheel

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if all required tools are installed
echo -e "${YELLOW}Verifying tool installations...${NC}"
for tool in flake8 mypy pytest safety bandit; do
    if ! command_exists $tool; then
        print_error "$tool is not installed. Please check the installation."
    fi
done

# Run flake8
echo -e "${YELLOW}Running flake8...${NC}"
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run mypy
echo -e "${YELLOW}Running mypy...${NC}"
mypy src/utils/ --ignore-missing-imports
mypy src/core/ --ignore-missing-imports
mypy src/backtesting/ --ignore-missing-imports

# Run pytest
echo -e "${YELLOW}Running pytest...${NC}"
pytest --cov=src --cov-report=xml

# Run safety check
echo -e "${YELLOW}Running safety check...${NC}"
safety check

# Run bandit
echo -e "${YELLOW}Running bandit...${NC}"
bandit -r src/

echo -e "${GREEN}Workflow verification complete!${NC}" 