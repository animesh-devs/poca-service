#!/bin/bash

# Script to run Docker tests for POCA service

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Docker test for POCA service...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker and try again.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose and try again.${NC}"
    exit 1
fi

# Stop any running containers
echo -e "${YELLOW}Stopping any running containers...${NC}"
docker-compose down

# Build and start the containers
echo -e "${YELLOW}Building and starting the containers...${NC}"
docker-compose up -d --build

# Wait for the service to start
echo -e "${YELLOW}Waiting for the service to start...${NC}"
sleep 10

# Wait a bit longer for the service to fully start
echo -e "${YELLOW}Waiting for the service to fully start...${NC}"
sleep 20

# Run the health check
echo -e "${YELLOW}Running health check...${NC}"
python3 docker_health_check.py

# Check if the health check was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Health check failed. Check the logs with 'docker-compose logs'.${NC}"
    exit 1
fi

echo -e "${GREEN}Health check passed. Service is running correctly.${NC}"

# Check the test result
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Test completed successfully!${NC}"
else
    echo -e "${RED}Test failed. Check the logs above for details.${NC}"
fi

# Ask if the user wants to stop the containers
read -p "Do you want to stop the Docker containers? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Stopping the containers...${NC}"
    docker-compose down
    echo -e "${GREEN}Containers stopped.${NC}"
else
    echo -e "${YELLOW}Containers are still running. Stop them with 'docker-compose down' when you're done.${NC}"
fi

exit 0
