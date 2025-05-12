#!/bin/bash

# Script to run the Docker container, fix the database, and run both test scripts

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting test suite for POCA service...${NC}"

# Check if Docker is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Start Docker containers if not already running
if ! docker ps | grep -q poca-service-api-1; then
    echo -e "${YELLOW}Starting Docker containers...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Waiting for containers to start...${NC}"
    sleep 10
fi

# Reset the database
echo -e "${YELLOW}Resetting the database...${NC}"
./reset_db.sh

# Make test scripts executable
echo -e "${YELLOW}Making test scripts executable...${NC}"
chmod +x test_complete_flow.py
chmod +x docker_test.py

# Run test_complete_flow.py
echo -e "${YELLOW}Running test_complete_flow.py...${NC}"
python3 test_complete_flow.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}test_complete_flow.py completed successfully!${NC}"
else
    echo -e "${RED}test_complete_flow.py failed!${NC}"
    exit 1
fi

# Run docker_test.py
echo -e "${YELLOW}Running docker_test.py...${NC}"
python3 docker_test.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}docker_test.py completed successfully!${NC}"
else
    echo -e "${RED}docker_test.py failed!${NC}"
    exit 1
fi

echo -e "${GREEN}All tests completed successfully!${NC}"

# Ask if the user wants to stop the containers
read -p "Do you want to stop the Docker containers? (y/n) " stop_containers
if [[ $stop_containers == "y" ]]; then
    echo -e "${YELLOW}Stopping Docker containers...${NC}"
    docker-compose down
    echo -e "${GREEN}Docker containers stopped${NC}"
else
    echo -e "${YELLOW}Docker containers are still running. Stop them with 'docker-compose down' when you're done.${NC}"
fi

exit 0
