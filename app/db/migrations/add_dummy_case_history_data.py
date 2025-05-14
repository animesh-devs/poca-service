#!/usr/bin/env python3
"""
Migration script to add dummy case history, document, and report data
"""

import sys
import os
import logging
from sqlalchemy import create_engine, text
from uuid import uuid4
from datetime import datetime, timedelta
import json

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.config import settings
from app.db.database import get_db
from app.models.case_history import CaseHistory, Document, UploadedBy
from app.models.report import Report, PatientReportMapping, ReportDocument, ReportType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def run_migration():
    """Run the migration to add dummy case history, document, and report data"""
    logging.info("Starting migration to add dummy case history, document, and report data...")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get all patients
        result = db.execute(text("SELECT id FROM patients"))
        patient_ids = [row[0] for row in result.fetchall()]
        
        if not patient_ids:
            logging.warning("No patients found in the database. Skipping migration.")
            return
        
        logging.info(f"Found {len(patient_ids)} patients in the database.")
        
        # Add case histories for each patient
        for patient_id in patient_ids:
            # Check if patient already has a case history
            existing_case_history = db.query(CaseHistory).filter(CaseHistory.patient_id == patient_id).first()
            
            if existing_case_history:
                logging.info(f"Patient {patient_id} already has a case history. Skipping.")
                continue
            
            # Create a new case history
            case_history_id = str(uuid4())
            case_history = CaseHistory(
                id=case_history_id,
                patient_id=patient_id,
                summary="Patient has a history of hypertension and diabetes. Regular check-ups recommended.",
                documents=[]  # Empty document IDs array
            )
            
            db.add(case_history)
            db.flush()  # Flush to get the ID
            
            logging.info(f"Created case history with ID: {case_history_id} for patient: {patient_id}")
            
            # Add documents to the case history
            document_ids = []
            
            # Document 1: Blood test
            doc1_id = str(uuid4())
            doc1 = Document(
                id=doc1_id,
                case_history_id=case_history_id,
                file_name="blood_test_results.pdf",
                size=1024,
                link="https://example.com/documents/blood_test_results.pdf",
                uploaded_by=UploadedBy.DOCTOR,
                remark="Regular blood test results"
            )
            db.add(doc1)
            document_ids.append(doc1_id)
            
            # Document 2: X-ray
            doc2_id = str(uuid4())
            doc2 = Document(
                id=doc2_id,
                case_history_id=case_history_id,
                file_name="chest_xray.jpg",
                size=2048,
                link="https://example.com/documents/chest_xray.jpg",
                uploaded_by=UploadedBy.DOCTOR,
                remark="Chest X-ray"
            )
            db.add(doc2)
            document_ids.append(doc2_id)
            
            # Update case history with document IDs
            case_history.documents = document_ids
            
            logging.info(f"Added {len(document_ids)} documents to case history: {case_history_id}")
            
            # Create a report for the patient
            report_id = str(uuid4())
            report = Report(
                id=report_id,
                title="Annual Health Check-up Report",
                description="Results of annual health check-up",
                report_type=ReportType.LAB_TEST
            )
            db.add(report)
            
            # Create patient-report mapping
            mapping_id = str(uuid4())
            mapping = PatientReportMapping(
                id=mapping_id,
                patient_id=patient_id,
                report_id=report_id
            )
            db.add(mapping)
            
            # Add a document to the report
            report_doc_id = str(uuid4())
            report_doc = ReportDocument(
                id=report_doc_id,
                report_id=report_id,
                file_name="annual_checkup.pdf",
                size=3072,
                link="https://example.com/reports/annual_checkup.pdf",
                uploaded_by="doctor",  # User ID who uploaded the document
                remark="Annual check-up report"
            )
            db.add(report_doc)
            
            logging.info(f"Created report with ID: {report_id} for patient: {patient_id}")
        
        # Commit all changes
        db.commit()
        logging.info("Migration completed successfully")
        
    except Exception as e:
        db.rollback()
        logging.error(f"Error during migration: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
