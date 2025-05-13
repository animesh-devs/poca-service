from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.db.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.mapping import (
    HospitalDoctorMapping,
    HospitalPatientMapping,
    DoctorPatientMapping,
    UserPatientRelation
)
from app.schemas.mapping import (
    HospitalDoctorMappingCreate, HospitalDoctorMappingResponse,
    HospitalPatientMappingCreate, HospitalPatientMappingResponse,
    DoctorPatientMappingCreate, DoctorPatientMappingResponse,
    UserPatientRelationCreate, UserPatientRelationUpdate, UserPatientRelationResponse
)
from app.dependencies import get_current_user, get_admin_user, get_doctor_user, get_hospital_user
from app.errors import ErrorCode, create_error_response

router = APIRouter()

@router.post("/hospital-doctor", response_model=HospitalDoctorMappingResponse)
async def create_hospital_doctor_mapping(
    mapping_data: HospitalDoctorMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
) -> Any:
    """
    Create a mapping between a hospital and a doctor (admin only)
    """
    # Check if hospital exists
    hospital = db.query(Hospital).filter(Hospital.id == mapping_data.hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Hospital not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == mapping_data.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Doctor not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if mapping already exists
    existing_mapping = db.query(HospitalDoctorMapping).filter(
        HospitalDoctorMapping.hospital_id == mapping_data.hospital_id,
        HospitalDoctorMapping.doctor_id == mapping_data.doctor_id
    ).first()

    if existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Mapping already exists",
                error_code=ErrorCode.RES_002
            )
        )

    # Create new mapping
    db_mapping = HospitalDoctorMapping(**mapping_data.model_dump())

    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)

    return db_mapping

@router.post("/hospital-patient", response_model=HospitalPatientMappingResponse)
async def create_hospital_patient_mapping(
    mapping_data: HospitalPatientMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
) -> Any:
    """
    Create a mapping between a hospital and a patient (admin only)
    """
    # Check if hospital exists
    hospital = db.query(Hospital).filter(Hospital.id == mapping_data.hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Hospital not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == mapping_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if mapping already exists
    existing_mapping = db.query(HospitalPatientMapping).filter(
        HospitalPatientMapping.hospital_id == mapping_data.hospital_id,
        HospitalPatientMapping.patient_id == mapping_data.patient_id
    ).first()

    if existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Mapping already exists",
                error_code=ErrorCode.RES_002
            )
        )

    # Create new mapping
    db_mapping = HospitalPatientMapping(**mapping_data.model_dump())

    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)

    return db_mapping

@router.post("/doctor-patient", response_model=DoctorPatientMappingResponse)
async def create_doctor_patient_mapping(
    mapping_data: DoctorPatientMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
) -> Any:
    """
    Create a mapping between a doctor and a patient (admin only)
    """
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == mapping_data.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Doctor not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if patient exists
    patient = db.query(Patient).filter(Patient.id == mapping_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if mapping already exists
    existing_mapping = db.query(DoctorPatientMapping).filter(
        DoctorPatientMapping.doctor_id == mapping_data.doctor_id,
        DoctorPatientMapping.patient_id == mapping_data.patient_id
    ).first()

    if existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Mapping already exists",
                error_code=ErrorCode.RES_002
            )
        )

    # Create new mapping
    db_mapping = DoctorPatientMapping(**mapping_data.model_dump())

    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)

    return db_mapping

@router.delete("/hospital-doctor/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hospital_doctor_mapping(
    mapping_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a hospital-doctor mapping (admin only)
    """
    mapping = db.query(HospitalDoctorMapping).filter(HospitalDoctorMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Mapping not found",
                error_code=ErrorCode.RES_001
            )
        )

    db.delete(mapping)
    db.commit()

@router.delete("/hospital-patient/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hospital_patient_mapping(
    mapping_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a hospital-patient mapping (admin only)
    """
    mapping = db.query(HospitalPatientMapping).filter(HospitalPatientMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Mapping not found",
                error_code=ErrorCode.RES_001
            )
        )

    db.delete(mapping)
    db.commit()

@router.delete("/doctor-patient/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor_patient_mapping(
    mapping_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete a doctor-patient mapping (admin only)
    """
    mapping = db.query(DoctorPatientMapping).filter(DoctorPatientMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Mapping not found",
                error_code=ErrorCode.RES_001
            )
        )

    db.delete(mapping)
    db.commit()
