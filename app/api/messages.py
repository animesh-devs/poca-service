from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Any, Optional
from uuid import uuid4

from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.chat import Chat, Message, MessageType
from app.models.document import FileDocument, DocumentType, UploadedBy
from app.services.document_storage import document_storage
from app.config import settings
from app.utils.document_utils import enhance_message_file_details
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
                        message="Invalid entity ID for this user",
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
                    message="Invalid entity ID for this user",
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
                        message="Invalid entity ID for this user",
                        error_code=ErrorCode.AUTH_004
                    )
                )

            # Messages should be accessible regardless of chat active status
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

            # Messages should be accessible regardless of chat active status
        else:
            # Hospitals and other roles don't have access to chats
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response(
                    status_code=status.HTTP_403_FORBIDDEN,
                    message="Invalid entity ID for this user",
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

@router.post("/with-attachment", response_model=MessageResponse)
async def create_message_with_attachment(
    chat_id: str = Form(...),
    receiver_id: str = Form(...),
    message: str = Form(...),
    message_type: MessageType = Form(MessageType.TEXT),
    file: Optional[UploadFile] = File(None),
    document_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_entity_id: str = Depends(get_user_entity_id)
) -> Any:
    """
    Create a new message with an attachment (document or image)

    This endpoint supports two ways to attach files:
    1. Upload a new file directly
    2. Reference an existing document by ID

    The message_type should be one of: text, audio, file, image, document
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

        # Check permissions based on user role
        is_admin = current_user.role == UserRole.ADMIN
        is_doctor = current_user.role == UserRole.DOCTOR
        is_patient = current_user.role == UserRole.PATIENT

        # Set sender_id to the entity ID
        sender_id = user_entity_id

        # Verify permissions and receiver_id
        if is_doctor:
            # Verify sender ID matches the doctor's entity ID
            if sender_id != chat.doctor_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=create_error_response(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message="Sender ID does not match authenticated user",
                        error_code=ErrorCode.BIZ_001
                    )
                )

            # Verify receiver ID matches the patient's ID
            if receiver_id != chat.patient_id:
                # Check if receiver_id is a user_id and get the patient profile
                patient_user = db.query(User).filter(User.id == receiver_id).first()
                if patient_user and patient_user.role == UserRole.PATIENT and patient_user.profile_id == chat.patient_id:
                    # Update receiver_id to use the profile_id
                    receiver_id = chat.patient_id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=create_error_response(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message="Receiver ID does not match chat patient",
                            error_code=ErrorCode.BIZ_001
                        )
                    )
        elif is_patient:
            # Verify sender ID matches the patient's entity ID
            # For patients, we need to check if the user_entity_id is the patient_id in the chat
            # This is because patients can have multiple patient profiles (1:n relationship)
            if sender_id != chat.patient_id:
                # Check if the user has a relation to this patient
                from app.models.mapping import UserPatientRelation
                relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == chat.patient_id
                ).first()

                if not relation:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=create_error_response(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message="Sender ID does not match authenticated user",
                            error_code=ErrorCode.BIZ_001
                        )
                    )

            # Verify receiver ID matches the doctor's ID
            if receiver_id != chat.doctor_id:
                # Check if receiver_id is a user_id and get the doctor profile
                doctor_user = db.query(User).filter(User.id == receiver_id).first()
                if doctor_user and doctor_user.role == UserRole.DOCTOR and doctor_user.profile_id == chat.doctor_id:
                    # Update receiver_id to use the profile_id
                    receiver_id = chat.doctor_id
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=create_error_response(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            message="Receiver ID does not match chat doctor",
                            error_code=ErrorCode.BIZ_001
                        )
                    )
        elif is_admin:
            # Admin can send messages as any user
            pass
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

        # Handle file attachment
        file_details = None

        if file and document_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Cannot provide both file and document_id",
                    error_code=ErrorCode.BIZ_001
                )
            )

        if file:
            # Upload a new file to in-memory storage
            file_content = await file.read()
            file_size = len(file_content)

            # Store document in memory storage
            storage_id = document_storage.store_document(
                file_content=file_content,
                filename=file.filename,
                content_type=file.content_type
            )

            # Create downloadable link using the public base URL
            download_link = f"{settings.PUBLIC_BASE_URL}{settings.API_V1_PREFIX}/documents/{storage_id}/download"

            # Determine uploaded_by_role based on current user's role
            if current_user.role == UserRole.DOCTOR:
                uploaded_by_role = UploadedBy.DOCTOR
            elif current_user.role == UserRole.ADMIN:
                uploaded_by_role = UploadedBy.ADMIN
            else:
                uploaded_by_role = UploadedBy.PATIENT

            # Create a document record
            doc_type = DocumentType.OTHER
            if message_type == MessageType.IMAGE:
                doc_type = DocumentType.OTHER  # You might want to add an IMAGE type to DocumentType
            elif message_type == MessageType.DOCUMENT:
                doc_type = DocumentType.OTHER

            db_document = FileDocument(
                id=storage_id,  # Use the storage ID as the document ID
                file_name=file.filename,
                size=file_size,
                link=download_link,
                document_type=doc_type,
                uploaded_by=current_user.id,
                uploaded_by_role=uploaded_by_role,
                remark=f"Attached to message in chat {chat_id}"
            )

            db.add(db_document)
            db.commit()
            db.refresh(db_document)

            # Create file details for the message
            file_details = {
                "document_id": db_document.id,
                "file_name": db_document.file_name,
                "size": db_document.size,
                "link": db_document.link,
                "uploaded_by": db_document.uploaded_by,
                "upload_timestamp": db_document.upload_timestamp.isoformat()
            }

            # Enhance file details with download link
            file_details = enhance_message_file_details(file_details)

        elif document_id:
            # Use an existing document
            db_document = db.query(FileDocument).filter(FileDocument.id == document_id).first()
            if not db_document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=create_error_response(
                        status_code=status.HTTP_404_NOT_FOUND,
                        message="Document not found",
                        error_code=ErrorCode.RES_001
                    )
                )

            # Create file details for the message
            file_details = {
                "document_id": db_document.id,
                "file_name": db_document.file_name,
                "size": db_document.size,
                "link": db_document.link,
                "uploaded_by": db_document.uploaded_by,
                "upload_timestamp": db_document.upload_timestamp.isoformat()
            }

            # Enhance file details with download link
            file_details = enhance_message_file_details(file_details)

        # Create new message
        db_message = Message(
            chat_id=chat_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message,
            message_type=message_type,
            file_details=file_details
        )

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
