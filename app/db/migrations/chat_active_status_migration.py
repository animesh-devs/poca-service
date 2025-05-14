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

from app.config import settings

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
        # For SQLite, we need to use PRAGMA table_info to get column information
        result = db.execute(text("PRAGMA table_info(chats)"))
        columns = result.fetchall()

        # Check if columns exist
        column_names = [column[1] for column in columns]  # Column name is at index 1

        is_active_exists = 'is_active' in column_names
        is_active_for_doctor_exists = 'is_active_for_doctor' in column_names
        is_active_for_patient_exists = 'is_active_for_patient' in column_names

        print(f"Columns found: {column_names}")
        print(f"is_active exists: {is_active_exists}")
        print(f"is_active_for_doctor exists: {is_active_for_doctor_exists}")
        print(f"is_active_for_patient exists: {is_active_for_patient_exists}")

        # If is_active exists but the new columns don't, add them
        if is_active_exists and not (is_active_for_doctor_exists and is_active_for_patient_exists):
            print("Adding new columns...")

            # Add the new columns
            if not is_active_for_doctor_exists:
                db.execute(text("ALTER TABLE chats ADD COLUMN is_active_for_doctor BOOLEAN DEFAULT 1"))

            if not is_active_for_patient_exists:
                db.execute(text("ALTER TABLE chats ADD COLUMN is_active_for_patient BOOLEAN DEFAULT 1"))

            # Copy values from is_active to the new columns
            db.execute(text("UPDATE chats SET is_active_for_doctor = is_active, is_active_for_patient = is_active"))

            # SQLite doesn't support dropping columns directly, so we need to create a new table
            # and copy the data over

            # First, get all column names except is_active
            columns_to_keep = [col for col in column_names if col != 'is_active']
            columns_str = ', '.join(columns_to_keep)

            # Create a new table without the is_active column
            db.execute(text(f"""
                CREATE TABLE chats_new (
                    id TEXT PRIMARY KEY,
                    doctor_id TEXT NOT NULL,
                    patient_id TEXT NOT NULL,
                    is_active_for_doctor BOOLEAN DEFAULT 1,
                    is_active_for_patient BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))

            # Copy data from the old table to the new table
            db.execute(text(f"""
                INSERT INTO chats_new (id, doctor_id, patient_id, is_active_for_doctor, is_active_for_patient, created_at, updated_at)
                SELECT id, doctor_id, patient_id, is_active_for_doctor, is_active_for_patient, created_at, updated_at
                FROM chats
            """))

            # Drop the old table
            db.execute(text("DROP TABLE chats"))

            # Rename the new table to the original name
            db.execute(text("ALTER TABLE chats_new RENAME TO chats"))

            db.commit()
            print("Migration completed successfully!")
        elif not is_active_exists and not (is_active_for_doctor_exists and is_active_for_patient_exists):
            # Neither old nor new columns exist, create the new columns directly
            print("Creating new columns directly...")

            # Create a new table with the correct schema if it doesn't exist
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    doctor_id TEXT NOT NULL,
                    patient_id TEXT NOT NULL,
                    is_active_for_doctor BOOLEAN DEFAULT 1,
                    is_active_for_patient BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """))

            db.commit()
            print("New table schema created successfully!")
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
