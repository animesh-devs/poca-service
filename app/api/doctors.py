from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.db.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.mapping import HospitalDoctorMapping, DoctorPatientMapping
from app.schemas.doctor import DoctorUpdate, DoctorResponse, DoctorListResponse, DoctorListItem
from app.dependencies import get_current_user, get_admin_user, get_doctor_user
from app.errors import ErrorCode, create_error_response

router = APIRouter()

@router.get("", response_model=DoctorListResponse)
async def get_doctors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all doctors
    """
    doctors = db.query(Doctor).offset(skip).limit(limit).all()
    total = db.query(Doctor).count()
    
    return {
        "doctors": [DoctorListItem.model_validate(doctor) for doctor in doctors],
        "total": total
    }

@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get doctor by ID
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Doctor not found",
                error_code=ErrorCode.RES_001
            )
        )
    
    return doctor

@router.put("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: str,
    doctor_data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update doctor profile
    """
    # Check if the current user is an admin or the doctor being updated
    is_admin = current_user.role == "admin"
    is_doctor_owner = current_user.role == "doctor" and current_user.profile_id == doctor_id
    
    if not (is_admin or is_doctor_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )
    
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Doctor not found",
                error_code=ErrorCode.RES_001
            )
        )
    
    # Update doctor fields
    for field, value in doctor_data.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    
    db.commit()
    db.refresh(doctor)
    
    return doctor

@router.get("/{doctor_id}/patients", response_model=List[dict])
async def get_doctor_patients(
    doctor_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all patients for a doctor
    """
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Doctor not found",
                error_code=ErrorCode.RES_001
            )
        )
    
    # Check if the current user is an admin or the doctor
    is_admin = current_user.role == "admin"
    is_doctor_owner = current_user.role == "doctor" and current_user.profile_id == doctor_id
    
    if not (is_admin or is_doctor_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )
    
    # Get all patients mapped to this doctor
    from app.models.patient import Patient
    
    # Query for doctor-patient mappings
    mappings = db.query(DoctorPatientMapping).filter(
        DoctorPatientMapping.doctor_id == doctor_id
    ).offset(skip).limit(limit).all()
    
    # Get patient IDs from mappings
    patient_ids = [mapping.patient_id for mapping in mappings]
    
    # Query for patients
    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    
    # Return patient data
    return [
        {
            "id": patient.id,
            "name": patient.name,
            "gender": patient.gender,
            "contact": patient.contact,
            "photo": patient.photo
        }
        for patient in patients
    ]

@router.get("/{doctor_id}/hospitals", response_model=List[dict])
async def get_doctor_hospitals(
    doctor_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all hospitals for a doctor
    """
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Doctor not found",
                error_code=ErrorCode.RES_001
            )
        )
    
    # Get all hospitals mapped to this doctor
    from app.models.hospital import Hospital
    
    # Query for hospital-doctor mappings
    mappings = db.query(HospitalDoctorMapping).filter(
        HospitalDoctorMapping.doctor_id == doctor_id
    ).offset(skip).limit(limit).all()
    
    # Get hospital IDs from mappings
    hospital_ids = [mapping.hospital_id for mapping in mappings]
    
    # Query for hospitals
    hospitals = db.query(Hospital).filter(Hospital.id.in_(hospital_ids)).all()
    
    # Return hospital data
    return [
        {
            "id": hospital.id,
            "name": hospital.name,
            "address": hospital.address,
            "contact": hospital.contact
        }
        for hospital in hospitals
    ]
