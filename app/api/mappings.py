from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Dict

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.hospital import Hospital
from app.models.chat import Chat
from app.models.mapping import (
    HospitalDoctorMapping,
    HospitalPatientMapping,
    DoctorPatientMapping,
    UserPatientRelation,
    RelationType
)
from app.schemas.mapping import (
    HospitalDoctorMappingCreate, HospitalDoctorMappingResponse,
    HospitalPatientMappingCreate, HospitalPatientMappingResponse,
    DoctorPatientMappingCreate, DoctorPatientMappingResponse,
    UserPatientRelationCreate, UserPatientRelationUpdate, UserPatientRelationResponse
)
from app.schemas.patient import PatientListResponse, PatientListItem
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

@router.post("/user-patient", response_model=UserPatientRelationResponse)
async def create_user_patient_relation(
    relation_data: UserPatientRelationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a relation between a user and a patient
    """
    try:
        from app.models.user import UserRole
        from app.models.mapping import RelationType

        # Check if user exists
        user = db.query(User).filter(User.id == relation_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="User not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if patient exists
        patient = db.query(Patient).filter(Patient.id == relation_data.patient_id).first()

        # If not found by ID, try to find by user_id
        if not patient:
            patient_user = db.query(User).filter(User.id == relation_data.patient_id, User.role == UserRole.PATIENT).first()
            if patient_user and patient_user.profile_id:
                patient = db.query(Patient).filter(Patient.id == patient_user.profile_id).first()

        if not patient:
            # If still not found, create a new patient if the relation is "self"
            if relation_data.relation == RelationType.SELF and user.role == UserRole.PATIENT:
                patient = Patient(
                    name=user.name,
                    user_id=user.id
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)

                # Update user's profile_id
                user.profile_id = patient.id
                db.commit()
                db.refresh(user)

                # Update relation_data.patient_id
                relation_data.patient_id = patient.id
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=create_error_response(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message="Patient not found",
                        error_code=ErrorCode.RES_001
                    )
                )

        # Check if relation already exists
        existing_relation = db.query(UserPatientRelation).filter(
            UserPatientRelation.user_id == relation_data.user_id,
            UserPatientRelation.patient_id == relation_data.patient_id
        ).first()

        if existing_relation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Relation already exists",
                    error_code=ErrorCode.RES_002
                )
            )

        # Validate relation type based on user role
        if relation_data.relation == RelationType.DOCTOR:
            # For doctor relation, check if the user is a doctor
            if user.role != UserRole.DOCTOR:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=create_error_response(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message="Only users with doctor role can have doctor relation",
                        error_code=ErrorCode.BIZ_001
                    )
                )

            # Also create a doctor-patient mapping if it doesn't exist
            doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
            if not doctor:
                # Try to get doctor by profile_id
                if user.profile_id:
                    doctor = db.query(Doctor).filter(Doctor.id == user.profile_id).first()

            if doctor:
                # Check if mapping already exists
                existing_mapping = db.query(DoctorPatientMapping).filter(
                    DoctorPatientMapping.doctor_id == doctor.id,
                    DoctorPatientMapping.patient_id == patient.id
                ).first()

                if not existing_mapping:
                    # Create new mapping
                    db_mapping = DoctorPatientMapping(
                        doctor_id=doctor.id,
                        patient_id=patient.id
                    )
                    db.add(db_mapping)

        # Create new relation
        db_relation = UserPatientRelation(**relation_data.model_dump())

        db.add(db_relation)
        db.commit()
        db.refresh(db_relation)

        return db_relation
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

@router.put("/user-patient/{relation_id}", response_model=UserPatientRelationResponse)
async def update_user_patient_relation(
    relation_id: str,
    relation_data: UserPatientRelationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a relation between a user and a patient
    """
    try:
        # Check if relation exists
        relation = db.query(UserPatientRelation).filter(UserPatientRelation.id == relation_id).first()
        if not relation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Relation not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user is authorized to update this relation
        from app.models.user import UserRole
        is_admin = current_user.role == UserRole.ADMIN
        is_owner = current_user.id == relation.user_id

        if not (is_admin or is_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Update relation
        for field, value in relation_data.model_dump().items():
            setattr(relation, field, value)

        db.commit()
        db.refresh(relation)

        return relation
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

@router.delete("/user-patient/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_patient_relation(
    relation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a user-patient relation
    """
    try:
        # Check if relation exists
        relation = db.query(UserPatientRelation).filter(UserPatientRelation.id == relation_id).first()
        if not relation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Relation not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user is authorized to delete this relation
        from app.models.user import UserRole
        is_admin = current_user.role == UserRole.ADMIN
        is_owner = current_user.id == relation.user_id

        if not (is_admin or is_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        db.delete(relation)
        db.commit()
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

@router.get("/user/{user_id}/patients", response_model=PatientListResponse)
async def get_user_patients(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all patients linked to a user through user-patient relations.

    The response includes patient information (id, name, gender, dob, contact, photo, relation)
    without chat information, as a patient can have multiple chats.
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

        # Create patient list items with additional fields
        patient_list_items = []
        for patient in patients:
            # Find the relation for this patient
            relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == user_id,
                UserPatientRelation.patient_id == patient.id
            ).first()

            relation_type = relation.relation.value if relation else None

            # Create PatientListItem
            patient_item = PatientListItem(
                id=patient.id,
                name=patient.name,
                gender=patient.gender,
                dob=patient.dob,
                contact=patient.contact,
                photo=patient.photo,
                relation=relation_type
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
