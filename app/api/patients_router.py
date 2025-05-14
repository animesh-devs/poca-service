from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Dict

from app.db.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.mapping import HospitalPatientMapping, DoctorPatientMapping
from app.schemas.patient import PatientUpdate, PatientResponse, PatientListResponse, PatientListItem
from app.schemas.hospital import HospitalListItem
from app.dependencies import get_current_user, get_admin_user, get_patient_user
from app.errors import ErrorCode, create_error_response

router = APIRouter()

@router.get("", response_model=PatientListResponse)
async def get_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all patients
    """
    # Only admins and doctors can see all patients
    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    patients = db.query(Patient).offset(skip).limit(limit).all()
    total = db.query(Patient).count()

    return {
        "patients": [PatientListItem.model_validate(patient) for patient in patients],
        "total": total
    }

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get patient by ID
    """
    # All authenticated users can access patient information

    # First, check if the ID is a profile_id
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    # If not found, check if it's a user_id and get the profile_id
    if not patient:
        # For admin, check any user ID
        if current_user.role == "admin":
            user = db.query(User).filter(User.id == patient_id).first()
            if user and user.role == "patient" and user.profile_id:
                patient = db.query(Patient).filter(Patient.id == user.profile_id).first()
        # For patient, check if it's their own user ID
        elif current_user.role == "patient":
            if patient_id == current_user.id and current_user.profile_id:
                patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()
            # Also allow patient to access their profile directly with profile_id
            elif patient_id == current_user.profile_id:
                patient = db.query(Patient).filter(Patient.id == current_user.profile_id).first()
        # For doctor, allow access to any patient (doctors need to see patient profiles)
        elif current_user.role == "doctor":
            user = db.query(User).filter(User.id == patient_id).first()
            if user and user.role == "patient" and user.profile_id:
                patient = db.query(Patient).filter(Patient.id == user.profile_id).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update patient profile
    """
    # First, check if the ID is a profile_id
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    # If not found, check if it's a user_id and get the profile_id
    if not patient and current_user.role == "admin":
        user = db.query(User).filter(User.id == patient_id).first()
        if user and user.role == "patient" and user.profile_id:
            patient = db.query(Patient).filter(Patient.id == user.profile_id).first()
            patient_id = user.profile_id  # Update patient_id to the profile_id

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if the current user is an admin or the patient being updated
    is_admin = current_user.role == "admin"
    is_patient_owner = (
        current_user.role == "patient" and
        (current_user.profile_id == patient_id or  # Using profile_id
         (patient and patient.id == current_user.profile_id))  # Using user_id
    )

    if not (is_admin or is_patient_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Update patient fields
    for field, value in patient_data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    return patient

@router.get("/{patient_id}/doctors", response_model=List[dict])
async def get_patient_doctors(
    patient_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all doctors for a patient
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

    # Check if the current user is an admin, a doctor treating this patient, or the patient
    is_admin = current_user.role == "admin"
    is_patient_owner = current_user.role == "patient" and current_user.profile_id == patient_id

    if not (is_admin or is_patient_owner):
        # If the user is a doctor, check if they are treating this patient
        if current_user.role == "doctor":
            doctor_id = current_user.profile_id
            mapping = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.doctor_id == doctor_id,
                DoctorPatientMapping.patient_id == patient_id
            ).first()

            if not mapping:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

    # Get all doctors mapped to this patient
    from app.models.doctor import Doctor

    # Query for doctor-patient mappings
    mappings = db.query(DoctorPatientMapping).filter(
        DoctorPatientMapping.patient_id == patient_id
    ).offset(skip).limit(limit).all()

    # Get doctor IDs from mappings
    doctor_ids = [mapping.doctor_id for mapping in mappings]

    # Query for doctors
    doctors = db.query(Doctor).filter(Doctor.id.in_(doctor_ids)).all()

    # Return doctor data
    return [
        {
            "id": doctor.id,
            "name": doctor.name,
            "designation": doctor.designation,
            "experience": doctor.experience,
            "photo": doctor.photo,
            "contact": doctor.contact
        }
        for doctor in doctors
    ]

@router.get("/{patient_id}/hospitals", response_model=List[Dict])
async def get_patient_hospitals(
    patient_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all hospitals for a patient
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

    # Check if the current user is an admin, a doctor treating this patient, or the patient
    is_admin = current_user.role == "admin"
    is_patient_owner = current_user.role == "patient" and current_user.profile_id == patient_id

    if not (is_admin or is_patient_owner):
        # If the user is a doctor, check if they are treating this patient
        if current_user.role == "doctor":
            doctor_id = current_user.profile_id
            mapping = db.query(DoctorPatientMapping).filter(
                DoctorPatientMapping.doctor_id == doctor_id,
                DoctorPatientMapping.patient_id == patient_id
            ).first()

            if not mapping:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

    # Get all hospitals mapped to this patient
    # Query for hospital-patient mappings
    mappings = db.query(HospitalPatientMapping).filter(
        HospitalPatientMapping.patient_id == patient_id
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
            "city": hospital.city,
            "state": hospital.state,
            "country": hospital.country,
            "contact": hospital.contact,
            "specialities": hospital.specialities
        }
        for hospital in hospitals
    ]
