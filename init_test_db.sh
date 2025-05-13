#!/bin/bash

# Script to initialize the test database

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Initializing test database for POCA service...${NC}"

# Activate virtual environment if it exists and is not already activated
if [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    . venv/bin/activate
    echo -e "${GREEN}Virtual environment activated.${NC}"
fi

# Run the init_test_db.py script
echo -e "${YELLOW}Running init_test_db.py...${NC}"
python testing-scripts/init_test_db.py

# Check if the script ran successfully
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Test database initialized successfully!${NC}"
else
    echo -e "${RED}Failed to initialize test database.${NC}"
    exit 1
fi

echo -e "${GREEN}You can now run the application with: python run.py${NC}"
exit 0
