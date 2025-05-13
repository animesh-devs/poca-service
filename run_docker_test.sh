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

# Check if Docker Compose is installed (either V1 or V2)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo -e "${GREEN}Using Docker Compose V1${NC}"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo -e "${GREEN}Using Docker Compose V2${NC}"
else
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose and try again.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker is not running. Please start Docker Desktop and try again.${NC}"
    exit 1
fi

# Stop any running containers
echo -e "${YELLOW}Stopping any running containers...${NC}"
$DOCKER_COMPOSE down

# Build and start the containers
echo -e "${YELLOW}Building and starting the containers...${NC}"
$DOCKER_COMPOSE up -d --build

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
    echo -e "${RED}Container is not running. Check the logs with '$DOCKER_COMPOSE logs'.${NC}"
    $DOCKER_COMPOSE logs
    exit 1
fi

# Check if the service is responding
echo -e "${YELLOW}Checking if the service is responding...${NC}"
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}Service is responding and healthy!${NC}"
else
    echo -e "${RED}Service is not responding. Check the logs with '$DOCKER_COMPOSE logs'.${NC}"
    $DOCKER_COMPOSE logs
    exit 1
fi

echo -e "${GREEN}Docker test completed successfully!${NC}"

# Ask if the user wants to stop the containers
read -p "Do you want to stop the Docker containers? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Stopping the containers...${NC}"
    $DOCKER_COMPOSE down
    echo -e "${GREEN}Containers stopped.${NC}"
else
    echo -e "${YELLOW}Containers are still running. Stop them with '$DOCKER_COMPOSE down' when you're done.${NC}"
fi

exit 0
