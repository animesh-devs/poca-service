#!/usr/bin/env python3
"""
Fix User Roles Script

This script fixes user roles in the database by converting them to uppercase.
"""

import sqlite3
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def fix_user_roles():
    """Fix user roles in the database by converting them to uppercase"""
    logging.info("Fixing user roles in the database...")
    
    try:
        # Connect to the database
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Get all users with their roles
        cursor.execute('SELECT id, role FROM users')
        users = cursor.fetchall()
        
        # Update each user's role to uppercase
        updates = 0
        for user_id, role in users:
            if role and not role.isupper():
                upper_role = role.upper()
                logging.info(f"Converting role for user {user_id}: {role} -> {upper_role}")
                cursor.execute('UPDATE users SET role = ? WHERE id = ?', (upper_role, user_id))
                updates += 1
        
        # Commit the changes
        conn.commit()
        
        # Verify the changes
        cursor.execute('SELECT id, role FROM users')
        updated_users = cursor.fetchall()
        for user_id, role in updated_users:
            logging.info(f"User {user_id} now has role: {role}")
        
        # Close the connection
        conn.close()
        
        logging.info(f"Fixed {updates} user roles in the database")
        return True
    except Exception as e:
        logging.error(f"Error fixing user roles: {str(e)}")
        return False

def main():
    """Main function"""
    logging.info("Starting database fix script...")
    
    # Fix user roles
    if fix_user_roles():
        logging.info("Database fixes completed successfully!")
    else:
        logging.error("Failed to fix database")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
