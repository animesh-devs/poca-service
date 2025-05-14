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

router = APIRouter()

@router.post("", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new chat between a doctor and a patient
    """
    # Check if user is admin, the doctor, or the patient in the chat
    is_admin = current_user.role == UserRole.ADMIN

    # For doctor, check if the doctor_id matches either the user's ID or profile_id
    is_doctor_in_chat = False
    if current_user.role == UserRole.DOCTOR:
        # Check if doctor_id is the user's profile_id
        if current_user.profile_id == chat_data.doctor_id:
            is_doctor_in_chat = True
        # Check if doctor_id is the user's ID and get the doctor profile
        elif current_user.id == chat_data.doctor_id:
            is_doctor_in_chat = True
            # Update chat_data.doctor_id to use the profile_id
            chat_data.doctor_id = current_user.profile_id

    # For patient, check if the patient_id matches either the user's ID or profile_id
    is_patient_in_chat = False
    if current_user.role == UserRole.PATIENT:
        # Check if patient_id is the user's profile_id
        if current_user.profile_id == chat_data.patient_id:
            is_patient_in_chat = True
        # Check if patient_id is the user's ID and get the patient profile
        elif current_user.id == chat_data.patient_id:
            is_patient_in_chat = True
            # Update chat_data.patient_id to use the profile_id
            chat_data.patient_id = current_user.profile_id

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
        Chat.patient_id == chat_data.patient_id,
        Chat.is_active_for_doctor == True,
        Chat.is_active_for_patient == True
    ).first()

    if existing_chat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Active chat already exists between this doctor and patient",
                error_code=ErrorCode.RES_002
            )
        )

    # Create new chat
    db_chat = Chat(**chat_data.model_dump())

    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)

    return db_chat

@router.get("", response_model=ChatListResponse)
async def get_chats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
        # Doctors can see their chats that are active for doctors
        if current_user.profile_id:
            # Use profile_id directly if available
            doctor_id = current_user.profile_id
            chats = db.query(Chat).filter(
                Chat.doctor_id == doctor_id,
                Chat.is_active_for_doctor == True
            ).offset(skip).limit(limit).all()
            total = db.query(Chat).filter(
                Chat.doctor_id == doctor_id,
                Chat.is_active_for_doctor == True
            ).count()
        else:
            # Try to find doctor profile
            doctor = db.query(Doctor).filter(Doctor.id == current_user.id).first()
            if not doctor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=create_error_response(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message="Doctor profile not found",
                        error_code=ErrorCode.RES_001
                    )
                )
            chats = db.query(Chat).filter(
                Chat.doctor_id == doctor.id,
                Chat.is_active_for_doctor == True
            ).offset(skip).limit(limit).all()
            total = db.query(Chat).filter(
                Chat.doctor_id == doctor.id,
                Chat.is_active_for_doctor == True
            ).count()
    elif current_user.role == UserRole.PATIENT:
        # Patients can see their chats that are active for patients
        if current_user.profile_id:
            # Use profile_id directly if available
            patient_id = current_user.profile_id
            chats = db.query(Chat).filter(
                Chat.patient_id == patient_id,
                Chat.is_active_for_patient == True
            ).offset(skip).limit(limit).all()
            total = db.query(Chat).filter(
                Chat.patient_id == patient_id,
                Chat.is_active_for_patient == True
            ).count()
        else:
            # Try to find patient profile by user_id
            patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

            # If not found, try to find by direct ID match
            if not patient:
                patient = db.query(Patient).filter(Patient.id == current_user.id).first()

            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=create_error_response(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message="Patient profile not found",
                        error_code=ErrorCode.RES_001
                    )
                )
            chats = db.query(Chat).filter(
                Chat.patient_id == patient.id,
                Chat.is_active_for_patient == True
            ).offset(skip).limit(limit).all()
            total = db.query(Chat).filter(
                Chat.patient_id == patient.id,
                Chat.is_active_for_patient == True
            ).count()
    else:
        # Hospitals and other roles don't have chats
        chats = []
        total = 0

    return {"chats": chats, "total": total}

@router.get("/{chat_id}", response_model=ChatResponse)
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
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Chats should be accessible to doctors regardless of active status
        return chat
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
            if user_entity_id != chat.patient_id:
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
            if user_entity_id != chat.patient_id:
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

@router.get("/{chat_id}/messages", response_model=MessageListResponse)
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

        return {"messages": messages, "total": total}
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
