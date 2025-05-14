"""
Migration script to update the Chat model from is_active to is_active_for_doctor and is_active_for_patient.

This script should be run after updating the model but before using the application.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings

def run_migration():
    """
    Run the migration to update the Chat model.
    """
    # Create a database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if the is_active column exists
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'chats' AND column_name = 'is_active'"))
        is_active_exists = result.fetchone() is not None
        
        # Check if the new columns exist
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'chats' AND column_name = 'is_active_for_doctor'"))
        is_active_for_doctor_exists = result.fetchone() is not None
        
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'chats' AND column_name = 'is_active_for_patient'"))
        is_active_for_patient_exists = result.fetchone() is not None
        
        # If is_active exists but the new columns don't, add them
        if is_active_exists and not (is_active_for_doctor_exists and is_active_for_patient_exists):
            print("Adding new columns...")
            
            # Add the new columns
            if not is_active_for_doctor_exists:
                db.execute(text("ALTER TABLE chats ADD COLUMN is_active_for_doctor BOOLEAN DEFAULT TRUE"))
            
            if not is_active_for_patient_exists:
                db.execute(text("ALTER TABLE chats ADD COLUMN is_active_for_patient BOOLEAN DEFAULT TRUE"))
            
            # Copy values from is_active to the new columns
            db.execute(text("UPDATE chats SET is_active_for_doctor = is_active, is_active_for_patient = is_active"))
            
            # Drop the old column
            db.execute(text("ALTER TABLE chats DROP COLUMN is_active"))
            
            db.commit()
            print("Migration completed successfully!")
        else:
            if not is_active_exists:
                print("The is_active column does not exist. Migration may have already been completed.")
            elif is_active_for_doctor_exists and is_active_for_patient_exists:
                print("The new columns already exist. Migration may have already been completed.")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
