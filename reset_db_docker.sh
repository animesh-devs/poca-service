#!/bin/bash

# Script to reset the database for Docker setup

# Set up colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Change to the poca-service directory
cd /Users/animeshshukla/personal/poca-service
echo -e "${YELLOW}Current directory: $(pwd)${NC}"

echo -e "${YELLOW}Resetting the database for Docker setup...${NC}"

# Stop any running containers
echo -e "${YELLOW}Stopping any running containers...${NC}"
docker-compose down
echo -e "${GREEN}Containers stopped.${NC}"

# Remove the database file
echo -e "${YELLOW}Removing the database file...${NC}"
rm -f app.db
echo -e "${GREEN}Database file removed.${NC}"

# Build and start the containers
echo -e "${YELLOW}Building and starting the containers...${NC}"
docker-compose up -d --build
echo -e "${GREEN}Containers started.${NC}"

# Wait for the service to start
echo -e "${YELLOW}Waiting for the service to start...${NC}"
sleep 10

# Wait a bit longer for the service to fully start
echo -e "${YELLOW}Waiting for the service to fully start...${NC}"
sleep 20

# Check if the container is running
echo -e "${YELLOW}Checking if the container is running...${NC}"
if docker ps | grep -q poca-service-api; then
    echo -e "${GREEN}Container is running.${NC}"
else
    echo -e "${RED}Container is not running. Check the logs with 'docker-compose logs'.${NC}"
    docker-compose logs
    exit 1
fi

# Check if the service is responding
echo -e "${YELLOW}Checking if the service is responding...${NC}"
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}Service is responding and healthy!${NC}"
else
    echo -e "${RED}Service is not responding. Check the logs with 'docker-compose logs'.${NC}"
    docker-compose logs
    exit 1
fi

echo -e "${GREEN}Database reset completed!${NC}"
echo -e "${GREEN}You can now run the Docker test script: python run_docker_test.py${NC}"
exit 0
