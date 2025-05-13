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
    ChatCreate, ChatResponse, ChatListResponse, ChatListItem
)
from app.dependencies import get_current_user, get_admin_user, get_doctor_user, get_patient_user
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
        Chat.is_active == True
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
        # Doctors can see their chats
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Doctor profile not found",
                    error_code=ErrorCode.RES_001
                )
            )

        chats = db.query(Chat).filter(Chat.doctor_id == doctor.id).offset(skip).limit(limit).all()
        total = db.query(Chat).filter(Chat.doctor_id == doctor.id).count()
    elif current_user.role == UserRole.PATIENT:
        # Patients can see their chats
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Patient profile not found",
                    error_code=ErrorCode.RES_001
                )
            )

        chats = db.query(Chat).filter(Chat.patient_id == patient.id).offset(skip).limit(limit).all()
        total = db.query(Chat).filter(Chat.patient_id == patient.id).count()
    else:
        # Hospitals and other roles don't have chats
        chats = []
        total = 0

    return {"chats": chats, "total": total}

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific chat by ID
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
        pass
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can access their chats
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or doctor.id != chat.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    elif current_user.role == UserRole.PATIENT:
        # Patients can access their chats
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or patient.id != chat.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
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

    return chat

@router.put("/{chat_id}/deactivate", response_model=ChatResponse)
async def deactivate_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Deactivate a chat
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
        # Admins can deactivate any chat
        pass
    elif current_user.role == UserRole.DOCTOR:
        # Doctors can deactivate their chats
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or doctor.id != chat.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )
    else:
        # Patients and other roles can't deactivate chats
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Not enough permissions",
                error_code=ErrorCode.AUTH_004
            )
        )

    # Deactivate the chat
    chat.is_active = False
    db.commit()
    db.refresh(chat)

    return chat

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
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
