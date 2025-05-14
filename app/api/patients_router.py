from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Dict

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.chat import Chat
from app.models.mapping import HospitalPatientMapping, DoctorPatientMapping, UserPatientRelation
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

    # Check if the current user is an admin, a doctor treating this patient, or a user with patient role who has access to this patient
    is_admin = current_user.role == UserRole.ADMIN
    is_patient_owner = current_user.role == UserRole.PATIENT and current_user.profile_id == patient_id

    # Check if the user with patient role has a relation to this patient
    is_patient_related = False
    if current_user.role == UserRole.PATIENT:
        # Check if there's a relation between the current user and the patient
        relation = db.query(UserPatientRelation).filter(
            UserPatientRelation.user_id == current_user.id,
            UserPatientRelation.patient_id == patient_id
        ).first()

        if relation:
            is_patient_related = True

    if not (is_admin or is_patient_owner or is_patient_related):
        # If the user is a doctor, check if they are treating this patient
        if current_user.role == UserRole.DOCTOR:
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

    # Check if the current user is an admin, a doctor treating this patient, or a user with patient role who has access to this patient
    is_admin = current_user.role == UserRole.ADMIN
    is_patient_owner = current_user.role == UserRole.PATIENT and current_user.profile_id == patient_id

    # Check if the user with patient role has a relation to this patient
    is_patient_related = False
    if current_user.role == UserRole.PATIENT:
        # Check if there's a relation between the current user and the patient
        relation = db.query(UserPatientRelation).filter(
            UserPatientRelation.user_id == current_user.id,
            UserPatientRelation.patient_id == patient_id
        ).first()

        if relation:
            is_patient_related = True

    if not (is_admin or is_patient_owner or is_patient_related):
        # If the user is a doctor, check if they are treating this patient
        if current_user.role == UserRole.DOCTOR:
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

@router.get("/user/{user_id}", response_model=PatientListResponse)
async def get_user_patients(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all patients associated with a user who has the patient role
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="User not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has patient role
        if user.role != UserRole.PATIENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="User does not have patient role",
                    error_code=ErrorCode.BIZ_001
                )
            )

        # Check if current user is authorized to view this user's patients
        is_admin = current_user.role == UserRole.ADMIN
        is_self = current_user.id == user_id

        if not (is_admin or is_self):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get all patient relations for this user
        relations = db.query(UserPatientRelation).filter(
            UserPatientRelation.user_id == user_id
        ).offset(skip).limit(limit).all()

        # Get patient IDs from relations
        patient_ids = [relation.patient_id for relation in relations]

        # Query for patients
        patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all()

        # For each patient, check if there's an active chat
        patient_list_items = []
        for patient in patients:
            # Check for active chats
            chat = None
            is_active_chat = False

            # For patients, look for chats with doctors
            chat = db.query(Chat).filter(
                Chat.patient_id == patient.id,
                Chat.is_active_for_patient == True,
                Chat.is_active_for_doctor == True
            ).first()

            if chat:
                is_active_chat = True

            # Create PatientListItem
            patient_item = PatientListItem(
                id=patient.id,
                name=patient.name,
                gender=patient.gender,
                photo=patient.photo,
                chat_id=chat.id if chat else None,
                is_active_chat=is_active_chat
            )
            patient_list_items.append(patient_item)

        return {
            "patients": patient_list_items,
            "total": len(patient_list_items)
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
