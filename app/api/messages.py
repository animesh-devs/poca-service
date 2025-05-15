from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.chat import Chat, Message
from app.schemas.chat import (
    MessageCreate, MessageResponse, MessageListResponse,
    ReadStatusUpdate
)
from app.dependencies import get_current_user, get_user_entity_id
from app.errors import ErrorCode, create_error_response

router = APIRouter()

@router.post("", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Create a new message in a chat

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Check if chat exists
        chat = db.query(Chat).filter(Chat.id == message_data.chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # No need to check if chat is active for both doctor and patient
        # as is_active_for_doctor and is_active_for_patient are only for UI purposes

        # Check if user has access to this chat
        if current_user.role == UserRole.ADMIN:
            # Admins can send messages to any chat
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

            # Verify sender ID matches the doctor's entity ID
            if message_data.sender_id != user_entity_id and message_data.sender_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=create_error_response(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message="Sender ID does not match authenticated user",
                        error_code=ErrorCode.BIZ_001
                    )
                )

            # Always use the entity ID as sender_id
            message_data.sender_id = user_entity_id

            # Verify receiver ID matches the patient's ID
            if message_data.receiver_id != chat.patient_id:
                # Check if receiver_id is a user_id and get the patient profile
                patient_user = db.query(User).filter(User.id == message_data.receiver_id).first()
                if patient_user and patient_user.role == UserRole.PATIENT and patient_user.profile_id == chat.patient_id:
                    # Update receiver_id to use the profile_id
                    message_data.receiver_id = chat.patient_id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=create_error_response(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message="Receiver ID does not match chat patient",
                            error_code=ErrorCode.BIZ_001
                        )
                    )
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

            # Verify sender ID matches the patient's entity ID
            if message_data.sender_id != user_entity_id and message_data.sender_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=create_error_response(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message="Sender ID does not match authenticated user",
                        error_code=ErrorCode.BIZ_001
                    )
                )

            # Always use the entity ID as sender_id
            message_data.sender_id = user_entity_id

            # Verify receiver ID matches the doctor's ID
            if message_data.receiver_id != chat.doctor_id:
                # Check if receiver_id is a user_id and get the doctor profile
                doctor_user = db.query(User).filter(User.id == message_data.receiver_id).first()
                if doctor_user and doctor_user.role == UserRole.DOCTOR and doctor_user.profile_id == chat.doctor_id:
                    # Update receiver_id to use the profile_id
                    message_data.receiver_id = chat.doctor_id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=create_error_response(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message="Receiver ID does not match chat doctor",
                            error_code=ErrorCode.BIZ_001
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

        # Create new message
        db_message = Message(
            chat_id=message_data.chat_id,
            sender_id=message_data.sender_id,
            receiver_id=message_data.receiver_id,
            message=message_data.message,
            message_type=message_data.message_type,
            file_details=message_data.file_details
        )

        # Update is_active flags based on who is sending the message
        # If doctor is sending, set is_active_for_patient=True and is_active_for_doctor=False
        # If patient is sending, set is_active_for_doctor=True and is_active_for_patient=False
        if current_user.role == UserRole.DOCTOR:
            chat.is_active_for_patient = True
            chat.is_active_for_doctor = False
        elif current_user.role == UserRole.PATIENT:
            chat.is_active_for_doctor = True
            chat.is_active_for_patient = False

        db.add(db_message)
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

@router.get("/chat/{chat_id}", response_model=MessageListResponse)
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

@router.put("/read-status", status_code=status.HTTP_200_OK)
async def update_read_status(
    status_data: ReadStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Update read status for multiple messages

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Get all messages with the given IDs
        message_ids = status_data.message_ids if hasattr(status_data, 'message_ids') else [status_data.message_id]
        messages = db.query(Message).filter(Message.id.in_(message_ids)).all()

        # Check if all messages exist
        if len(messages) != len(message_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="One or more messages not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to these messages
        for message in messages:
            chat = db.query(Chat).filter(Chat.id == message.chat_id).first()
            if not chat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=create_error_response(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message=f"Chat not found for message {message.id}",
                        error_code=ErrorCode.RES_001
                    )
                )

            if current_user.role == UserRole.ADMIN:
                # Admins can update any message
                pass
            elif current_user.role == UserRole.DOCTOR:
                # Check if doctor has access to this chat using user_entity_id
                if user_entity_id != chat.doctor_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=create_error_response(
                            status_code=status.HTTP_403_FORBIDDEN,
                            message=f"Not enough permissions for message {message.id}",
                            error_code=ErrorCode.AUTH_004
                        )
                    )

                # Doctors can only mark messages as read if they are the receiver
                if message.receiver_id != user_entity_id and status_data.is_read:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=create_error_response(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message=f"Cannot mark message {message.id} as read because you are not the receiver",
                            error_code=ErrorCode.BIZ_001
                        )
                    )
            elif current_user.role == UserRole.PATIENT:
                # Check if patient has access to this chat using user_entity_id
                if user_entity_id != chat.patient_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=create_error_response(
                            status_code=status.HTTP_403_FORBIDDEN,
                            message=f"Not enough permissions for message {message.id}",
                            error_code=ErrorCode.AUTH_004
                        )
                    )

                # Patients can only mark messages as read if they are the receiver
                if message.receiver_id != user_entity_id and status_data.is_read:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=create_error_response(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message=f"Cannot mark message {message.id} as read because you are not the receiver",
                            error_code=ErrorCode.BIZ_001
                        )
                    )
            else:
                # Hospitals and other roles don't have access to messages
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=create_error_response(
                        status_code=status.HTTP_403_FORBIDDEN,
                        message="Not enough permissions",
                        error_code=ErrorCode.AUTH_004
                    )
                )

        # Update read status for all messages
        for message in messages:
            message.is_read = status_data.is_read

        db.commit()

        return {"success": True, "updated_count": len(messages)}
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

@router.put("/{message_id}/read", status_code=status.HTTP_200_OK)
async def update_message_read_status(
    message_id: str,
    is_read: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Update read status for a single message

    This endpoint uses the user_entity_id header to determine which entity (doctor, patient)
    the user is operating as. This simplifies permission checks.
    """
    try:
        # Get the message
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Message not found",
                    error_code=ErrorCode.RES_001
                )
            )

        # Check if user has access to this message
        chat = db.query(Chat).filter(Chat.id == message.chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Chat not found for this message",
                    error_code=ErrorCode.RES_001
                )
            )

        if current_user.role == UserRole.ADMIN:
            # Admins can update any message
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

            # Doctors can only mark messages as read if they are the receiver
            if message.receiver_id != user_entity_id and is_read:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=create_error_response(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message="Cannot mark message as read because you are not the receiver",
                        error_code=ErrorCode.BIZ_001
                    )
                )
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

            # Patients can only mark messages as read if they are the receiver
            if message.receiver_id != user_entity_id and is_read:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=create_error_response(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message="Cannot mark message as read because you are not the receiver",
                        error_code=ErrorCode.BIZ_001
                    )
                )
        else:
            # Hospitals and other roles don't have access to messages
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Not enough permissions",
                    error_code=ErrorCode.AUTH_004
                )
            )

        # Update read status
        message.is_read = is_read
        db.commit()

        return {"success": True, "message_id": message_id, "is_read": is_read}
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
