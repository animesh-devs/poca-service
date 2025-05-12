#!/usr/bin/env python3
"""
Simple health check script for the POCA service running in Docker.
"""

import requests
import json
import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# API configuration
BASE_URL = "http://localhost:8000"

def check_health():
    """Check if the service is running"""
    logging.info("Checking if the service is running...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                logging.info("Service is healthy!")
                return True
        
        logging.error(f"Service is not healthy. Status code: {response.status_code}, Response: {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to the service: {str(e)}")
        return False

def check_api():
    """Check if the API is working"""
    logging.info("Checking if the API is working...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/docs")
        if response.status_code == 200:
            logging.info("API documentation is accessible!")
            return True
        
        logging.error(f"API documentation is not accessible. Status code: {response.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to the API: {str(e)}")
        return False

def main():
    """Main function"""
    logging.info("Starting Docker health check...")
    
    # Check if the service is running
    if not check_health():
        logging.error("Health check failed. Aborting test.")
        return False
    
    # Check if the API is working
    if not check_api():
        logging.error("API check failed. Aborting test.")
        return False
    
    logging.info("Docker health check completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
