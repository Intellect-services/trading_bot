#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command status
check_status() {
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: $1 failed${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}Starting workflow verification...${NC}"

# Create and activate virtual environment
echo -e "${YELLOW}Setting up virtual environment...${NC}"
python3.10 -m venv venv310
check_status "Virtual environment creation"
source venv310/bin/activate
check_status "Virtual environment activation"

# Upgrade pip and install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
python -m pip install --upgrade pip
check_status "Pip upgrade"
pip install setuptools wheel
check_status "Setuptools and wheel installation"
pip install -r requirements.txt
check_status "Requirements installation"
pip install pytest pytest-cov flake8 mypy
check_status "Test tools installation"

# Run flake8
echo -e "${YELLOW}Running flake8...${NC}"
flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
check_status "Flake8 error checking"
flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
check_status "Flake8 style checking"

# Run mypy
echo -e "${YELLOW}Running mypy...${NC}"
mypy src/utils/ --ignore-missing-imports --disallow-untyped-defs
check_status "Mypy utils check"
mypy src/core/ --ignore-missing-imports --disallow-untyped-defs
check_status "Mypy core check"
mypy src/backtesting/ --ignore-missing-imports --disallow-untyped-defs
check_status "Mypy backtesting check"

# Run pytest
echo -e "${YELLOW}Running tests...${NC}"
pytest --cov=src --cov-report=xml
check_status "Pytest execution"

# Run safety check
echo -e "${YELLOW}Running safety check...${NC}"
pip install safety==1.10.3
check_status "Safety installation"
safety check
check_status "Safety check"

# Run bandit
echo -e "${YELLOW}Running bandit...${NC}"
bandit -r src/
check_status "Bandit check"

echo -e "${GREEN}Workflow verification complete!${NC}" 