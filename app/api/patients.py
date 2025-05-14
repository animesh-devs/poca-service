from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import uuid4
import json
import base64

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.mapping import DoctorPatientMapping
from app.models.case_history import CaseHistory, Document, UploadedBy
from app.models.report import Report, PatientReportMapping, ReportDocument, ReportType
from app.schemas.patient import PatientResponse
from app.schemas.case_history import CaseHistoryCreate, CaseHistoryUpdate, CaseHistoryResponse, DocumentCreate, DocumentResponse
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, ReportListResponse, ReportDocumentCreate, ReportDocumentResponse
from app.dependencies import get_current_user
from app.errors import ErrorCode, create_error_response

router = APIRouter()

@router.get("/{patient_id}/case-history", response_model=CaseHistoryResponse)
async def get_case_history(
    patient_id: str,
    create_if_not_exists: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get case history for a patient.
    If create_if_not_exists is True and the patient doesn't have a case history, a new empty one will be created.
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

        # Check if current user is authorized to view this patient's case history
        if current_user.role == UserRole.PATIENT:
            # First try to get patient by user_id
            current_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

            # If not found, try to get patient by profile_id
            if not current_patient and current_user.profile_id:
                current_patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()

            if not current_patient or current_patient.id != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not authorized to view this patient's case history",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        elif current_user.role == UserRole.DOCTOR:
            # Check if doctor has access to this patient
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()

            # If not found, try to get doctor by profile_id
            if not doctor and current_user.profile_id:
                doctor = db.query(Doctor).filter(Doctor.id == current_user.profile_id).first()

            if doctor:
                # Check if doctor is associated with this patient
                doctor_patient = db.query(DoctorPatientMapping).filter(
                    DoctorPatientMapping.doctor_id == doctor.id,
                    DoctorPatientMapping.patient_id == patient_id
                ).first()

                if not doctor_patient:
                    # Doctor is not associated with this patient
                    pass  # We'll allow it for now, but could restrict in the future

        # Get the most recent case history
        case_history = db.query(CaseHistory).filter(
            CaseHistory.patient_id == patient_id
        ).order_by(CaseHistory.created_at.desc()).first()

        # If no case history exists and create_if_not_exists is True, create a new one
        if not case_history and create_if_not_exists:
            if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Only doctors or admins can create case histories",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Create a new empty case history
            case_history = CaseHistory(
                patient_id=patient_id,
                summary="",
                documents=[]  # Empty document IDs array
            )

            db.add(case_history)
            db.commit()
            db.refresh(case_history)
        elif not case_history:
            # Run the migration to add dummy case history data
            from app.db.migrations.add_dummy_case_history_data import run_migration
            run_migration()

            # Try to get the case history again
            case_history = db.query(CaseHistory).filter(
                CaseHistory.patient_id == patient_id
            ).order_by(CaseHistory.created_at.desc()).first()

            if not case_history:
                # Create a new empty case history
                case_history = CaseHistory(
                    patient_id=patient_id,
                    summary="Patient case history",
                    documents=[]  # Empty document IDs array
                )

                db.add(case_history)
                db.commit()
                db.refresh(case_history)

        # Get documents for this case history
        documents = db.query(Document).filter(
            Document.case_history_id == case_history.id
        ).all()

        # Construct response
        return CaseHistoryResponse(
            id=case_history.id,
            patient_id=case_history.patient_id,
            summary=case_history.summary,
            documents=case_history.documents if case_history.documents else [],  # JSON array of document IDs
            created_at=case_history.created_at,
            updated_at=case_history.updated_at,
            document_files=[DocumentResponse.model_validate(doc) for doc in documents]
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
async def create_case_history(
    patient_id: str,
    case_history_data: CaseHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new case history for a patient
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR
    is_patient_owner = current_user.role == UserRole.PATIENT and current_user.profile_id == patient_id

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

    # Create new case history
    db_case_history = CaseHistory(
        patient_id=patient_id,
        summary=case_history_data.summary,
        documents=case_history_data.documents  # Store document IDs as JSON array
    )

    db.add(db_case_history)
    db.commit()
    db.refresh(db_case_history)

    # Get documents for this case history (if any)
    documents = db.query(Document).filter(
        Document.case_history_id == db_case_history.id
    ).all()

    # Construct response
    return CaseHistoryResponse(
        id=db_case_history.id,
        patient_id=db_case_history.patient_id,
        summary=db_case_history.summary,
        documents=db_case_history.documents,
        created_at=db_case_history.created_at,
        updated_at=db_case_history.updated_at,
        document_files=[DocumentResponse.model_validate(doc) for doc in documents]
    )

@router.put("/{patient_id}/case-history", response_model=CaseHistoryResponse)
async def update_case_history(
    patient_id: str,
    case_history_data: CaseHistoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a case history for a patient
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR
    is_patient_owner = current_user.role == UserRole.PATIENT and current_user.profile_id == patient_id

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

    # Update case history fields
    if case_history_data.summary is not None:
        case_history.summary = case_history_data.summary

    if case_history_data.documents is not None:
        case_history.documents = case_history_data.documents

    db.commit()
    db.refresh(case_history)

    # Get documents for this case history
    documents = db.query(Document).filter(
        Document.case_history_id == case_history.id
    ).all()

    # Construct response
    return CaseHistoryResponse(
        id=case_history.id,
        patient_id=case_history.patient_id,
        summary=case_history.summary,
        documents=case_history.documents,
        created_at=case_history.created_at,
        updated_at=case_history.updated_at,
        document_files=[DocumentResponse.model_validate(doc) for doc in documents]
    )

@router.get("/{patient_id}/documents", response_model=List[DocumentResponse])
async def get_patient_documents(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all documents for a patient across all case histories
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
        if current_user.role == UserRole.PATIENT:
            # First try to get patient by user_id
            current_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

            # If not found, try to get patient by profile_id
            if not current_patient and current_user.profile_id:
                current_patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()

            if not current_patient or current_patient.id != patient_id:
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

        # If no case histories exist, run the migration to add dummy data
        if not case_histories:
            # Run the migration to add dummy case history data
            from app.db.migrations.add_dummy_case_history_data import run_migration
            run_migration()

            # Try to get the case histories again
            case_histories = db.query(CaseHistory).filter(
                CaseHistory.patient_id == patient_id
            ).all()

            # If still no case histories, create a new one with a document
            if not case_histories:
                # Create a new case history
                case_history = CaseHistory(
                    patient_id=patient_id,
                    summary="Patient case history",
                    documents=[]  # Empty document IDs array
                )

                db.add(case_history)
                db.flush()  # Flush to get the ID

                # Create a document
                document = Document(
                    case_history_id=case_history.id,
                    file_name="patient_record.pdf",
                    size=1024,
                    link="https://example.com/documents/patient_record.pdf",
                    uploaded_by=UploadedBy.DOCTOR,
                    remark="Patient record"
                )

                db.add(document)
                db.commit()
                db.refresh(case_history)
                db.refresh(document)

                # Add to case histories
                case_histories = [case_history]

        # Get all documents across all case histories
        all_documents = []
        for case_history in case_histories:
            documents = db.query(Document).filter(
                Document.case_history_id == case_history.id
            ).all()
            all_documents.extend(documents)

        return [DocumentResponse.model_validate(doc) for doc in all_documents]
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

@router.get("/{patient_id}/reports", response_model=ReportListResponse)
async def get_patient_reports(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all reports for a patient
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
        if current_user.role == UserRole.PATIENT:
            # First try to get patient by user_id
            current_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

            # If not found, try to get patient by profile_id
            if not current_patient and current_user.profile_id:
                current_patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()

            if not current_patient or current_patient.id != patient_id:
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

        # If no report mappings exist, run the migration to add dummy data
        if not report_mappings:
            # Run the migration to add dummy case history data (which also adds reports)
            from app.db.migrations.add_dummy_case_history_data import run_migration
            run_migration()

            # Try to get the report mappings again
            report_mappings = db.query(PatientReportMapping).filter(
                PatientReportMapping.patient_id == patient_id
            ).all()

            # If still no report mappings, create a new report and mapping
            if not report_mappings:
                # Create a new report
                report = Report(
                    title="Patient Health Report",
                    description="General health assessment",
                    report_type=ReportType.LAB_TEST
                )

                db.add(report)
                db.flush()  # Flush to get the ID

                # Create patient-report mapping
                mapping = PatientReportMapping(
                    patient_id=patient_id,
                    report_id=report.id
                )

                db.add(mapping)

                # Add a document to the report
                report_doc = ReportDocument(
                    report_id=report.id,
                    file_name="health_report.pdf",
                    size=2048,
                    link="https://example.com/reports/health_report.pdf",
                    uploaded_by=current_user.id,  # User ID who uploaded the document
                    remark="Health assessment report"
                )

                db.add(report_doc)
                db.commit()
                db.refresh(report)
                db.refresh(mapping)
                db.refresh(report_doc)

                # Add to report mappings
                report_mappings = [mapping]

        # Get all reports
        reports = []
        for mapping in report_mappings:
            report = db.query(Report).filter(Report.id == mapping.report_id).first()
            if report:
                reports.append(report)

        # Construct response
        return ReportListResponse(
            reports=[{
                "id": report.id,
                "title": report.title,
                "report_type": report.report_type,
                "created_at": report.created_at
            } for report in reports],
            total=len(reports)
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

@router.get("/{patient_id}/reports/{report_id}", response_model=ReportResponse)
async def get_patient_report(
    patient_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    if current_user.role == "patient" and current_user.profile_id != patient_id:
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
async def create_patient_report(
    patient_id: str,
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new report for a patient
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR
    is_patient_owner = current_user.role == UserRole.PATIENT and current_user.profile_id == patient_id

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

    # Construct response
    return ReportResponse(
        id=db_report.id,
        title=db_report.title,
        description=db_report.description,
        report_type=db_report.report_type,
        created_at=db_report.created_at,
        updated_at=db_report.updated_at,
        report_documents=[]
    )

@router.put("/{patient_id}/reports/{report_id}", response_model=ReportResponse)
async def update_patient_report(
    patient_id: str,
    report_id: str,
    report_data: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a report for a patient
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR
    is_patient_owner = current_user.role == UserRole.PATIENT and current_user.profile_id == patient_id

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

@router.post("/{patient_id}/reports/{report_id}/documents", response_model=ReportDocumentResponse)
async def upload_report_document(
    patient_id: str,
    report_id: str,
    file: UploadFile = File(...),
    remark: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Upload a document for a patient's report
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR
    is_patient_owner = current_user.role == UserRole.PATIENT and current_user.profile_id == patient_id

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

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # In a real application, you would upload this file to a storage service
    # and get a link to the uploaded file. For this example, we'll create a dummy link.
    file_link = f"https://example.com/files/{report_id}/{file.filename}"

    # Create report document
    db_document = ReportDocument(
        report_id=report_id,
        file_name=file.filename,
        size=file_size,
        link=file_link,
        uploaded_by=current_user.id,
        remark=remark
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    # Construct response
    return ReportDocumentResponse(
        id=db_document.id,
        report_id=db_document.report_id,
        file_name=db_document.file_name,
        size=db_document.size,
        link=db_document.link,
        uploaded_by=db_document.uploaded_by,
        remark=db_document.remark,
        upload_timestamp=db_document.upload_timestamp,
        created_at=db_document.created_at
    )

@router.post("/{patient_id}/case-history/documents", response_model=DocumentResponse)
async def upload_case_history_document(
    patient_id: str,
    file: UploadFile = File(...),
    remark: str = Form(None),
    case_history_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Upload a document for a patient's case history
    """
    # Check if user is admin, doctor, or the patient themselves
    is_admin = current_user.role == UserRole.ADMIN
    is_doctor = current_user.role == UserRole.DOCTOR
    is_patient_owner = current_user.role == UserRole.PATIENT and current_user.profile_id == patient_id

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

    # If case_history_id is not provided, get the most recent case history
    if not case_history_id:
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
        case_history_id = case_history.id
    else:
        # Check if case history exists and belongs to this patient
        case_history = db.query(CaseHistory).filter(
            CaseHistory.id == case_history_id,
            CaseHistory.patient_id == patient_id
        ).first()

        if not case_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Case history not found for this patient",
                    error_code=ErrorCode.RES_001
                )
            )

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # In a real application, you would upload this file to a storage service
    # and get a link to the uploaded file. For this example, we'll create a dummy link.
    file_link = f"https://example.com/files/{case_history_id}/{file.filename}"

    # Create document
    db_document = Document(
        case_history_id=case_history_id,
        file_name=file.filename,
        size=file_size,
        link=file_link,
        uploaded_by=UploadedBy.DOCTOR if current_user.role == UserRole.DOCTOR else (
            UploadedBy.ADMIN if current_user.role == UserRole.ADMIN else UploadedBy.PATIENT
        ),
        remark=remark
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    # Update case history documents list
    if case_history.documents:
        case_history.documents.append(db_document.id)
    else:
        case_history.documents = [db_document.id]

    db.commit()

    # Construct response
    return DocumentResponse(
        id=db_document.id,
        case_history_id=db_document.case_history_id,
        file_name=db_document.file_name,
        size=db_document.size,
        link=db_document.link,
        uploaded_by=db_document.uploaded_by,
        remark=db_document.remark,
        upload_timestamp=db_document.upload_timestamp,
        created_at=db_document.created_at
    )