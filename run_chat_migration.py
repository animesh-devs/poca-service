#!/usr/bin/env python3
"""
Run the chat migration script to update the database schema.

This script will update the Chat model from is_active to is_active_for_doctor and is_active_for_patient.
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.migrations.chat_active_status_migration import run_migration

if __name__ == "__main__":
    print("Running chat migration script...")
    run_migration()
    print("Migration script completed.")
