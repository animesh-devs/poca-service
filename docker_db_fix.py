#!/usr/bin/env python3
"""
Script to fix the database path for Docker testing.
This script modifies the create_chat_in_db function to use the correct database path.
"""

import os
import sys
import re

def fix_db_path(file_path):
    """Fix the database path in the test script"""
    print(f"Fixing database path in {file_path}...")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the database path
    pattern = r"conn = sqlite3\.connect\('app\.db'\)"
    replacement = "conn = sqlite3.connect('/app/app.db')"
    
    new_content = re.sub(pattern, replacement, content)
    
    # Write the file
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print("Database path fixed.")

if __name__ == "__main__":
    # Check if the file exists
    test_file = "test_docker.py"
    if not os.path.exists(test_file):
        print(f"Error: {test_file} not found.")
        sys.exit(1)
    
    # Fix the database path
    fix_db_path(test_file)
