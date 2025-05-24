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
from app.models.user import User, UserRole
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
    user_entity_id: str = None,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time AI chat"""
    # Authenticate user
    try:
        if not token:
            logger.warning("WebSocket connection attempt without token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        current_user = await get_current_user_ws(token, db)
        if not current_user:
            logger.warning("WebSocket authentication failed")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Extract user-entity-id from headers
        headers = dict(websocket.headers)
        logger.info(f"WebSocket headers: {headers}")

        # Get user-entity-id from query params if not in headers
        if not user_entity_id:
            user_entity_id = headers.get("user-entity-id")

        logger.info(f"User entity ID: {user_entity_id}, User role: {current_user.role}")

        # If user_entity_id is not provided, try to determine it
        if not user_entity_id:
            if current_user.role in [UserRole.DOCTOR, UserRole.HOSPITAL] and current_user.profile_id:
                user_entity_id = current_user.profile_id
                logger.info(f"Using profile_id {user_entity_id} for user {current_user.id}")
            elif current_user.role == UserRole.PATIENT:
                # Try to find a "self" relation first
                from app.models.mapping import UserPatientRelation, RelationType
                self_relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.relation == RelationType.SELF
                ).first()

                if self_relation:
                    user_entity_id = self_relation.patient_id
                    logger.info(f"Using self relation patient ID {user_entity_id} for user {current_user.id}")
                else:
                    # Try to find any relation
                    any_relation = db.query(UserPatientRelation).filter(
                        UserPatientRelation.user_id == current_user.id
                    ).first()

                    if any_relation:
                        user_entity_id = any_relation.patient_id
                        logger.info(f"Using patient relation {user_entity_id} for user {current_user.id}")
            elif current_user.role == UserRole.ADMIN:
                user_entity_id = current_user.id
                logger.info(f"Using admin user ID {user_entity_id} as entity ID")

        # Check if the session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            logger.warning(f"AI session not found: {session_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get the associated chat to check user access
        chat = db.query(Chat).filter(Chat.id == session.chat_id).first()
        if not chat:
            logger.warning(f"Chat not found for AI session: {session_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check if the user has access to the chat
        has_access = False

        if current_user.role == UserRole.ADMIN:
            # Admin has access to all chats
            has_access = True
            logger.info(f"Admin user {current_user.id} accessing AI session {session_id}")
        elif current_user.role == UserRole.DOCTOR:
            # For doctors: user_entity_id should be doctor_id (same as user.profile_id)
            # Check if this doctor is part of the chat
            if user_entity_id == chat.doctor_id:
                has_access = True
                logger.info(f"Doctor {user_entity_id} accessing AI session {session_id}")
            elif not user_entity_id and current_user.profile_id == chat.doctor_id:
                # Fallback: check profile_id if user_entity_id not provided
                has_access = True
                logger.info(f"Doctor {current_user.profile_id} accessing AI session {session_id} (using profile_id)")
            else:
                logger.warning(f"Doctor {current_user.id} (entity_id: {user_entity_id}, profile_id: {current_user.profile_id}) denied access to AI session {session_id} - not assigned to chat {chat.id}")
        elif current_user.role == UserRole.PATIENT:
            # For patients: user_entity_id should be patient_id (from user-patient-relation mapping)
            # Check if this patient is part of the chat
            if user_entity_id == chat.patient_id:
                # Verify that this user actually has a relation to this patient
                from app.models.mapping import UserPatientRelation
                relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == chat.patient_id
                ).first()

                if relation:
                    has_access = True
                    logger.info(f"Patient user {current_user.id} with relation '{relation.relation}' accessing AI session {session_id} for patient {chat.patient_id}")
                else:
                    logger.warning(f"Patient user {current_user.id} has no relation to patient {chat.patient_id} for AI session {session_id}")
            else:
                # If user_entity_id doesn't match, check if user has any relation to this chat's patient
                from app.models.mapping import UserPatientRelation
                relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == chat.patient_id
                ).first()

                if relation:
                    has_access = True
                    logger.info(f"Patient user {current_user.id} with relation '{relation.relation}' accessing AI session {session_id} for patient {chat.patient_id} (auto-resolved)")
                else:
                    logger.warning(f"Patient user {current_user.id} has no relation to patient {chat.patient_id} for AI session {session_id}")
        elif current_user.role == UserRole.HOSPITAL:
            # For hospitals: user_entity_id should be hospital_id (same as user.profile_id)
            # Hospitals can access sessions if they have relationships with the doctor or patient
            if user_entity_id and user_entity_id == current_user.profile_id:
                # Check if hospital has relationship with the doctor or patient in this chat
                from app.models.mapping import HospitalDoctorMapping, HospitalPatientMapping

                doctor_relation = db.query(HospitalDoctorMapping).filter(
                    HospitalDoctorMapping.hospital_id == user_entity_id,
                    HospitalDoctorMapping.doctor_id == chat.doctor_id
                ).first()

                patient_relation = db.query(HospitalPatientMapping).filter(
                    HospitalPatientMapping.hospital_id == user_entity_id,
                    HospitalPatientMapping.patient_id == chat.patient_id
                ).first()

                if doctor_relation or patient_relation:
                    has_access = True
                    logger.info(f"Hospital {user_entity_id} accessing AI session {session_id} (has relationship with chat participants)")
                else:
                    logger.warning(f"Hospital {user_entity_id} has no relationship with chat participants for AI session {session_id}")
            else:
                logger.warning(f"Hospital user {current_user.id} invalid entity_id {user_entity_id} for AI session {session_id}")

        if not has_access:
            logger.warning(f"User {current_user.id} (role: {current_user.role}, entity_id: {user_entity_id}) denied access to AI session {session_id}")
            logger.warning(f"Chat details - doctor_id: {chat.doctor_id}, patient_id: {chat.patient_id}")
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
