#!/usr/bin/env python3
"""
Script to run Docker tests for POCA service
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

def check_docker_installed():
    """Check if Docker is installed"""
    print_color(YELLOW, "Checking if Docker is installed...")
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print_color(RED, "Docker is not installed. Please install Docker and try again.")
        sys.exit(1)
    print_color(GREEN, f"Docker is installed: {result.stdout.strip()}")

def check_docker_compose():
    """Check if Docker Compose is installed"""
    print_color(YELLOW, "Checking if Docker Compose is installed...")

    # Try Docker Compose V1
    result = run_command("docker-compose --version", check=False)
    if result.returncode == 0:
        print_color(GREEN, f"Using Docker Compose V1: {result.stdout.strip()}")
        return "docker-compose"

    # Try Docker Compose V2
    result = run_command("docker compose version", check=False)
    if result.returncode == 0:
        print_color(GREEN, f"Using Docker Compose V2: {result.stdout.strip()}")
        return "docker compose"

    print_color(RED, "Docker Compose is not installed. Please install Docker Compose and try again.")
    sys.exit(1)

def check_docker_running():
    """Check if Docker is running"""
    print_color(YELLOW, "Checking if Docker is running...")
    result = run_command("docker info", check=False)
    if result.returncode != 0:
        print_color(RED, "Docker is not running. Please start Docker Desktop and try again.")
        sys.exit(1)
    print_color(GREEN, "Docker is running.")

def stop_containers(docker_compose):
    """Stop any running containers"""
    print_color(YELLOW, "Stopping any running containers...")
    # Get the current directory
    current_dir = os.getcwd()
    print_color(YELLOW, f"Current directory: {current_dir}")

    # Check if docker-compose.yml exists in the current directory
    if os.path.exists(os.path.join(current_dir, "docker-compose.yml")):
        run_command(f"{docker_compose} down")
        print_color(GREEN, "Containers stopped.")
    else:
        print_color(YELLOW, "docker-compose.yml not found in the current directory. Searching for it...")
        # Try to find the docker-compose.yml file
        for root, dirs, files in os.walk(current_dir):
            if "docker-compose.yml" in files:
                compose_dir = root
                print_color(GREEN, f"Found docker-compose.yml in {compose_dir}")
                os.chdir(compose_dir)
                run_command(f"{docker_compose} down")
                os.chdir(current_dir)  # Go back to the original directory
                print_color(GREEN, "Containers stopped.")
                return

        print_color(RED, "docker-compose.yml not found. Cannot stop containers.")
        return

def start_containers(docker_compose):
    """Build and start the containers"""
    print_color(YELLOW, "Building and starting the containers...")
    # Get the current directory
    current_dir = os.getcwd()

    # Check if docker-compose.yml exists in the current directory
    if os.path.exists(os.path.join(current_dir, "docker-compose.yml")):
        run_command(f"{docker_compose} up -d --build")
        print_color(GREEN, "Containers started.")
    else:
        print_color(YELLOW, "docker-compose.yml not found in the current directory. Searching for it...")
        # Try to find the docker-compose.yml file
        for root, _, files in os.walk(current_dir):
            if "docker-compose.yml" in files:
                compose_dir = root
                print_color(GREEN, f"Found docker-compose.yml in {compose_dir}")
                os.chdir(compose_dir)
                run_command(f"{docker_compose} up -d --build")
                os.chdir(current_dir)  # Go back to the original directory
                print_color(GREEN, "Containers started.")
                return

        print_color(RED, "docker-compose.yml not found. Cannot start containers.")
        sys.exit(1)

def wait_for_service():
    """Wait for the service to start"""
    print_color(YELLOW, "Waiting for the service to start...")
    time.sleep(10)
    print_color(YELLOW, "Waiting for the service to fully start...")
    time.sleep(20)

def check_container_running():
    """Check if the container is running"""
    print_color(YELLOW, "Checking if the container is running...")
    result = run_command("docker ps | grep poca-service-api", check=False)
    if result.returncode != 0:
        print_color(RED, "Container is not running. Check the logs.")
        run_command("docker-compose logs")
        sys.exit(1)
    print_color(GREEN, "Container is running.")

def check_service_health():
    """Check if the service is responding"""
    print_color(YELLOW, "Checking if the service is responding...")
    try:
        # Try to import requests
        try:
            import requests
        except ImportError:
            print_color(YELLOW, "requests module not found. Installing it...")
            run_command("pip install requests")
            import requests

        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200 and "healthy" in response.text:
            print_color(GREEN, "Service is responding and healthy!")
            return True
        else:
            print_color(RED, f"Service is not healthy. Status code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print_color(RED, f"Error connecting to the service: {str(e)}")

        # Try using curl as a fallback
        print_color(YELLOW, "Trying with curl...")
        result = run_command("curl -s http://localhost:8000/health", check=False)
        if result.returncode == 0 and "healthy" in result.stdout:
            print_color(GREEN, "Service is responding and healthy (via curl)!")
            return True
        else:
            print_color(RED, "Service is not healthy (via curl).")
            return False

def main():
    """Main function"""
    print_color(YELLOW, "Starting Docker test for POCA service...")

    # Check prerequisites
    check_docker_installed()
    docker_compose = check_docker_compose()
    check_docker_running()

    # Stop any running containers
    stop_containers(docker_compose)

    # Start containers
    start_containers(docker_compose)

    # Wait for service to start
    wait_for_service()

    # Check if container is running
    check_container_running()

    # Check service health
    if not check_service_health():
        print_color(RED, "Service health check failed.")
        run_command(f"{docker_compose} logs")
        sys.exit(1)

    print_color(GREEN, "Docker test completed successfully!")

    # Ask if the user wants to stop the containers
    stop_containers_input = input("Do you want to stop the Docker containers? (y/n) ")
    if stop_containers_input.lower() == 'y':
        stop_containers(docker_compose)
    else:
        print_color(YELLOW, f"Containers are still running. Stop them with '{docker_compose} down' when you're done.")

if __name__ == "__main__":
    main()
