from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.db.database import get_db
from app.models.user import User
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.mapping import HospitalDoctorMapping, HospitalPatientMapping
from app.schemas.hospital import HospitalCreate, HospitalUpdate, HospitalResponse, HospitalListResponse, HospitalListItem
from app.schemas.doctor import DoctorListResponse, DoctorListItem
from app.schemas.patient import PatientListResponse, PatientListItem
from app.dependencies import get_current_user, get_admin_user, get_hospital_user
from app.errors import ErrorCode, create_error_response

router = APIRouter()

@router.post("", response_model=HospitalResponse)
async def create_hospital(
    hospital_data: HospitalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
) -> Any:
    """
    Create a new hospital (admin only)
    """
    # Check if hospital with this email already exists
    db_hospital = db.query(Hospital).filter(Hospital.email == hospital_data.email).first()
    if db_hospital:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Hospital with this email already exists",
                error_code=ErrorCode.RES_002
            )
        )

    # Create new hospital
    db_hospital = Hospital(**hospital_data.model_dump())

    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)

    return db_hospital

@router.get("", response_model=HospitalListResponse)
async def get_hospitals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all hospitals
    """
    hospitals = db.query(Hospital).offset(skip).limit(limit).all()
    total = db.query(Hospital).count()

    return {
        "hospitals": [HospitalListItem.model_validate(hospital) for hospital in hospitals],
        "total": total
    }

@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get hospital by ID
    """
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Hospital not found",
                error_code=ErrorCode.RES_001
            )
        )

    return hospital

@router.put("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(
    hospital_id: str,
    hospital_data: HospitalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update hospital
    """
    # Only admins or the hospital itself can update
    if current_user.role != "admin" and (current_user.role != "hospital" or current_user.profile_id != hospital_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Hospital not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Update hospital fields
    for field, value in hospital_data.model_dump(exclude_unset=True).items():
        setattr(hospital, field, value)

    db.commit()
    db.refresh(hospital)

    return hospital

@router.delete("/{hospital_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hospital(
    hospital_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Delete hospital (admin only)
    """
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Hospital not found",
                error_code=ErrorCode.RES_001
            )
        )

    db.delete(hospital)
    db.commit()

@router.get("/{hospital_id}/doctors", response_model=DoctorListResponse)
async def get_hospital_doctors(
    hospital_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all doctors in a hospital
    """
    # Check if hospital exists
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Hospital not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Get all doctors mapped to this hospital
    doctor_mappings = db.query(HospitalDoctorMapping).filter(
        HospitalDoctorMapping.hospital_id == hospital_id
    ).offset(skip).limit(limit).all()

    doctor_ids = [mapping.doctor_id for mapping in doctor_mappings]
    doctors = db.query(Doctor).filter(Doctor.id.in_(doctor_ids)).all()
    total = db.query(HospitalDoctorMapping).filter(
        HospitalDoctorMapping.hospital_id == hospital_id
    ).count()

    return {
        "doctors": [DoctorListItem.model_validate(doctor) for doctor in doctors],
        "total": total
    }

@router.get("/{hospital_id}/patients", response_model=PatientListResponse)
async def get_hospital_patients(
    hospital_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all patients in a hospital
    """
    # Only admins, the hospital itself, or doctors in the hospital can view patients
    is_doctor_in_hospital = False
    if current_user.role == "doctor":
        doctor_mapping = db.query(HospitalDoctorMapping).filter(
            HospitalDoctorMapping.hospital_id == hospital_id,
            HospitalDoctorMapping.doctor_id == current_user.profile_id
        ).first()
        is_doctor_in_hospital = doctor_mapping is not None

    if (current_user.role != "admin" and
        (current_user.role != "hospital" or current_user.profile_id != hospital_id) and
        not is_doctor_in_hospital):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Check if hospital exists
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Hospital not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Get all patients mapped to this hospital
    patient_mappings = db.query(HospitalPatientMapping).filter(
        HospitalPatientMapping.hospital_id == hospital_id
    ).offset(skip).limit(limit).all()

    patient_ids = [mapping.patient_id for mapping in patient_mappings]
    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    total = db.query(HospitalPatientMapping).filter(
        HospitalPatientMapping.hospital_id == hospital_id
    ).count()

    return {
        "patients": [PatientListItem.model_validate(patient) for patient in patients],
        "total": total
    }
