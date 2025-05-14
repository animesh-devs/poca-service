from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.database import get_db
from app.models.ai import AISession, AIMessage
from app.models.chat import Chat, Message
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.ai import (
    AISessionCreate, AISessionResponse,
    AIMessageCreate, AIMessageResponse, AIMessageListResponse,
    AISummaryUpdate, AISummaryResponse, AISuggestedResponseRequest, AISuggestedResponseResponse
)
from app.dependencies import get_current_user
from app.services.ai import get_ai_service
from app.errors import ErrorCode, create_error_response

router = APIRouter()

@router.post("/sessions", response_model=AISessionResponse)
async def create_ai_session(
    session_data: AISessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new AI session"""
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
    # Doctor users should have their profile_id match the chat's doctor_id
    elif current_user.role == UserRole.DOCTOR:
        if current_user.profile_id != chat.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You don't have access to this chat",
                    error_code=ErrorCode.AUTH_004
                )
            )
    # Patient users should have their profile_id match the chat's patient_id
    elif current_user.role == UserRole.PATIENT:
        if current_user.profile_id != chat.patient_id:
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

    # Create new AI session
    db_session = AISession(
        chat_id=chat_id
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return db_session

@router.post("/messages", response_model=AIMessageResponse)
async def create_ai_message(
    message_data: AIMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new AI message and get a response"""
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
    # Doctor users should have their profile_id match the chat's doctor_id
    elif current_user.role == UserRole.DOCTOR:
        has_access = False
        # Check if profile_id matches doctor_id
        if current_user.profile_id and current_user.profile_id == chat.doctor_id:
            has_access = True
        # Check if user_id matches doctor's user_id
        else:
            doctor = db.query(Doctor).filter(Doctor.id == chat.doctor_id).first()
            if doctor and doctor.user_id == current_user.id:
                has_access = True

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You don't have access to this chat",
                    error_code=ErrorCode.AUTH_004
                )
            )
    # Patient users should have their profile_id match the chat's patient_id
    elif current_user.role == UserRole.PATIENT:
        has_access = False
        # Check if profile_id matches patient_id
        if current_user.profile_id and current_user.profile_id == chat.patient_id:
            has_access = True
        # Check if user_id matches patient's user_id
        else:
            patient = db.query(Patient).filter(Patient.id == chat.patient_id).first()
            if patient and patient.user_id == current_user.id:
                has_access = True

        if not has_access:
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

    # Generate AI response
    ai_service = get_ai_service()
    response_data = await ai_service.generate_response(message_data.message, context)

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

@router.get("/sessions/{session_id}/messages", response_model=AIMessageListResponse)
async def get_ai_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages for an AI session"""
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
    # Doctor users should have their profile_id match the chat's doctor_id
    elif current_user.role == UserRole.DOCTOR:
        if current_user.profile_id != chat.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You don't have access to this chat",
                    error_code=ErrorCode.AUTH_004
                )
            )
    # Patient users should have their profile_id match the chat's patient_id
    elif current_user.role == UserRole.PATIENT:
        if current_user.profile_id != chat.patient_id:
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

    # Get messages
    messages = db.query(AIMessage).filter(
        AIMessage.session_id == session_id
    ).order_by(AIMessage.timestamp.asc()).offset(skip).limit(limit).all()

    total = db.query(AIMessage).filter(AIMessage.session_id == session_id).count()

    return {"messages": messages, "total": total}

@router.get("/sessions/{session_id}", response_model=AISessionResponse)
async def get_ai_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get an AI session by ID"""
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
    # Doctor users should have their profile_id match the chat's doctor_id
    elif current_user.role == UserRole.DOCTOR:
        if current_user.profile_id != chat.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You don't have access to this chat",
                    error_code=ErrorCode.AUTH_004
                )
            )
    # Patient users should have their profile_id match the chat's patient_id
    elif current_user.role == UserRole.PATIENT:
        if current_user.profile_id != chat.patient_id:
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

    return session

@router.put("/sessions/{session_id}/end", response_model=AISessionResponse)
async def end_ai_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """End an AI session"""
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
    # Doctor users should have their profile_id match the chat's doctor_id
    elif current_user.role == UserRole.DOCTOR:
        if current_user.profile_id != chat.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You don't have access to this chat",
                    error_code=ErrorCode.AUTH_004
                )
            )
    # Patient users should have their profile_id match the chat's patient_id
    elif current_user.role == UserRole.PATIENT:
        if current_user.profile_id != chat.patient_id:
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

@router.put("/sessions/{session_id}/summary", response_model=AISummaryResponse)
async def update_ai_summary(
    session_id: str,
    summary_data: AISummaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the summary for an AI session"""
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
    # Doctor users should have their profile_id match the chat's doctor_id
    elif current_user.role == UserRole.DOCTOR:
        if current_user.profile_id != chat.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="You don't have access to this chat",
                    error_code=ErrorCode.AUTH_004
                )
            )
    # Patient users should have their profile_id match the chat's patient_id
    elif current_user.role == UserRole.PATIENT:
        if current_user.profile_id != chat.patient_id:
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

@router.post("/suggested-response", response_model=AISuggestedResponseResponse)
async def generate_suggested_response(
    request_data: AISuggestedResponseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a suggested response for a doctor based on a patient summary"""
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
    # Doctor users should have their profile_id match the chat's doctor_id
    elif current_user.role == UserRole.DOCTOR:
        if current_user.profile_id != chat.doctor_id:
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

    # Generate a suggested response using the AI service
    ai_service = get_ai_service()

    # Create a system prompt for the doctor's suggested response
    doctor_prompt = "You are a medical professional. Based on the patient's summary, provide a thoughtful, professional response. Include possible diagnoses, recommended next steps, and any advice you would give to the patient. Be empathetic and clear."

    context = [
        {"role": "system", "content": doctor_prompt},
        {"role": "user", "content": f"Patient summary: {request_data.summary}"}
    ]

    suggested_response = await ai_service.generate_response("Please provide a suggested response to this patient summary.", context)

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

    # Create a response object
    response_data = {
        "id": db_message.id,
        "session_id": session_id,
        "suggested_response": suggested_response,
        "timestamp": db_message.timestamp
    }

    return response_data