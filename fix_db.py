#!/usr/bin/env python3
"""
Script to fix the database by updating user roles to uppercase.
"""

import sqlite3
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="\033[1;36m%(asctime)s - %(levelname)s\033[0m: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def fix_user_roles():
    """Fix user roles in the database by converting them to uppercase."""
    logging.info("Fixing user roles in the database...")
    
    try:
        # Connect to the database
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Get all users with lowercase roles
        cursor.execute("SELECT id, email, role FROM users")
        users = cursor.fetchall()
        
        # Update each user with uppercase role
        updated_count = 0
        for user_id, email, role in users:
            if role and role.upper() in ['ADMIN', 'DOCTOR', 'PATIENT', 'HOSPITAL']:
                cursor.execute(
                    "UPDATE users SET role = ? WHERE id = ?",
                    (role.upper(), user_id)
                )
                logging.info(f"Updated user {email} role from '{role}' to '{role.upper()}'")
                updated_count += 1
        
        # Commit changes
        conn.commit()
        logging.info(f"Successfully updated {updated_count} user roles")
        
        # Close connection
        conn.close()
        return True
    
    except Exception as e:
        logging.error(f"Error fixing user roles: {str(e)}")
        return False

if __name__ == "__main__":
    fix_user_roles()
