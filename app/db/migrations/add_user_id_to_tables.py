#!/usr/bin/env python3
"""
Migration script to add user_id column to hospitals, doctors, and patients tables
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
    """Run the migration to add user_id column to tables"""
    logging.info("Starting migration to add user_id column to tables...")
    
    # Create SQLAlchemy engine
    engine = create_engine(
        settings.DATABASE_URL, 
        connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
    )
    
    with engine.connect() as conn:
        # Check if user_id column exists in hospitals table
        result = conn.execute(text("PRAGMA table_info(hospitals)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "user_id" not in columns:
            logging.info("Adding user_id column to hospitals table...")
            conn.execute(text("ALTER TABLE hospitals ADD COLUMN user_id VARCHAR"))
            logging.info("Added user_id column to hospitals table")
        else:
            logging.info("user_id column already exists in hospitals table")
        
        # Check if user_id column exists in doctors table
        result = conn.execute(text("PRAGMA table_info(doctors)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "user_id" not in columns:
            logging.info("Adding user_id column to doctors table...")
            conn.execute(text("ALTER TABLE doctors ADD COLUMN user_id VARCHAR"))
            logging.info("Added user_id column to doctors table")
        else:
            logging.info("user_id column already exists in doctors table")
        
        # Check if user_id column exists in patients table
        result = conn.execute(text("PRAGMA table_info(patients)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "user_id" not in columns:
            logging.info("Adding user_id column to patients table...")
            conn.execute(text("ALTER TABLE patients ADD COLUMN user_id VARCHAR"))
            logging.info("Added user_id column to patients table")
        else:
            logging.info("user_id column already exists in patients table")
        
        conn.commit()
    
    logging.info("Migration completed successfully")

if __name__ == "__main__":
    run_migration()
