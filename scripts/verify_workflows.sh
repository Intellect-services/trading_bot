#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting workflow verification...${NC}"

# Create and activate virtual environment
echo -e "${YELLOW}Setting up virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

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