"""
Profile photo loader for startup
Loads profile photos into memory storage when the application starts
"""
import os
import logging
from typing import Dict, List
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.document import FileDocument
from app.services.document_storage import document_storage

logger = logging.getLogger(__name__)

def load_profile_photos_into_storage():
    """Load all profile photos from database into memory storage"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get all profile photo records from database
        profile_photos = db.query(FileDocument).filter(
            FileDocument.remark.like("Profile photo for test data%")
        ).all()
        
        if not profile_photos:
            logger.info("No profile photos found in database")
            return
        
        loaded_count = 0
        
        for photo_record in profile_photos:
            try:
                # Determine the file path based on the filename
                filename = photo_record.file_name
                
                # Try multiple possible paths for the photo files
                possible_paths = [
                    os.path.join('data', 'doctor profile photos', filename),
                    os.path.join('data', 'patient profile photos', filename),
                    os.path.join('..', 'data', 'doctor profile photos', filename),
                    os.path.join('..', 'data', 'patient profile photos', filename),
                    filename  # Just the filename in current directory
                ]

                photo_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        photo_path = path
                        break

                if not photo_path:
                    logger.warning(f"Profile photo file not found for: {filename}")
                    continue
                
                # Read the photo file
                with open(photo_path, 'rb') as f:
                    file_content = f.read()
                
                # Determine content type
                if filename.lower().endswith('.png'):
                    content_type = 'image/png'
                elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                    content_type = 'image/jpeg'
                else:
                    content_type = 'image/png'
                
                # Store in memory using the same ID from database
                document_storage._storage[photo_record.id] = (
                    file_content,
                    {
                        "filename": filename,
                        "content_type": content_type,
                        "size": len(file_content),
                        "document_id": photo_record.id
                    }
                )
                
                loaded_count += 1
                logger.info(f"Loaded profile photo into memory: {filename} (ID: {photo_record.id}) from {photo_path}")
                
            except Exception as e:
                logger.error(f"Failed to load profile photo {photo_record.file_name}: {e}")
                continue
        
        logger.info(f"Successfully loaded {loaded_count} profile photos into memory storage")
        
    except Exception as e:
        logger.error(f"Failed to load profile photos: {e}")
    finally:
        if 'db' in locals():
            db.close()

def get_profile_photo_paths() -> Dict[str, List[str]]:
    """Get available profile photo paths"""
    doctor_photos_dir = os.path.join('data', 'doctor profile photos')
    patient_photos_dir = os.path.join('data', 'patient profile photos')
    
    doctor_photos = []
    patient_photos = []
    
    if os.path.exists(doctor_photos_dir):
        doctor_photos = [f for f in os.listdir(doctor_photos_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if os.path.exists(patient_photos_dir):
        patient_photos = [f for f in os.listdir(patient_photos_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    return {
        'doctor_photos': doctor_photos,
        'patient_photos': patient_photos
    }
