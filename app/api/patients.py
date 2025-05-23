from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

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
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, ReportListResponse, ReportDocumentResponse
from app.dependencies import get_current_user, get_admin_user, get_user_entity_id
from app.api.auth import get_password_hash
from app.errors import ErrorCode, create_error_response

router = APIRouter()



@router.get("/{patient_id}/case-history", response_model=CaseHistoryResponse)
async def get_case_history(
    patient_id: str,
    create_if_not_exists: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Get the most recent case history for a patient

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

        # If no case history exists and create_if_not_exists is True, create one
        if not case_history and create_if_not_exists:
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
                uploaded_by=UploadedBy.DOCTOR if is_doctor else (UploadedBy.ADMIN if is_admin else UploadedBy.PATIENT),
                remark="Patient record"
            )

            db.add(document)
            db.commit()
            db.refresh(case_history)
            db.refresh(document)
        elif not case_history:
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
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Create a new case history for a patient
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

    # Create new case history
    db_case_history = CaseHistory(
        patient_id=patient_id,
        summary=case_history_data.summary,
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

    # Construct response
    return CaseHistoryResponse(
        id=db_case_history.id,
        patient_id=db_case_history.patient_id,
        summary=db_case_history.summary,
        documents=db_case_history.documents,
        created_at=db_case_history.created_at,
        updated_at=db_case_history.updated_at,
        document_files=[DocumentResponse.model_validate(doc) for doc in all_documents]
    )

@router.put("/{patient_id}/case-history", response_model=CaseHistoryResponse)
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
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
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
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
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
            # First try to get patient by profile_id (preferred way)
            if current_user.profile_id:
                current_patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()
            else:
                # Try to find patient by user_id
                current_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

                # If not found, try to find by direct ID match
                if not current_patient:
                    current_patient = db.query(Patient).filter(Patient.id == current_user.id).first()

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

    # Construct response
    return ReportResponse(
        id=db_report.id,
        title=db_report.title,
        description=db_report.description,
        report_type=db_report.report_type,
        created_at=db_report.created_at,
        updated_at=db_report.updated_at,
        report_documents=[ReportDocumentResponse.model_validate(doc) for doc in all_report_documents]
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





@router.post("/admin/create", response_model=PatientResponse)
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