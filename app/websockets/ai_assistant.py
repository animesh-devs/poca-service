from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from app.db.database import get_db
from app.models.ai import AISession, AIMessage
from app.models.chat import Chat
from app.models.user import User
from app.dependencies import get_current_user_ws
from app.services.ai import get_ai_service
from app.websockets.connection_manager import manager

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_ai_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = None,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time AI chat"""
    # Authenticate user
    try:
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        current_user = await get_current_user_ws(token, db)
        if not current_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check if the session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Generate a unique client ID
        client_id = str(uuid.uuid4())

        # Accept connection
        await manager.connect(websocket, session_id, client_id)

        # Send welcome message
        welcome_message = {
            "type": "system",
            "content": "Connected to AI Assistant. You can start chatting now."
        }
        await manager.send_message(welcome_message, session_id, client_id)

        # Get AI service
        ai_service = get_ai_service()

        # Get previous messages for context
        previous_messages = db.query(AIMessage).filter(
            AIMessage.session_id == session_id
        ).order_by(AIMessage.timestamp.asc()).all()

        context = []
        for prev_msg in previous_messages:
            if prev_msg.message:
                context.append({"role": "user", "content": prev_msg.message})
            if prev_msg.response:
                context.append({"role": "assistant", "content": prev_msg.response})

        # Track question count
        question_count = len([msg for msg in context if msg["role"] == "user"])

        try:
            while True:
                # Receive message from WebSocket
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Extract message content
                message_content = message_data.get("message", "")

                if not message_content:
                    continue

                # Create a status message
                status_message = {
                    "type": "status",
                    "content": "Processing your message..."
                }
                await manager.send_message(status_message, session_id, client_id)

                # Create new AI message in database
                db_message = AIMessage(
                    session_id=session_id,
                    message=message_content
                )

                db.add(db_message)
                db.commit()
                db.refresh(db_message)

                # Add message to context
                context.append({"role": "user", "content": message_content})
                question_count += 1

                # Generate AI response
                response_data = await ai_service.generate_response(message_content, context)

                # Handle response based on type
                if isinstance(response_data, dict):
                    # Extract message and summary flag
                    response_message = response_data.get("message", "")
                    is_summary = response_data.get("isSummary", False)

                    # Update the message with the response
                    db_message.response = response_message
                    db_message.is_summary = is_summary
                else:
                    # Fallback for string responses
                    response_message = response_data
                    is_summary = question_count >= 5 and "summary" in response_message.lower()
                    db_message.response = response_message
                    db_message.is_summary = is_summary

                db.commit()

                # Add response to context
                context.append({"role": "assistant", "content": response_message})

                # Send response to client in the requested JSON format
                response_json = {
                    "message": response_message,
                    "isSummary": is_summary
                }

                # Wrap in a WebSocket message
                ws_response = {
                    "type": "ai_response",
                    "message_id": db_message.id,
                    "content": response_json,
                    "question_count": question_count
                }
                await manager.send_message(ws_response, session_id, client_id)

                # If this is a summary, send a notification
                if is_summary:
                    summary_notification = {
                        "type": "summary",
                        "content": "AI has generated a summary. You can edit it and send it to the doctor."
                    }
                    await manager.send_message(summary_notification, session_id, client_id)

        except WebSocketDisconnect:
            manager.disconnect(session_id, client_id)
            logger.info(f"Client {client_id} disconnected from AI session {session_id}")

        except Exception as e:
            logger.error(f"Error in WebSocket connection: {str(e)}")
            error_message = {
                "type": "error",
                "content": f"An error occurred: {str(e)}"
            }
            await manager.send_message(error_message, session_id, client_id)
            manager.disconnect(session_id, client_id)

    except Exception as e:
        logger.error(f"Error setting up WebSocket connection: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
