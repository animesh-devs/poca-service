#!/usr/bin/env python3
"""
Migration script to add feedback fields to the suggestions table
"""

import sys
import os
import logging
from sqlalchemy import create_engine, text

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def run_migration():
    """Run the migration to add feedback fields to the suggestions table"""
    logging.info("Starting migration to add feedback fields to the suggestions table...")

    # Create database engine
    engine = create_engine(settings.DATABASE_URL)

    try:
        # For SQLite, we need to check if the columns exist differently
        with engine.connect() as connection:
            # Check if the table exists
            result = connection.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='suggestions'
            """))

            if not result.fetchone():
                logging.info("Suggestions table does not exist. Skipping migration.")
                return

            # Get the current columns in the table
            result = connection.execute(text("PRAGMA table_info(suggestions)"))
            columns = [row[1] for row in result.fetchall()]

            # Add columns if they don't exist
            if 'updated_at' not in columns:
                connection.execute(text("ALTER TABLE suggestions ADD COLUMN updated_at TIMESTAMP"))
                logging.info("Added updated_at column")

            if 'has_feedback' not in columns:
                connection.execute(text("ALTER TABLE suggestions ADD COLUMN has_feedback BOOLEAN DEFAULT FALSE"))
                logging.info("Added has_feedback column")

            if 'feedback' not in columns:
                connection.execute(text("ALTER TABLE suggestions ADD COLUMN feedback TEXT"))
                logging.info("Added feedback column")

            if 'feedback_date' not in columns:
                connection.execute(text("ALTER TABLE suggestions ADD COLUMN feedback_date TIMESTAMP"))
                logging.info("Added feedback_date column")

            connection.commit()

        logging.info("Migration completed successfully")

    except Exception as e:
        logging.error(f"Error during migration: {str(e)}")

if __name__ == "__main__":
    run_migration()
