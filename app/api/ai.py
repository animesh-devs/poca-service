from app.models.doctor import Doctor
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict
from datetime import datetime
import logging

from app.db.database import get_db
from app.models.ai import AISession, AIMessage
from app.models.chat import Chat
from app.models.user import User, UserRole
from app.models.case_history import CaseHistory
from app.schemas.ai import (
    AISessionCreate, AISessionResponse,
    AIMessageCreate, AIMessageResponse, AIMessageListResponse,
    AISummaryUpdate, AISummaryResponse, AISuggestedResponseRequest, AISuggestedResponseResponse
)
from app.dependencies import get_current_user, get_user_entity_id
from app.services.ai import get_ai_service
from app.errors import ErrorCode, create_error_response
from app.utils.decorators import standardize_response

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sessions", response_model=AISessionResponse)
@standardize_response
async def create_ai_session(
    session_data: AISessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
):
    """
    Create a new AI session

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Ensure chat_id is a valid UUID
        from uuid import UUID
        chat_id = str(UUID(session_data.chat_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid chat ID format",
                error_code=ErrorCode.REQ_001
            )
        )

    try:
        # Check if the chat exists
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

        # Check if the user has access to the chat
        # Admin users have access to all chats
        if current_user.role == UserRole.ADMIN:
            pass  # Admin has access to all chats
        # Doctor users should have their entity_id match the chat's doctor_id
        elif current_user.role == UserRole.DOCTOR:
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # For patients, check if the user has a relation to the patient in this chat (1:n relationship)
        # The user_entity_id should be the patient_id they want to access
        elif current_user.role == UserRole.PATIENT:
            if user_entity_id == chat.patient_id:
                # Verify that this user actually has a relation to this patient
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
            else:
                # user_entity_id doesn't match the chat's patient_id
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # Hospital users don't have access to chats directly
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Create new AI session
        db_session = AISession(
            chat_id=chat_id
        )

        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        return db_session

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

@router.post("/messages", response_model=AIMessageResponse)
@standardize_response
async def create_ai_message(
    message_data: AIMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
):
    """
    Create a new AI message and get a response

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Ensure session_id is a valid UUID
        from uuid import UUID
        session_id = str(UUID(message_data.session_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid session ID format",
                error_code=ErrorCode.REQ_001
            )
        )

    try:
        # Check if the session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="AI session not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Get the associated chat to check user access
        chat = db.query(Chat).filter(Chat.id == session.chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found for this AI session",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if the user has access to the chat
        # Admin users have access to all chats
        if current_user.role == UserRole.ADMIN:
            pass  # Admin has access to all chats
        # Doctor users should have their entity_id match the chat's doctor_id
        elif current_user.role == UserRole.DOCTOR:
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # For patients, check if the user has a relation to the patient in this chat (1:n relationship)
        # The user_entity_id should be the patient_id they want to access
        elif current_user.role == UserRole.PATIENT:
            if user_entity_id == chat.patient_id:
                # Verify that this user actually has a relation to this patient
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
            else:
                # user_entity_id doesn't match the chat's patient_id
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # Hospital users don't have access to chats directly
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Create new AI message
        db_message = AIMessage(
            session_id=session_id,
            message=message_data.message
        )

        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # Get previous messages for context
        previous_messages = db.query(AIMessage).filter(
            AIMessage.session_id == session_id,
            AIMessage.id != db_message.id
        ).order_by(AIMessage.timestamp.asc()).all()

        context = []
        for prev_msg in previous_messages:
            if prev_msg.message:
                context.append({"role": "user", "content": prev_msg.message})
            if prev_msg.response:
                context.append({"role": "assistant", "content": prev_msg.response})

        # Fetch patient and doctor context for AI prompt resolution
        from app.models.patient import Patient
        from app.models.doctor import Doctor
        from app.models.mapping import UserPatientRelation
        from app.models.case_history import CaseHistory

        patient_data = None
        doctor_data = None
        case_summary = None
        patient_relation = None

        # Get patient information
        patient = db.query(Patient).filter(Patient.id == chat.patient_id).first()
        if patient:
            patient_data = patient

            # Get the most recent case history for case summary
            case_history = db.query(CaseHistory).filter(
                CaseHistory.patient_id == patient.id
            ).order_by(CaseHistory.created_at.desc()).first()
            if case_history and case_history.summary:
                case_summary = case_history.summary

            # Get patient relation if current user is a patient
            if current_user.role == UserRole.PATIENT:
                patient_relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == patient.id
                ).first()

        # Get doctor information
        doctor = db.query(Doctor).filter(Doctor.id == chat.doctor_id).first()
        if doctor:
            doctor_data = doctor

        # Generate AI response with context
        ai_service = get_ai_service()
        response_data = await ai_service.generate_response(
            message_data.message,
            context,
            patient_data=patient_data,
            doctor_data=doctor_data,
            case_summary=case_summary,
            patient_relation=patient_relation
        )

        # Handle response based on type
        if isinstance(response_data, dict):
            # Store the message part in the database
            db_message.response = response_data.get("message", "")
            # Store whether this is a summary
            db_message.is_summary = response_data.get("isSummary", False)
        else:
            # Fallback for string responses
            db_message.response = response_data
            db_message.is_summary = False

        db.commit()
        db.refresh(db_message)

        return db_message

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

@router.get("/sessions/{session_id}/messages", response_model=AIMessageListResponse)
@standardize_response
async def get_ai_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
):
    """
    Get all messages for an AI session

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Ensure session_id is a valid UUID
        from uuid import UUID
        session_id = str(UUID(session_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid session ID format",
                error_code=ErrorCode.REQ_001
            )
        )

    try:
        # Check if the session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="AI session not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Get the associated chat to check user access
        chat = db.query(Chat).filter(Chat.id == session.chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found for this AI session",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if the user has access to the chat
        # Admin users have access to all chats
        if current_user.role == UserRole.ADMIN:
            pass  # Admin has access to all chats
        # Doctor users should have their entity_id match the chat's doctor_id
        elif current_user.role == UserRole.DOCTOR:
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # For patients, check if the user has a relation to the patient in this chat (1:n relationship)
        # The user_entity_id should be the patient_id they want to access
        elif current_user.role == UserRole.PATIENT:
            if user_entity_id == chat.patient_id:
                # Verify that this user actually has a relation to this patient
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
            else:
                # user_entity_id doesn't match the chat's patient_id
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # Hospital users don't have access to chats directly
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get messages
        messages = db.query(AIMessage).filter(
            AIMessage.session_id == session_id
        ).order_by(AIMessage.timestamp.asc()).offset(skip).limit(limit).all()

        total = db.query(AIMessage).filter(AIMessage.session_id == session_id).count()

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

@router.get("/sessions/{session_id}", response_model=AISessionResponse)
@standardize_response
async def get_ai_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
):
    """
    Get an AI session by ID

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Ensure session_id is a valid UUID
        from uuid import UUID
        session_id = str(UUID(session_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid session ID format",
                error_code=ErrorCode.REQ_001
            )
        )

    try:
        # Check if the session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="AI session not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Get the associated chat to check user access
        chat = db.query(Chat).filter(Chat.id == session.chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found for this AI session",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if the user has access to the chat
        # Admin users have access to all chats
        if current_user.role == UserRole.ADMIN:
            pass  # Admin has access to all chats
        # Doctor users should have their entity_id match the chat's doctor_id
        elif current_user.role == UserRole.DOCTOR:
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # For patients, check if the user has a relation to the patient in this chat (1:n relationship)
        # The user_entity_id should be the patient_id they want to access
        elif current_user.role == UserRole.PATIENT:
            if user_entity_id == chat.patient_id:
                # Verify that this user actually has a relation to this patient
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
            else:
                # user_entity_id doesn't match the chat's patient_id
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # Hospital users don't have access to chats directly
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
                    error_code=ErrorCode.AUTH_004
                )
            )

        return session

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

@router.put("/sessions/{session_id}/end", response_model=AISessionResponse)
@standardize_response
async def end_ai_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
):
    """
    End an AI session

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Ensure session_id is a valid UUID
        from uuid import UUID
        session_id = str(UUID(session_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid session ID format",
                error_code=ErrorCode.REQ_001
            )
        )

    try:
        # Check if the session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="AI session not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Get the associated chat to check user access
        chat = db.query(Chat).filter(Chat.id == session.chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found for this AI session",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if the user has access to the chat
        # Admin users have access to all chats
        if current_user.role == UserRole.ADMIN:
            pass  # Admin has access to all chats
        # Doctor users should have their entity_id match the chat's doctor_id
        elif current_user.role == UserRole.DOCTOR:
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="You don't have access to this chat",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # For patients, check if the user has a relation to the patient in this chat (1:n relationship)
        # The user_entity_id should be the patient_id they want to access
        elif current_user.role == UserRole.PATIENT:
            if user_entity_id == chat.patient_id:
                # Verify that this user actually has a relation to this patient
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
                            message="You don't have access to this chat",
                            error_code=ErrorCode.AUTH_004
                        )
                    )
            else:
                # user_entity_id doesn't match the chat's patient_id
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="You don't have access to this chat",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # Hospital users don't have access to chats directly
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You don't have access to this chat",
                    error_code=ErrorCode.AUTH_004
                )
            )

        session.end_timestamp = datetime.now()
        db.commit()
        db.refresh(session)

        return session

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

@router.put("/sessions/{session_id}/summary", response_model=AISummaryResponse)
async def update_ai_summary(
    session_id: str,
    summary_data: AISummaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
):
    """
    Update the summary for an AI session

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Ensure session_id is a valid UUID
        from uuid import UUID
        session_id = str(UUID(session_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid session ID format",
                error_code=ErrorCode.REQ_001
            )
        )

    try:
        # Check if the session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="AI session not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Get the associated chat to check user access
        chat = db.query(Chat).filter(Chat.id == session.chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found for this AI session",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if the user has access to the chat
        # Admin users have access to all chats
        if current_user.role == UserRole.ADMIN:
            pass  # Admin has access to all chats
        # Doctor users should have their entity_id match the chat's doctor_id
        elif current_user.role == UserRole.DOCTOR:
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="You don't have access to this chat",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # For patients, check if the user has a relation to the patient in this chat (1:n relationship)
        # The user_entity_id should be the patient_id they want to access
        elif current_user.role == UserRole.PATIENT:
            if user_entity_id == chat.patient_id:
                # Verify that this user actually has a relation to this patient
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
                            message="You don't have access to this chat",
                            error_code=ErrorCode.AUTH_004
                        )
                    )
            else:
                # user_entity_id doesn't match the chat's patient_id
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="You don't have access to this chat",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # Hospital users don't have access to chats directly
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You don't have access to this chat",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Get the last message in the session
        last_message = db.query(AIMessage).filter(
            AIMessage.session_id == session_id
        ).order_by(AIMessage.timestamp.desc()).first()

        if not last_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="No messages found in the session",
                    error_code=ErrorCode.RES_001
                )
            )

        # Update the last message with the edited summary
        last_message.response = summary_data.summary
        last_message.is_summary = True  # Mark this as a summary
        db.commit()
        db.refresh(last_message)

        # Create a response object
        summary_response = {
            "id": last_message.id,
            "session_id": session_id,
            "summary": last_message.response,
            "timestamp": last_message.timestamp
        }

        return summary_response

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

@router.post("/suggested-response", response_model=AISuggestedResponseResponse)
@standardize_response
async def generate_suggested_response(
    request_data: AISuggestedResponseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
):
    """
    Generate a suggested response for a doctor based on a patient summary

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Ensure session_id is a valid UUID
        from uuid import UUID
        session_id = str(UUID(request_data.session_id))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid session ID format",
                error_code=ErrorCode.REQ_001
            )
        )

    try:
        # Check if the session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="AI session not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Get the chat associated with the session
        chat = db.query(Chat).filter(Chat.id == session.chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found for this AI session",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if the user has access to the chat
        # Admin users have access to all chats
        if current_user.role == UserRole.ADMIN:
            pass  # Admin has access to all chats
        # Doctor users should have their entity_id match the chat's doctor_id
        elif current_user.role == UserRole.DOCTOR:
            if user_entity_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="You don't have access to this chat",
                        error_code=ErrorCode.AUTH_004
                    )
                )
        # Only doctors and admins can generate suggested responses
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Only doctors can generate suggested responses",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Retrieve patient's case history for discharge summary
        discharge_summary = None
        try:
            # Get the most recent case history for the patient
            case_history = db.query(CaseHistory).filter(
                CaseHistory.patient_id == chat.patient_id
            ).order_by(CaseHistory.created_at.desc()).first()

            if case_history and case_history.summary:
                discharge_summary = case_history.summary
                logger.info(f"Retrieved case history summary for patient {chat.patient_id}")
            else:
                logger.info(f"No case history found for patient {chat.patient_id}")
        except Exception as e:
            logger.warning(f"Failed to retrieve case history for patient {chat.patient_id}: {e}")

        # Generate a suggested response using the AI service
        ai_service = get_ai_service()

        doctor_data = db.query(Doctor).filter(Doctor.id == chat.doctor_id).first()

        doctor_identifier = ai_service._get_doctor_identifier(doctor_data)
        logger.info(f"Doctor email: {doctor_identifier}")
        
        has_hardcoded = ai_service._has_hardcoded_suggested_responses(doctor_data)
        logger.info(f"Has hardcoded suggested responses: {has_hardcoded}")
        
        if has_hardcoded:
            logger.info(f"Using hardcoded suggested responses for doctor: {doctor_identifier}")
            hardcoded_response = ai_service._get_hardcoded_suggested_responses(doctor_data)
            logger.info(f"Hardcoded response: {hardcoded_response}")
            if hardcoded_response:
                logger.info(f"Returning suggested hardcoded response: {hardcoded_response}")
                suggested_response = f"{hardcoded_response}"
            else:
                logger.warning(f"Hardcoded suggested response was None for doctor: {doctor_identifier}")
        else:
            logger.info(f"No hardcoded suggested responses configured for doctor: {doctor_identifier}")
            logger.info("Proceeding with normal AI flow")
            suggested_response = await ai_service.generate_suggested_response(
                request_data.summary,
                discharge_summary
            )

        # Create a new AI message for the suggested response
        db_message = AIMessage(
            session_id=session_id,
            message=f"Patient summary: {request_data.summary}",
            response=suggested_response,
            is_summary=False  # This is not a summary, it's a suggested response
        )

        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # Create a response object that matches the AISuggestedResponseResponse schema
        # The @standardize_response decorator will wrap this in the standard format
        response_data = AISuggestedResponseResponse(
            id=db_message.id,
            session_id=session_id,
            suggested_response=suggested_response,
            timestamp=db_message.timestamp
        )

        return response_data

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