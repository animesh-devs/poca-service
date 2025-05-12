import os
import argparse
import uuid
from datetime import datetime

from app.db.database import engine, Base, get_db
from app.models.user import User, UserRole
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.mapping import HospitalDoctorMapping, HospitalPatientMapping, DoctorPatientMapping
from app.api.auth import get_password_hash

def init_db():
    """Initialize the database with tables and default admin user"""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Check if admin user already exists
        admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin_exists:
            print("Admin user already exists. Skipping initialization.")
            return
        
        # Create admin user
        admin_id = str(uuid.uuid4())
        admin_user = User(
            id=admin_id,
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            name="Admin User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Created admin user with ID: {admin_id}")
        print("Admin credentials: admin@example.com / admin123")
        
        print("Database initialized successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()

def main():
    """Main function to initialize the database"""
    parser = argparse.ArgumentParser(description="Initialize the database for POCA Service")
    parser.add_argument("--force", action="store_true", help="Force initialization even if database already exists")
    args = parser.parse_args()
    
    # Check if database file exists
    db_path = "app.db"
    if os.path.exists(db_path) and not args.force:
        print(f"Database file {db_path} already exists. Use --force to reinitialize.")
        return
    
    # Initialize database
    init_db()

if __name__ == "__main__":
    main()
