from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from uuid import uuid4
import json
import base64

from app.db.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.case_history import CaseHistory, Document, UploadedBy
from app.models.report import Report, PatientReportMapping, ReportDocument, ReportType
from app.schemas.patient import PatientResponse
from app.schemas.case_history import CaseHistoryCreate, CaseHistoryUpdate, CaseHistoryResponse, DocumentCreate, DocumentResponse
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, ReportListResponse, ReportDocumentCreate, ReportDocumentResponse
from app.dependencies import get_current_user, get_doctor_user, get_patient_user
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

    # Check if current user is authorized to view this patient's case history
    if current_user.role == "patient" and current_user.profile_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not authorized to view this patient's case history",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Get the most recent case history
    case_history = db.query(CaseHistory).filter(
        CaseHistory.patient_id == patient_id
    ).order_by(CaseHistory.created_at.desc()).first()

    # If no case history exists and create_if_not_exists is True, create a new one
    if not case_history and create_if_not_exists:
        if current_user.role not in ["doctor", "admin"]:
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
        documents=case_history.documents,  # JSON array of document IDs
        created_at=case_history.created_at,
        updated_at=case_history.updated_at,
        document_files=[DocumentResponse.model_validate(doc) for doc in documents]
    )

@router.post("/{patient_id}/case-history", response_model=CaseHistoryResponse)
async def create_case_history(
    patient_id: str,
    case_history_data: CaseHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_doctor_user)
) -> Any:
    """
    Create a new case history for a patient
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
    current_user: User = Depends(get_doctor_user)
) -> Any:
    """
    Update a case history for a patient
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

    # Check if current user is authorized to view this patient's documents
    if current_user.role == "patient" and current_user.profile_id != patient_id:
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

    return [DocumentResponse.model_validate(doc) for doc in all_documents]

@router.get("/{patient_id}/reports", response_model=ReportListResponse)
async def get_patient_reports(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all reports for a patient
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

    # Get all report mappings for this patient
    report_mappings = db.query(PatientReportMapping).filter(
        PatientReportMapping.patient_id == patient_id
    ).all()

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
    current_user: User = Depends(get_doctor_user)
) -> Any:
    """
    Create a new report for a patient
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
    current_user: User = Depends(get_doctor_user)
) -> Any:
    """
    Update a report for a patient
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
    current_user: User = Depends(get_doctor_user)
) -> Any:
    """
    Upload a document for a patient's report
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
