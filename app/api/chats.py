from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from sqlalchemy import or_, and_

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.chat import Chat, Message
from app.schemas.chat import (
    ChatCreate, ChatResponse, ChatListResponse, ChatListItem,
    MessageListResponse
)
from app.dependencies import get_current_user, get_admin_user, get_doctor_user, get_patient_user, get_user_entity_id
from app.errors import ErrorCode, create_error_response
from app.utils.document_utils import enhance_message_file_details
from app.utils.decorators import standardize_response

router = APIRouter()

@router.post("", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Create a new chat between a doctor and a patient
    """
    # Check if user is admin, the doctor, or the patient in the chat
    is_admin = current_user.role == UserRole.ADMIN

    # For doctor, check if the doctor_id matches the user_entity_id
    is_doctor_in_chat = False
    if current_user.role == UserRole.DOCTOR:
        if user_entity_id == chat_data.doctor_id:
            is_doctor_in_chat = True
        # If doctor_id is the user's ID, update it to use the entity_id
        elif current_user.id == chat_data.doctor_id:
            is_doctor_in_chat = True
            chat_data.doctor_id = user_entity_id

    # For patient, check if the patient_id matches the user_entity_id
    # or if the user has a relation to this patient (1:n relationship)
    is_patient_in_chat = False
    if current_user.role == UserRole.PATIENT:
        if user_entity_id == chat_data.patient_id:
            is_patient_in_chat = True
        # If patient_id is the user's ID, update it to use the entity_id
        elif current_user.id == chat_data.patient_id:
            is_patient_in_chat = True
            chat_data.patient_id = user_entity_id
        else:
            # Check if the user has a relation to this patient
            from app.models.mapping import UserPatientRelation
            relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id,
                UserPatientRelation.patient_id == chat_data.patient_id
            ).first()
            is_patient_in_chat = relation is not None

    if not (is_admin or is_doctor_in_chat or is_patient_in_chat):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )
    # Check if doctor exists
    doctor = db.query(Doctor).filter(Doctor.id == chat_data.doctor_id).first()
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
    patient = db.query(Patient).filter(Patient.id == chat_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Patient not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if chat already exists
    existing_chat = db.query(Chat).filter(
        Chat.doctor_id == chat_data.doctor_id,
        Chat.patient_id == chat_data.patient_id
    ).first()

    if existing_chat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Chat already exists between this doctor and patient",
                error_code=ErrorCode.RES_002
            )
        )

    # Create new chat
    db_chat = Chat(**chat_data.model_dump())

    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)

    return db_chat

@router.get("")
@standardize_response
async def get_chats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Get all chats for the current user
    """
    # Different behavior based on user role
    if current_user.role == UserRole.ADMIN:
        # Admins can see all chats
        chats = db.query(Chat).offset(skip).limit(limit).all()
        total = db.query(Chat).count()
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can see all their chats
        # Use user_entity_id directly
        doctor_id = user_entity_id
        chats = db.query(Chat).filter(
            Chat.doctor_id == doctor_id
        ).offset(skip).limit(limit).all()
        total = db.query(Chat).filter(
            Chat.doctor_id == doctor_id
        ).count()
    elif current_user.role == UserRole.PATIENT:
        # Patients can see all their chats
        # Use user_entity_id directly
        patient_id = user_entity_id

        # For patients, we need to check if there are any chats with this patient_id
        # or if the user has relations to other patients (1:n relationship)
        from app.models.mapping import UserPatientRelation
        relations = db.query(UserPatientRelation).filter(
            UserPatientRelation.user_id == current_user.id
        ).all()

        # Get all patient IDs this user has access to
        patient_ids = [patient_id]  # Start with the user_entity_id
        for relation in relations:
            if relation.patient_id not in patient_ids:
                patient_ids.append(relation.patient_id)

        # Get chats for all these patient IDs
        chats = db.query(Chat).filter(
            Chat.patient_id.in_(patient_ids)
        ).offset(skip).limit(limit).all()

        total = db.query(Chat).filter(
            Chat.patient_id.in_(patient_ids)
        ).count()
    else:
        # Hospitals and other roles don't have chats
        chats = []
        total = 0

    return {"chats": chats, "total": total}

@router.get("/{chat_id}")
@standardize_response
async def get_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Get a specific chat by ID

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Chat not found",
                error_code=ErrorCode.RES_001
            )
        )

    # Check if user has access to this chat
    if current_user.role == UserRole.ADMIN:
        # Admins can access any chat
        return chat
    elif current_user.role == UserRole.DOCTOR:
        # Check if doctor has access to this chat using user_entity_id
        if user_entity_id != chat.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Chats should be accessible to doctors regardless of active status
        return chat
    elif current_user.role == UserRole.PATIENT:
        # Check if patient has access to this chat using user_entity_id
        # For patients, we need to check if the user_entity_id is the patient_id in the chat
        # This is because patients can have multiple patient profiles (1:n relationship)
        if user_entity_id != chat.patient_id:
            # Check if the user has a relation to this patient
            from app.models.mapping import UserPatientRelation
            relation = db.query(UserPatientRelation).filter(
                UserPatientRelation.user_id == current_user.id,
                UserPatientRelation.patient_id == chat.patient_id
            ).first()

            if not relation:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )

        # Chats should be accessible to patients regardless of active status
        return chat
    else:
        # Hospitals and other roles don't have access to chats
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

@router.put("/{chat_id}/deactivate-for-doctor", response_model=ChatResponse)
async def deactivate_chat_for_doctor(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Deactivate a chat for the doctor

    This endpoint uses the user_entity_id header to determine which entity (doctor)
    the user is operating as. This simplifies permission checks.
    """
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to this chat
        if current_user.role == UserRole.ADMIN:
            # Admins can deactivate any chat
            pass
        elif current_user.role == UserRole.DOCTOR:
            # Check if doctor has access to this chat using user_entity_id
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            # Other roles can't deactivate chats for doctors
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Deactivate the chat for the doctor
        chat.is_active_for_doctor = False
        db.commit()
        db.refresh(chat)

        return chat
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

@router.put("/{chat_id}/deactivate-for-patient", response_model=ChatResponse)
async def deactivate_chat_for_patient(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Deactivate a chat for the patient

    This endpoint uses the user_entity_id header to determine which entity (patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to this chat
        if current_user.role == UserRole.ADMIN:
            # Admins can deactivate any chat
            pass
        elif current_user.role == UserRole.PATIENT:
            # Check if patient has access to this chat using user_entity_id
            # For patients, we need to check if the user_entity_id is the patient_id in the chat
            # This is because patients can have multiple patient profiles (1:n relationship)
            if user_entity_id != chat.patient_id:
                # Check if the user has a relation to this patient
                from app.models.mapping import UserPatientRelation
                relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == chat.patient_id
                ).first()

                if not relation:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=create_error_response(
                            status_code=status.HTTP_403_FORBIDDEN,
                            message="Not enough permissions",
                            error_code=ErrorCode.AUTH_004
                        )
                    )
        else:
            # Other roles can't deactivate chats for patients
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Deactivate the chat for the patient
        chat.is_active_for_patient = False
        db.commit()
        db.refresh(chat)

        return chat
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

@router.put("/{chat_id}/activate-for-doctor", response_model=ChatResponse)
async def activate_chat_for_doctor(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Activate a chat for the doctor

    This endpoint uses the user_entity_id header to determine which entity (doctor)
    the user is operating as. This simplifies permission checks.
    """
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to this chat
        if current_user.role == UserRole.ADMIN:
            # Admins can activate any chat
            pass
        elif current_user.role == UserRole.DOCTOR:
            # Check if doctor has access to this chat using user_entity_id
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        else:
            # Other roles can't activate chats for doctors
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Activate the chat for the doctor
        chat.is_active_for_doctor = True
        db.commit()
        db.refresh(chat)

        return chat
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

@router.put("/{chat_id}/activate-for-patient", response_model=ChatResponse)
async def activate_chat_for_patient(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Activate a chat for the patient

    This endpoint uses the user_entity_id header to determine which entity (patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to this chat
        if current_user.role == UserRole.ADMIN:
            # Admins can activate any chat
            pass
        elif current_user.role == UserRole.PATIENT:
            # Check if patient has access to this chat using user_entity_id
            # For patients, we need to check if the user_entity_id is the patient_id in the chat
            # This is because patients can have multiple patient profiles (1:n relationship)
            if user_entity_id != chat.patient_id:
                # Check if the user has a relation to this patient
                from app.models.mapping import UserPatientRelation
                relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == chat.patient_id
                ).first()

                if not relation:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=create_error_response(
                            status_code=status.HTTP_403_FORBIDDEN,
                            message="Not enough permissions",
                            error_code=ErrorCode.AUTH_004
                        )
                    )
        else:
            # Other roles can't activate chats for patients
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Activate the chat for the patient
        chat.is_active_for_patient = True
        db.commit()
        db.refresh(chat)

        return chat
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

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user)  # Using _ to indicate unused parameter
):
    """
    Delete a chat (admin only)
    """
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Chat not found",
                error_code=ErrorCode.RES_001
            )
        )

    db.delete(chat)
    db.commit()

@router.get("/patient/{patient_id}")
@standardize_response
async def get_patient_chats(
    patient_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: Optional[str] = Depends(get_user_entity_id)
) -> Any:
    """
    Get all chats where a specific patient is a participant

    This endpoint returns all chats where the specified patient is a participant.
    Access is restricted to:
    - Admins
    - The patient themselves
    - Doctors who have a chat with this patient
    """
    try:
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

        # Check permissions
        has_permission = False

        if current_user.role == UserRole.ADMIN:
            # Admins can access any patient's chats
            has_permission = True
        elif current_user.role == UserRole.PATIENT:
            # Patients can only access their own chats
            # Check if user_entity_id matches patient_id
            if user_entity_id == patient_id:
                has_permission = True
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can access chats where they are a participant with this patient
            # This will be checked by the query below
            has_permission = True

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get all chats for this patient
        if current_user.role == UserRole.ADMIN:
            # Admins can see all chats for this patient
            chats = db.query(Chat).filter(
                Chat.patient_id == patient_id
            ).offset(skip).limit(limit).all()

            total = db.query(Chat).filter(
                Chat.patient_id == patient_id
            ).count()
        elif current_user.role == UserRole.PATIENT:
            # Patients can see all their chats
            chats = db.query(Chat).filter(
                Chat.patient_id == patient_id
            ).offset(skip).limit(limit).all()

            total = db.query(Chat).filter(
                Chat.patient_id == patient_id
            ).count()
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can only see chats where they are a participant with this patient
            doctor_id = user_entity_id

            chats = db.query(Chat).filter(
                Chat.patient_id == patient_id,
                Chat.doctor_id == doctor_id
            ).offset(skip).limit(limit).all()

            total = db.query(Chat).filter(
                Chat.patient_id == patient_id,
                Chat.doctor_id == doctor_id
            ).count()
        else:
            # Other roles don't have access to chats
            chats = []
            total = 0

        return {"chats": chats, "total": total}
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

@router.get("/doctor/{doctor_id}")
@standardize_response
async def get_doctor_chats(
    doctor_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: Optional[str] = Depends(get_user_entity_id)
) -> Any:
    """
    Get all chats where a specific doctor is a participant

    This endpoint returns all chats where the specified doctor is a participant.
    Access is restricted to:
    - Admins
    - The doctor themselves
    - Patients who have a chat with this doctor
    """
    try:
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

        # Check permissions
        has_permission = False

        if current_user.role == UserRole.ADMIN:
            # Admins can access any doctor's chats
            has_permission = True
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can only access their own chats
            # Check if user_entity_id matches doctor_id
            if user_entity_id == doctor_id:
                has_permission = True
        elif current_user.role == UserRole.PATIENT:
            # Patients can access chats where they are a participant with this doctor
            # This will be checked by the query below
            has_permission = True

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get all chats for this doctor
        if current_user.role == UserRole.ADMIN:
            # Admins can see all chats for this doctor
            chats = db.query(Chat).filter(
                Chat.doctor_id == doctor_id
            ).offset(skip).limit(limit).all()

            total = db.query(Chat).filter(
                Chat.doctor_id == doctor_id
            ).count()
        elif current_user.role == UserRole.DOCTOR:
            # Doctors can see all their chats
            chats = db.query(Chat).filter(
                Chat.doctor_id == doctor_id
            ).offset(skip).limit(limit).all()

            total = db.query(Chat).filter(
                Chat.doctor_id == doctor_id
            ).count()
        elif current_user.role == UserRole.PATIENT:
            # Patients can only see chats where they are a participant with this doctor
            patient_id = user_entity_id

            chats = db.query(Chat).filter(
                Chat.doctor_id == doctor_id,
                Chat.patient_id == patient_id
            ).offset(skip).limit(limit).all()

            total = db.query(Chat).filter(
                Chat.doctor_id == doctor_id,
                Chat.patient_id == patient_id
            ).count()
        else:
            # Other roles don't have access to chats
            chats = []
            total = 0

        return {"chats": chats, "total": total}
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

@router.get("/{chat_id}/messages")
@standardize_response
async def get_chat_messages(
    chat_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Get all messages for a specific chat

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Check if chat exists
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to this chat
        if current_user.role == UserRole.ADMIN:
            # Admins can access any chat
            pass
        elif current_user.role == UserRole.DOCTOR:
            # Check if doctor has access to this chat using user_entity_id
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Messages should be accessible regardless of chat active status
        elif current_user.role == UserRole.PATIENT:
            # Check if patient has access to this chat using user_entity_id
            if user_entity_id != chat.patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Messages should be accessible regardless of chat active status
        else:
            # Hospitals and other roles don't have access to chats
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get messages for the chat
        messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp.desc()).offset(skip).limit(limit).all()
        total = db.query(Message).filter(Message.chat_id == chat_id).count()

        # Enhance file_details in messages with download links
        enhanced_messages = []
        for message in messages:
            message_dict = {
                "id": message.id,
                "chat_id": message.chat_id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "message": message.message,
                "message_type": message.message_type,
                "file_details": enhance_message_file_details(message.file_details),
                "timestamp": message.timestamp,
                "is_read": message.is_read
            }
            enhanced_messages.append(message_dict)

        return {"messages": enhanced_messages, "total": total}
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
