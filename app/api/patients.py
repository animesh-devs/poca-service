from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
import logging

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.mapping import DoctorPatientMapping, UserPatientRelation
from app.models.case_history import CaseHistory, Document, UploadedBy
from app.models.report import Report, PatientReportMapping, ReportDocument, ReportType
from app.models.document import FileDocument, DocumentType
from app.schemas.patient import PatientResponse, AdminPatientCreate
from app.schemas.case_history import CaseHistoryCreate, CaseHistoryUpdate, CaseHistoryResponse, DocumentResponse
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, ReportDocumentResponse
from app.services.document_processor import document_processor
from app.utils.document_utils import enhance_case_history_documents, enhance_report_documents
from app.utils.decorators import standardize_response
from app.dependencies import get_current_user, get_admin_user, get_user_entity_id
from app.api.auth import get_password_hash
from app.errors import ErrorCode, create_error_response
import logging

router = APIRouter()
logger = logging.getLogger(__name__)



@router.get("/{patient_id}/case-history", response_model=CaseHistoryResponse)
@standardize_response
async def get_case_history(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Get the most recent case history for a patient

    Returns only existing case history. If no case history exists, returns 404.

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            # Try to find patient by user_id
            user = db.query(User).filter(User.id == patient_id).first()
            if user and user.role == UserRole.PATIENT:
                # Get patient by user_id
                patient = db.query(Patient).filter(Patient.user_id == user.id).first()

                # If not found, try to get patient by profile_id
                if not patient and user.profile_id:
                    patient = db.query(Patient).filter(Patient.id == user.profile_id).first()

                if patient:
                    patient_id = patient.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=create_error_response(
                            status_code=status.HTTP_404_NOT_FOUND,
                            message="Patient not found",
                            error_code=ErrorCode.RES_001
                        )
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=create_error_response(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message="Patient not found",
                        error_code=ErrorCode.RES_001
                    )
                )

        # Check if user is authorized to view this patient's case history
        is_admin = current_user.role == UserRole.ADMIN
        is_doctor = current_user.role == UserRole.DOCTOR

        # For patients, we need to check if the user_entity_id is the patient_id
        # or if the user has a relation to this patient (1:n relationship)
        is_patient_owner = False
        if current_user.role == UserRole.PATIENT:
            if user_entity_id == patient_id:
                is_patient_owner = True
            else:
                # Check if the user has a relation to this patient
                from app.models.mapping import UserPatientRelation
                relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == patient_id
                ).first()
                is_patient_owner = relation is not None

        # For doctors, check if they are treating this patient
        doctor_treating_patient = False
        if is_doctor:
            # Check if there's a doctor-patient mapping
            doctor = db.query(Doctor).filter(Doctor.id == user_entity_id).first()
            if doctor:
                mapping = db.query(DoctorPatientMapping).filter(
                    DoctorPatientMapping.doctor_id == doctor.id,
                    DoctorPatientMapping.patient_id == patient_id
                ).first()
                doctor_treating_patient = mapping is not None

        if not (is_admin or is_patient_owner or doctor_treating_patient):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get the most recent case history
        case_history = db.query(CaseHistory).filter(
            CaseHistory.patient_id == patient_id
        ).order_by(CaseHistory.created_at.desc()).first()

        # If no case history exists, return 404
        if not case_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Case history not found for this patient",
                    error_code=ErrorCode.RES_001
                )
            )

        # Get documents for this case history
        documents = db.query(Document).filter(
            Document.case_history_id == case_history.id
        ).all()

        # Enhance documents with download links
        enhanced_documents = enhance_case_history_documents(documents)

        # Construct response
        return CaseHistoryResponse(
            id=case_history.id,
            patient_id=case_history.patient_id,
            summary=case_history.summary,
            documents=case_history.documents,
            created_at=case_history.created_at,
            updated_at=case_history.updated_at,
            document_files=[DocumentResponse(**doc) for doc in enhanced_documents]
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )

@router.post("/{patient_id}/case-history", response_model=CaseHistoryResponse)
@standardize_response
async def create_case_history(
    patient_id: str,
    case_history_data: CaseHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Create a new case history for a patient
    """

    logger = logging.getLogger(__name__)

    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR

    logger.info(f"user_entity_id: {user_entity_id}, patient_id: {patient_id}, role: {current_user.role}")


    # For patients, we need to check if the user_entity_id is the patient_id
    # or if the user has a relation to this patient (1:n relationship)
    is_patient_owner = False
    if current_user.role == UserRole.PATIENT:
        if user_entity_id == patient_id:
            is_patient_owner = True
        else:
            # Check if the user has a relation to this patient
            from app.models.mapping import UserPatientRelation
            relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id,
                UserPatientRelation.patient_id == patient_id
            ).first()
            is_patient_owner = relation is not None

    # For doctors, check if they are treating this patient
    doctor_treating_patient = False
    if is_doctor:
        # Check if there's a doctor-patient mapping
        doctor = db.query(Doctor).filter(Doctor.id == user_entity_id).first()
        if doctor:
            mapping = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.doctor_id == doctor.id,
                DoctorPatientMapping.patient_id == patient_id
            ).first()
            doctor_treating_patient = mapping is not None

    if not (is_admin or doctor_treating_patient or is_patient_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Invalid entity ID for this user",
                error_code=ErrorCode.AUTH_004
            )
        )
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Generate AI-enhanced summary if documents are provided
    enhanced_summary = case_history_data.summary
    if case_history_data.documents and case_history_data.summary:
        try:
            logger.info(f"Generating AI-enhanced summary for {len(case_history_data.documents)} documents")
            enhanced_summary = await document_processor.generate_case_history_summary(
                document_ids=case_history_data.documents,
                user_summary=case_history_data.summary
            )
            logger.info("AI-enhanced summary generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate AI summary, using original: {e}")
            enhanced_summary = case_history_data.summary

    # Create new case history with enhanced summary
    db_case_history = CaseHistory(
        patient_id=patient_id,
        summary=enhanced_summary,
        documents=case_history_data.documents or []  # Store document IDs as JSON array
    )

    db.add(db_case_history)
    db.commit()
    db.refresh(db_case_history)

    # Process document IDs if provided
    case_history_documents = []
    if case_history_data.documents:
        for doc_id in case_history_data.documents:
            # Get the document from the FileDocument table
            file_document = db.query(FileDocument).filter(FileDocument.id == doc_id).first()
            if file_document:
                # Create a case history document record
                uploaded_by_role = UploadedBy.DOCTOR if current_user.role == UserRole.DOCTOR else (
                    UploadedBy.ADMIN if current_user.role == UserRole.ADMIN else UploadedBy.PATIENT
                )

                case_doc = Document(
                    case_history_id=db_case_history.id,
                    file_name=file_document.file_name,
                    size=file_document.size,
                    link=file_document.link,
                    uploaded_by=uploaded_by_role,
                    remark=file_document.remark
                )

                db.add(case_doc)
                case_history_documents.append(case_doc)

                # Update the file document with the case history ID and type
                file_document.entity_id = db_case_history.id
                file_document.document_type = DocumentType.CASE_HISTORY

        if case_history_documents:
            db.commit()
            for doc in case_history_documents:
                db.refresh(doc)

    # Get all documents for this case history
    all_documents = db.query(Document).filter(
        Document.case_history_id == db_case_history.id
    ).all()

    # Enhance documents with download links
    enhanced_documents = enhance_case_history_documents(all_documents)

    # Construct response
    return CaseHistoryResponse(
        id=db_case_history.id,
        patient_id=db_case_history.patient_id,
        summary=db_case_history.summary,
        documents=db_case_history.documents,
        created_at=db_case_history.created_at,
        updated_at=db_case_history.updated_at,
        document_files=[DocumentResponse(**doc) for doc in enhanced_documents]
    )

@router.put("/{patient_id}/case-history", response_model=CaseHistoryResponse)
@standardize_response
async def update_case_history(
    patient_id: str,
    case_history_data: CaseHistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Update a case history for a patient
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR

    # For patients, we need to check if the user_entity_id is the patient_id
    # or if the user has a relation to this patient (1:n relationship)
    is_patient_owner = False
    if current_user.role == UserRole.PATIENT:
        if user_entity_id == patient_id:
            is_patient_owner = True
        else:
            # Check if the user has a relation to this patient
            from app.models.mapping import UserPatientRelation
            relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id,
                UserPatientRelation.patient_id == patient_id
            ).first()
            is_patient_owner = relation is not None

    # For doctors, check if they are treating this patient
    doctor_treating_patient = False
    if is_doctor:
        # Check if there's a doctor-patient mapping
        doctor = db.query(Doctor).filter(Doctor.id == user_entity_id).first()
        if doctor:
            mapping = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.doctor_id == doctor.id,
                DoctorPatientMapping.patient_id == patient_id
            ).first()
            doctor_treating_patient = mapping is not None

    if not (is_admin or doctor_treating_patient or is_patient_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Invalid entity ID for this user",
                error_code=ErrorCode.AUTH_004
            )
        )
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Get the most recent case history
    case_history = db.query(CaseHistory).filter(
        CaseHistory.patient_id == patient_id
    ).order_by(CaseHistory.created_at.desc()).first()

    if not case_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Case history not found for this patient",
                error_code=ErrorCode.RES_001
            )
        )

    # Generate AI-enhanced summary if both summary and documents are being updated
    enhanced_summary = case_history_data.summary
    if (case_history_data.summary is not None and
        case_history_data.documents is not None and
        case_history_data.documents):
        try:
            logger.info(f"Generating AI-enhanced summary for updated case history with {len(case_history_data.documents)} documents")
            enhanced_summary = await document_processor.generate_case_history_summary(
                document_ids=case_history_data.documents,
                user_summary=case_history_data.summary
            )
            logger.info("AI-enhanced summary generated successfully for update")
        except Exception as e:
            logger.error(f"Failed to generate AI summary for update, using original: {e}")
            enhanced_summary = case_history_data.summary

    # Update case history fields
    if case_history_data.summary is not None:
        case_history.summary = enhanced_summary

    if case_history_data.documents is not None:
        case_history.documents = case_history_data.documents

    db.commit()
    db.refresh(case_history)

    # Get documents for this case history
    documents = db.query(Document).filter(
        Document.case_history_id == case_history.id
    ).all()

    # Enhance documents with download links
    enhanced_documents = enhance_case_history_documents(documents)

    # Construct response
    return CaseHistoryResponse(
        id=case_history.id,
        patient_id=case_history.patient_id,
        summary=case_history.summary,
        documents=case_history.documents,
        created_at=case_history.created_at,
        updated_at=case_history.updated_at,
        document_files=[DocumentResponse(**doc) for doc in enhanced_documents]
    )

@router.get("/{patient_id}/documents")
@standardize_response
async def get_patient_documents(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Get all existing documents for a patient across all case histories

    Returns only existing documents. If no case histories or documents exist, returns an empty list.
    """
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            # Try to find patient by user_id
            user = db.query(User).filter(User.id == patient_id).first()
            if user and user.role == UserRole.PATIENT:
                # Get patient by user_id
                patient = db.query(Patient).filter(Patient.user_id == user.id).first()

                # If not found, try to get patient by profile_id
                if not patient and user.profile_id:
                    patient = db.query(Patient).filter(Patient.id == user.profile_id).first()

                if patient:
                    patient_id = patient.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=create_error_response(
                            status_code=status.HTTP_404_NOT_FOUND,
                            message="Patient not found",
                            error_code=ErrorCode.RES_001
                        )
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=create_error_response(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message="Patient not found",
                        error_code=ErrorCode.RES_001
                    )
                )

        # Check if current user is authorized to view this patient's documents
        is_admin = current_user.role == UserRole.ADMIN
        is_doctor = current_user.role == UserRole.DOCTOR

        # For patients, check if the user has a relation to this patient (1:n relationship)
        # The user_entity_id should be the patient_id they want to access
        is_patient_owner = False
        if current_user.role == UserRole.PATIENT:
            # Check if the user has a relation to this patient
            # The user_entity_id should match the patient_id they're trying to access
            if user_entity_id == patient_id:
                # Verify that this user actually has a relation to this patient
                from app.models.mapping import UserPatientRelation
                relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == patient_id
                ).first()
                is_patient_owner = relation is not None

        # For doctors, check if they are treating this patient
        doctor_treating_patient = False
        if is_doctor:
            # Check if there's a doctor-patient mapping
            doctor = db.query(Doctor).filter(Doctor.id == user_entity_id).first()
            if doctor:
                mapping = db.query(DoctorPatientMapping).filter(
                    DoctorPatientMapping.doctor_id == doctor.id,
                    DoctorPatientMapping.patient_id == patient_id
                ).first()
                doctor_treating_patient = mapping is not None

        if not (is_admin or doctor_treating_patient or is_patient_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not authorized to view this patient's documents",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get all case histories for this patient
        case_histories = db.query(CaseHistory).filter(
            CaseHistory.patient_id == patient_id
        ).all()

        # Get all documents across all case histories
        all_documents = []
        for case_history in case_histories:
            documents = db.query(Document).filter(
                Document.case_history_id == case_history.id
            ).all()
            all_documents.extend(documents)

        # Enhance documents with download links
        enhanced_documents = enhance_case_history_documents(all_documents)

        return {
            "documents": [DocumentResponse(**doc) for doc in enhanced_documents],
            "total": len(enhanced_documents)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )

@router.get("/{patient_id}/reports")
@standardize_response
async def get_patient_reports(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Get all existing reports for a patient with complete report information including documents

    Returns only existing reports for the patient. If no reports exist, returns an empty list.
    Each report includes description, updated_at, and report_documents with download links.
    """
    try:
        # Check if patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            # Try to find patient by user_id
            user = db.query(User).filter(User.id == patient_id).first()
            if user and user.role == UserRole.PATIENT:
                # Get patient by user_id
                patient = db.query(Patient).filter(Patient.user_id == user.id).first()

                # If not found, try to get patient by profile_id
                if not patient and user.profile_id:
                    patient = db.query(Patient).filter(Patient.id == user.profile_id).first()

                if patient:
                    patient_id = patient.id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=create_error_response(
                            status_code=status.HTTP_404_NOT_FOUND,
                            message="Patient not found",
                            error_code=ErrorCode.RES_001
                        )
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=create_error_response(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message="Patient not found",
                        error_code=ErrorCode.RES_001
                    )
                )

        # Check if current user is authorized to view this patient's reports
        is_admin = current_user.role == UserRole.ADMIN
        is_doctor = current_user.role == UserRole.DOCTOR

        # For patients, check if the user has a relation to this patient (1:n relationship)
        # The user_entity_id should be the patient_id they want to access
        is_patient_owner = False
        if current_user.role == UserRole.PATIENT:
            # Check if the user has a relation to this patient
            # The user_entity_id should match the patient_id they're trying to access
            if user_entity_id == patient_id:
                # Verify that this user actually has a relation to this patient
                relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == patient_id
                ).first()
                is_patient_owner = relation is not None

        # For doctors, check if they are treating this patient
        doctor_treating_patient = False
        if is_doctor:
            # Check if there's a doctor-patient mapping
            doctor = db.query(Doctor).filter(Doctor.id == user_entity_id).first()
            if doctor:
                mapping = db.query(DoctorPatientMapping).filter(
                    DoctorPatientMapping.doctor_id == doctor.id,
                    DoctorPatientMapping.patient_id == patient_id
                ).first()
                doctor_treating_patient = mapping is not None

        if not (is_admin or doctor_treating_patient or is_patient_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not authorized to view this patient's reports",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get all report mappings for this patient
        report_mappings = db.query(PatientReportMapping).filter(
            PatientReportMapping.patient_id == patient_id
        ).all()

        # Get all reports with complete information
        reports = []
        for mapping in report_mappings:
            report = db.query(Report).filter(Report.id == mapping.report_id).first()
            if report:
                # Get report documents for this report
                report_documents = db.query(ReportDocument).filter(
                    ReportDocument.report_id == report.id
                ).all()

                # Enhance report documents with download links
                enhanced_report_documents = enhance_report_documents(report_documents)

                # Create complete ReportResponse object
                complete_report = ReportResponse(
                    id=report.id,
                    title=report.title,
                    description=report.description,
                    report_type=report.report_type,
                    created_at=report.created_at,
                    updated_at=report.updated_at,
                    report_documents=[ReportDocumentResponse(**doc) for doc in enhanced_report_documents]
                )
                reports.append(complete_report)

        # Construct response with complete report objects
        return {
            "reports": reports,
            "total": len(reports)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )

@router.get("/{patient_id}/reports/{report_id}", response_model=ReportResponse)
@standardize_response
async def get_patient_report(
    patient_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Get a specific report for a patient
    """
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if current user is authorized to view this patient's reports
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR

    # For patients, check if the user has a relation to this patient (1:n relationship)
    # The user_entity_id should be the patient_id they want to access
    is_patient_owner = False
    if current_user.role == UserRole.PATIENT:
        # Check if the user has a relation to this patient
        # The user_entity_id should match the patient_id they're trying to access
        if user_entity_id == patient_id:
            # Verify that this user actually has a relation to this patient
            relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id,
                UserPatientRelation.patient_id == patient_id
            ).first()
            is_patient_owner = relation is not None

    # For doctors, check if they are treating this patient
    doctor_treating_patient = False
    if is_doctor:
        # Check if there's a doctor-patient mapping
        doctor = db.query(Doctor).filter(Doctor.id == user_entity_id).first()
        if doctor:
            mapping = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.doctor_id == doctor.id,
                DoctorPatientMapping.patient_id == patient_id
            ).first()
            doctor_treating_patient = mapping is not None

    if not (is_admin or doctor_treating_patient or is_patient_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not authorized to view this patient's reports",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Check if report exists and belongs to this patient
    mapping = db.query(PatientReportMapping).filter(
        PatientReportMapping.patient_id == patient_id,
        PatientReportMapping.report_id == report_id
    ).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Report not found for this patient",
                error_code=ErrorCode.RES_001
            )
        )

    # Get the report
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Report not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Get report documents
    report_documents = db.query(ReportDocument).filter(
        ReportDocument.report_id == report_id
    ).all()

    # Construct response
    return ReportResponse(
        id=report.id,
        title=report.title,
        description=report.description,
        report_type=report.report_type,
        created_at=report.created_at,
        updated_at=report.updated_at,
        report_documents=[ReportDocumentResponse.model_validate(doc) for doc in report_documents]
    )

@router.post("/{patient_id}/reports", response_model=ReportResponse)
@standardize_response
async def create_patient_report(
    patient_id: str,
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Create a new report for a patient
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR

    # For patients, check if the user has a relation to this patient (1:n relationship)
    # The user_entity_id should be the patient_id they want to access
    is_patient_owner = False
    if current_user.role == UserRole.PATIENT:
        # Check if the user has a relation to this patient
        # The user_entity_id should match the patient_id they're trying to access
        if user_entity_id == patient_id:
            # Verify that this user actually has a relation to this patient
            relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id,
                UserPatientRelation.patient_id == patient_id
            ).first()
            is_patient_owner = relation is not None

    if not (is_admin or is_doctor or is_patient_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Create new report
    db_report = Report(
        title=report_data.title,
        description=report_data.description,
        report_type=report_data.report_type
    )

    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # Create patient-report mapping
    db_mapping = PatientReportMapping(
        patient_id=patient_id,
        report_id=db_report.id
    )

    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)

    # Process document IDs if provided
    report_documents = []
    if report_data.document_ids:
        for doc_id in report_data.document_ids:
            # Get the document from the FileDocument table
            file_document = db.query(FileDocument).filter(FileDocument.id == doc_id).first()
            if file_document:
                # Create a report document record
                report_doc = ReportDocument(
                    report_id=db_report.id,
                    file_name=file_document.file_name,
                    size=file_document.size,
                    link=file_document.link,
                    uploaded_by=current_user.id,
                    remark=file_document.remark
                )

                db.add(report_doc)
                report_documents.append(report_doc)

                # Update the file document with the report ID and type
                file_document.entity_id = db_report.id
                file_document.document_type = DocumentType.REPORT

        if report_documents:
            db.commit()
            for doc in report_documents:
                db.refresh(doc)

    # Get all report documents
    all_report_documents = db.query(ReportDocument).filter(
        ReportDocument.report_id == db_report.id
    ).all()

    # Enhance report documents with download links
    enhanced_report_documents = enhance_report_documents(all_report_documents)

    # Construct response
    return ReportResponse(
        id=db_report.id,
        title=db_report.title,
        description=db_report.description,
        report_type=db_report.report_type,
        created_at=db_report.created_at,
        updated_at=db_report.updated_at,
        report_documents=[ReportDocumentResponse(**doc) for doc in enhanced_report_documents]
    )

@router.put("/{patient_id}/reports/{report_id}", response_model=ReportResponse)
@standardize_response
async def update_patient_report(
    patient_id: str,
    report_id: str,
    report_data: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Update a report for a patient
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR

    # For patients, check if the user has a relation to this patient (1:n relationship)
    # The user_entity_id should be the patient_id they want to access
    is_patient_owner = False
    if current_user.role == UserRole.PATIENT:
        # Check if the user has a relation to this patient
        # The user_entity_id should match the patient_id they're trying to access
        if user_entity_id == patient_id:
            # Verify that this user actually has a relation to this patient
            relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id,
                UserPatientRelation.patient_id == patient_id
            ).first()
            is_patient_owner = relation is not None

    if not (is_admin or is_doctor or is_patient_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )
    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if report exists and belongs to this patient
    mapping = db.query(PatientReportMapping).filter(
        PatientReportMapping.patient_id == patient_id,
        PatientReportMapping.report_id == report_id
    ).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Report not found for this patient",
                error_code=ErrorCode.RES_001
            )
        )

    # Get the report
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Report not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Update report fields
    if report_data.title is not None:
        report.title = report_data.title

    if report_data.description is not None:
        report.description = report_data.description

    if report_data.report_type is not None:
        report.report_type = report_data.report_type

    db.commit()
    db.refresh(report)

    # Get report documents
    report_documents = db.query(ReportDocument).filter(
        ReportDocument.report_id == report_id
    ).all()

    # Construct response
    return ReportResponse(
        id=report.id,
        title=report.title,
        description=report.description,
        report_type=report.report_type,
        created_at=report.created_at,
        updated_at=report.updated_at,
        report_documents=[ReportDocumentResponse.model_validate(doc) for doc in report_documents]
    )





@router.post("/admin/create", response_model=PatientResponse)
@standardize_response
async def admin_create_patient(
    patient_data: AdminPatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
) -> Any:
    """
    Create a new patient with user account (admin only)
    """
    try:
        # Check if user with this email already exists
        db_user = db.query(User).filter(User.email == patient_data.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Email already registered",
                    error_code=ErrorCode.RES_002
                )
            )

        # Create patient profile
        db_patient = Patient(
            name=patient_data.name,
            dob=patient_data.dob,
            gender=patient_data.gender,
            contact=patient_data.contact,
            photo=patient_data.photo
        )

        db.add(db_patient)
        db.flush()  # Flush to get the ID

        # Create user account
        hashed_password = get_password_hash(patient_data.password)
        db_user = User(
            email=patient_data.email,
            hashed_password=hashed_password,
            name=patient_data.user_name,
            role=UserRole.PATIENT,
            contact=patient_data.user_contact,
            profile_id=db_patient.id
        )

        db.add(db_user)
        db.flush()  # Flush to get the ID

        # Link the patient to the user
        db_patient.user_id = db_user.id

        # Create user-patient relation
        relation = UserPatientRelation(
            user_id=db_user.id,
            patient_id=db_patient.id,
            relation=patient_data.relation_type
        )

        db.add(relation)
        db.commit()
        db.refresh(db_patient)

        return PatientResponse(
            id=db_patient.id,
            name=db_patient.name,
            dob=db_patient.dob,
            gender=db_patient.gender,
            contact=db_patient.contact,
            photo=db_patient.photo,
            created_at=db_patient.created_at,
            updated_at=db_patient.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"An error occurred: {str(e)}",
                error_code=ErrorCode.SRV_001
            )
        )