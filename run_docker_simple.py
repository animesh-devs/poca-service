#!/usr/bin/env python3
"""
Simple script to run Docker tests for POCA service
"""

import subprocess
import time
import sys
import os

# ANSI colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[0;33m'
NC = '\033[0m'  # No Color

def print_color(color, message):
    """Print colored message"""
    print(f"{color}{message}{NC}")

def run_command(command, check=True):
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print_color(RED, f"Command failed: {e}")
        print_color(RED, f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def main():
    """Main function"""
    print_color(YELLOW, "Starting Docker test for POCA service...")
    
    # Change to the poca-service directory
    os.chdir("/Users/animeshshukla/personal/poca-service")
    print_color(YELLOW, f"Current directory: {os.getcwd()}")
    
    # Check if docker-compose.yml exists
    if not os.path.exists("docker-compose.yml"):
        print_color(RED, "docker-compose.yml not found in the current directory.")
        sys.exit(1)
    
    # Stop any running containers
    print_color(YELLOW, "Stopping any running containers...")
    run_command("docker-compose down")
    
    # Build and start the containers
    print_color(YELLOW, "Building and starting the containers...")
    run_command("docker-compose up -d --build")
    
    # Wait for the service to start
    print_color(YELLOW, "Waiting for the service to start...")
    time.sleep(10)
    
    # Wait a bit longer for the service to fully start
    print_color(YELLOW, "Waiting for the service to fully start...")
    time.sleep(20)
    
    # Check if the container is running
    print_color(YELLOW, "Checking if the container is running...")
    result = run_command("docker ps | grep poca-service-api", check=False)
    if result.returncode != 0:
        print_color(RED, "Container is not running. Check the logs.")
        run_command("docker-compose logs")
        sys.exit(1)
    print_color(GREEN, "Container is running.")
    
    # Check if the service is responding
    print_color(YELLOW, "Checking if the service is responding...")
    result = run_command("curl -s http://localhost:8000/health", check=False)
    if result.returncode != 0 or "healthy" not in result.stdout:
        print_color(RED, "Service is not healthy. Check the logs.")
        run_command("docker-compose logs")
        sys.exit(1)
    print_color(GREEN, "Service is responding and healthy!")
    
    print_color(GREEN, "Docker test completed successfully!")
    
    # Ask if the user wants to stop the containers
    stop_containers = input("Do you want to stop the Docker containers? (y/n) ")
    if stop_containers.lower() == 'y':
        print_color(YELLOW, "Stopping the containers...")
        run_command("docker-compose down")
        print_color(GREEN, "Containers stopped.")
    else:
        print_color(YELLOW, "Containers are still running. Stop them with 'docker-compose down' when you're done.")

if __name__ == "__main__":
    main()
