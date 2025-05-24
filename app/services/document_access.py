"""
Document access control service
Handles permissions for document access based on user roles and relationships
"""
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.models.user import User, UserRole
from app.models.document import FileDocument
from app.models.mapping import DoctorPatientMapping, UserPatientRelation
from app.models.patient import Patient
from app.models.doctor import Doctor

logger = logging.getLogger(__name__)

class DocumentAccessControl:
    """
    Service to handle document access permissions
    """
    
    @staticmethod
    def can_access_document(
        user: User, 
        document: FileDocument, 
        db: Session
    ) -> bool:
        """
        Check if a user can access a specific document
        
        Access rules:
        1. Admin users can access any document
        2. Users can access documents they uploaded
        3. Patients can access documents uploaded by their treating doctors
        4. Doctors can access documents uploaded by their patients
        5. Doctors can access documents uploaded by other doctors treating the same patients
        
        Args:
            user: The user requesting access
            document: The document being accessed
            db: Database session
            
        Returns:
            bool: True if user can access the document, False otherwise
        """
        # Rule 1: Admin users can access any document
        if user.role == UserRole.ADMIN:
            logger.info(f"Admin user {user.id} granted access to document {document.id}")
            return True
        
        # Rule 2: Users can access documents they uploaded
        if document.uploaded_by == user.id:
            logger.info(f"User {user.id} granted access to own document {document.id}")
            return True
        
        # For more complex access control, we need to determine relationships
        return DocumentAccessControl._check_relationship_access(user, document, db)
    
    @staticmethod
    def _check_relationship_access(
        user: User, 
        document: FileDocument, 
        db: Session
    ) -> bool:
        """
        Check access based on doctor-patient relationships
        
        Args:
            user: The user requesting access
            document: The document being accessed
            db: Database session
            
        Returns:
            bool: True if access is granted based on relationships
        """
        # Get the uploader of the document
        uploader = db.query(User).filter(User.id == document.uploaded_by).first()
        if not uploader:
            logger.warning(f"Document {document.id} has invalid uploader {document.uploaded_by}")
            return False
        
        if user.role == UserRole.PATIENT:
            return DocumentAccessControl._check_patient_access(user, uploader, db)
        elif user.role == UserRole.DOCTOR:
            return DocumentAccessControl._check_doctor_access(user, uploader, db)
        
        return False
    
    @staticmethod
    def _check_patient_access(
        patient_user: User, 
        uploader: User, 
        db: Session
    ) -> bool:
        """
        Check if a patient can access a document uploaded by someone else
        
        Patients can access documents uploaded by:
        - Their treating doctors
        
        Args:
            patient_user: The patient user requesting access
            uploader: The user who uploaded the document
            db: Database session
            
        Returns:
            bool: True if patient can access the document
        """
        if uploader.role != UserRole.DOCTOR:
            return False
        
        # Get patient entities for this user
        patient_relations = db.query(UserPatientRelation).filter(
            UserPatientRelation.user_id == patient_user.id
        ).all()
        
        patient_ids = [rel.patient_id for rel in patient_relations]
        
        # Get doctor entity for the uploader
        doctor = db.query(Doctor).filter(Doctor.user_id == uploader.id).first()
        if not doctor:
            return False
        
        # Check if this doctor treats any of the patient's entities
        doctor_patient_mappings = db.query(DoctorPatientMapping).filter(
            DoctorPatientMapping.doctor_id == doctor.id,
            DoctorPatientMapping.patient_id.in_(patient_ids)
        ).first()
        
        if doctor_patient_mappings:
            logger.info(f"Patient user {patient_user.id} granted access to document uploaded by treating doctor {uploader.id}")
            return True
        
        return False
    
    @staticmethod
    def _check_doctor_access(
        doctor_user: User, 
        uploader: User, 
        db: Session
    ) -> bool:
        """
        Check if a doctor can access a document uploaded by someone else
        
        Doctors can access documents uploaded by:
        - Their patients
        - Other doctors treating the same patients
        
        Args:
            doctor_user: The doctor user requesting access
            uploader: The user who uploaded the document
            db: Database session
            
        Returns:
            bool: True if doctor can access the document
        """
        # Get doctor entity for the requesting user
        doctor = db.query(Doctor).filter(Doctor.user_id == doctor_user.id).first()
        if not doctor:
            return False
        
        # Get patients treated by this doctor
        doctor_patient_mappings = db.query(DoctorPatientMapping).filter(
            DoctorPatientMapping.doctor_id == doctor.id
        ).all()
        
        patient_ids = [mapping.patient_id for mapping in doctor_patient_mappings]
        
        if uploader.role == UserRole.PATIENT:
            # Check if the uploader is one of the doctor's patients
            uploader_patient_relations = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == uploader.id,
                UserPatientRelation.patient_id.in_(patient_ids)
            ).first()
            
            if uploader_patient_relations:
                logger.info(f"Doctor user {doctor_user.id} granted access to document uploaded by patient {uploader.id}")
                return True
        
        elif uploader.role == UserRole.DOCTOR:
            # Check if the uploader doctor treats any of the same patients
            uploader_doctor = db.query(Doctor).filter(Doctor.user_id == uploader.id).first()
            if not uploader_doctor:
                return False
            
            uploader_patient_mappings = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.doctor_id == uploader_doctor.id,
                DoctorPatientMapping.patient_id.in_(patient_ids)
            ).first()
            
            if uploader_patient_mappings:
                logger.info(f"Doctor user {doctor_user.id} granted access to document uploaded by colleague doctor {uploader.id}")
                return True
        
        return False

# Global instance
document_access_control = DocumentAccessControl()
