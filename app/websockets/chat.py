from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from app.db.database import get_db
from app.models.chat import Chat, Message, MessageType
from app.models.user import User, UserRole
from app.dependencies import get_current_user_ws
from app.websockets.connection_manager import manager

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{chat_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    chat_id: str,
    token: str = None,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time chat"""
    # Authenticate user
    try:
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        current_user = await get_current_user_ws(token, db)
        if not current_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check if the chat exists
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check if user has access to this chat
        has_access = False
        if current_user.role == UserRole.ADMIN:
            has_access = True
        elif current_user.role == UserRole.DOCTOR:
            # Check if the doctor is part of this chat
            if current_user.profile_id and current_user.profile_id == chat.doctor_id:
                has_access = True
        elif current_user.role == UserRole.PATIENT:
            # Check if the patient is part of this chat
            if current_user.profile_id and current_user.profile_id == chat.patient_id:
                has_access = True

        if not has_access:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Generate a unique client ID
        client_id = str(uuid.uuid4())

        # Accept connection
        await manager.connect(websocket, chat_id, client_id)

        # Send welcome message
        welcome_message = {
            "type": "system",
            "content": f"Connected to chat {chat_id}. You can start chatting now."
        }
        await manager.send_message(welcome_message, chat_id, client_id)

        # Get previous messages for context (last 50 messages)
        previous_messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(Message.timestamp.desc()).limit(50).all()

        # Send previous messages to the client
        if previous_messages:
            history_message = {
                "type": "history",
                "messages": [
                    {
                        "id": msg.id,
                        "sender_id": msg.sender_id,
                        "receiver_id": msg.receiver_id,
                        "content": msg.message,
                        "message_type": msg.message_type.value,
                        "timestamp": msg.timestamp.isoformat(),
                        "is_read": msg.is_read
                    } for msg in reversed(previous_messages)
                ]
            }
            await manager.send_message(history_message, chat_id, client_id)

        try:
            while True:
                # Receive message from WebSocket
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Extract message content
                message_content = message_data.get("content", "")
                message_type = message_data.get("message_type", "text")
                file_details = message_data.get("file_details", None)

                if not message_content:
                    continue

                # Determine sender and receiver IDs
                sender_id = current_user.id
                if current_user.role == UserRole.DOCTOR:
                    receiver_id = chat.patient_id
                else:
                    receiver_id = chat.doctor_id

                # Create new message in database
                db_message = Message(
                    chat_id=chat_id,
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    message=message_content,
                    message_type=MessageType(message_type),
                    file_details=file_details,
                    is_read=False
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

                # Broadcast message to all clients in the chat
                message_broadcast = {
                    "type": "message",
                    "message": {
                        "id": db_message.id,
                        "sender_id": db_message.sender_id,
                        "receiver_id": db_message.receiver_id,
                        "content": db_message.message,
                        "message_type": db_message.message_type.value,
                        "timestamp": db_message.timestamp.isoformat(),
                        "is_read": db_message.is_read
                    }
                }

                # Send to all clients in the chat
                connected_clients = manager.get_connected_clients(chat_id)
                for connected_client in connected_clients:
                    await manager.send_message(message_broadcast, chat_id, connected_client)

        except WebSocketDisconnect:
            manager.disconnect(chat_id, client_id)
            logger.info(f"Client {client_id} disconnected from chat {chat_id}")

        except Exception as e:
            logger.error(f"Error in WebSocket connection: {str(e)}")
            error_message = {
                "type": "error",
                "content": f"An error occurred: {str(e)}"
            }
            await manager.send_message(error_message, chat_id, client_id)
            manager.disconnect(chat_id, client_id)

    except Exception as e:
        logger.error(f"Error setting up WebSocket connection: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
