import socketio
import logging

from app.db.database import get_db
from app.models.ai import AISession, AIMessage
from app.models.chat import Chat
from app.models.user import UserRole
from app.services.ai import get_ai_service
from app.socketio.connection_manager import socketio_manager
from app.socketio.auth import authenticate_socketio_user

# Configure logging
logger = logging.getLogger(__name__)

def create_ai_assistant_handlers(sio: socketio.AsyncServer):
    """Create Socket.IO event handlers for AI assistant"""

    @sio.event
    async def connect(sid, environ, auth):
        """Handle Socket.IO connection for AI assistant"""
        try:
            # Get database session
            db_gen = get_db()
            db = next(db_gen)

            try:
                # Authenticate user
                if not auth or not isinstance(auth, dict):
                    logger.warning(f"Socket.IO AI connection {sid} rejected: Invalid auth data")
                    await sio.disconnect(sid)
                    return False

                user = await authenticate_socketio_user(auth, db)
                if not user:
                    logger.warning(f"Socket.IO AI connection {sid} rejected: Authentication failed")
                    await sio.disconnect(sid)
                    return False

                # Extract session_id and user_entity_id from auth
                session_id = auth.get('session_id')
                user_entity_id = auth.get('user_entity_id')

                if not session_id:
                    logger.warning(f"Socket.IO AI connection {sid} rejected: Missing session_id")
                    await sio.disconnect(sid)
                    return False

                # Validate AI session exists
                ai_session = db.query(AISession).filter(AISession.id == session_id).first()
                if not ai_session:
                    logger.warning(f"Socket.IO AI connection {sid} rejected: AI session {session_id} not found")
                    await sio.disconnect(sid)
                    return False

                # Get the associated chat
                chat = db.query(Chat).filter(Chat.id == ai_session.chat_id).first()
                if not chat:
                    logger.warning(f"Socket.IO AI connection {sid} rejected: Chat {ai_session.chat_id} not found")
                    await sio.disconnect(sid)
                    return False

                # Determine user_entity_id if not provided (same logic as WebSocket)
                if not user_entity_id:
                    if user.role in [UserRole.DOCTOR, UserRole.HOSPITAL] and user.profile_id:
                        user_entity_id = user.profile_id
                        logger.info(f"Using profile_id {user_entity_id} for user {user.id}")
                    elif user.role == UserRole.PATIENT:
                        # Try to find a "self" relation first
                        from app.models.mapping import UserPatientRelation, RelationType
                        self_relation = db.query(UserPatientRelation).filter(
                            UserPatientRelation.user_id == user.id,
                            UserPatientRelation.relation == RelationType.SELF
                        ).first()

                        if self_relation:
                            user_entity_id = self_relation.patient_id
                            logger.info(f"Using self relation patient ID {user_entity_id} for user {user.id}")
                        else:
                            # Try to find any relation
                            any_relation = db.query(UserPatientRelation).filter(
                                UserPatientRelation.user_id == user.id
                            ).first()

                            if any_relation:
                                user_entity_id = any_relation.patient_id
                                logger.info(f"Using patient relation {user_entity_id} for user {user.id}")
                    elif user.role == UserRole.ADMIN:
                        user_entity_id = user.id
                        logger.info(f"Using admin user ID {user_entity_id} as entity ID")

                # Check access permissions
                has_access = False

                if user.role == UserRole.ADMIN:
                    # Admin has access to all chats
                    has_access = True
                    logger.info(f"Admin user {user.id} accessing AI session {session_id}")
                elif user.role == UserRole.DOCTOR:
                    # For doctors: user_entity_id should be doctor_id (same as user.profile_id)
                    # Check if this doctor is part of the chat
                    if user_entity_id == chat.doctor_id:
                        has_access = True
                        logger.info(f"Doctor {user_entity_id} accessing AI session {session_id}")
                    elif not user_entity_id and user.profile_id == chat.doctor_id:
                        # Fallback: check profile_id if user_entity_id not provided
                        has_access = True
                        logger.info(f"Doctor {user.profile_id} accessing AI session {session_id} (using profile_id)")
                    else:
                        logger.warning(f"Doctor {user.id} (entity_id: {user_entity_id}, profile_id: {user.profile_id}) denied access to AI session {session_id} - not assigned to chat {chat.id}")
                elif user.role == UserRole.PATIENT:
                    # For patients: user_entity_id should be patient_id (from user-patient-relation mapping)
                    # Check if this patient is part of the chat
                    if user_entity_id == chat.patient_id:
                        # Verify that this user actually has a relation to this patient
                        from app.models.mapping import UserPatientRelation
                        relation = db.query(UserPatientRelation).filter(
                            UserPatientRelation.user_id == user.id,
                            UserPatientRelation.patient_id == chat.patient_id
                        ).first()

                        if relation:
                            has_access = True
                            logger.info(f"Patient user {user.id} with relation '{relation.relation}' accessing AI session {session_id} for patient {chat.patient_id}")
                        else:
                            logger.warning(f"Patient user {user.id} has no relation to patient {chat.patient_id} for AI session {session_id}")
                    else:
                        # If user_entity_id doesn't match, check if user has any relation to this chat's patient
                        from app.models.mapping import UserPatientRelation
                        relation = db.query(UserPatientRelation).filter(
                            UserPatientRelation.user_id == user.id,
                            UserPatientRelation.patient_id == chat.patient_id
                        ).first()

                        if relation:
                            has_access = True
                            logger.info(f"Patient user {user.id} with relation '{relation.relation}' accessing AI session {session_id} for patient {chat.patient_id} (auto-resolved)")
                        else:
                            logger.warning(f"Patient user {user.id} has no relation to patient {chat.patient_id} for AI session {session_id}")
                elif user.role == UserRole.HOSPITAL:
                    # For hospitals: user_entity_id should be hospital_id (same as user.profile_id)
                    # Hospitals can access sessions if they have relationships with the doctor or patient
                    if user_entity_id and user_entity_id == user.profile_id:
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
                        logger.warning(f"Hospital user {user.id} invalid entity_id {user_entity_id} for AI session {session_id}")

                if not has_access:
                    logger.warning(f"User {user.id} (role: {user.role}, entity_id: {user_entity_id}) denied access to AI session {session_id}")
                    logger.warning(f"Chat details - doctor_id: {chat.doctor_id}, patient_id: {chat.patient_id}")
                    await sio.disconnect(sid)
                    return False

                # Connect to session
                client_id = await socketio_manager.connect(sid, session_id)

                # Store session info in the socket's session
                await sio.save_session(sid, {
                    'user_id': user.id,
                    'session_id': session_id,
                    'client_id': client_id,
                    'user_entity_id': user_entity_id,
                    'user_role': user.role.value
                })

                # Send welcome message
                welcome_message = {
                    "type": "system",
                    "content": "Connected to AI Assistant. You can start chatting now."
                }
                await socketio_manager.send_message(welcome_message, session_id, client_id)

                logger.info(f"Socket.IO AI client {client_id} connected to session {session_id}")
                return True

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Socket.IO AI connection error for {sid}: {str(e)}")
            await sio.disconnect(sid)
            return False

    @sio.event
    async def disconnect(sid):
        """Handle Socket.IO disconnection"""
        try:
            await socketio_manager.disconnect(sid)
        except Exception as e:
            logger.error(f"Socket.IO AI disconnect error for {sid}: {str(e)}")

    @sio.event
    async def ai_message(sid, data):
        """Handle AI message from client"""
        try:
            # Get session info
            session_info = await sio.get_session(sid)
            if not session_info:
                logger.warning(f"Socket.IO AI message from {sid}: No session info")
                return

            session_id = session_info.get('session_id')
            client_id = session_info.get('client_id')

            if not session_id or not client_id:
                logger.warning(f"Socket.IO AI message from {sid}: Missing session or client ID")
                return

            # Extract message content
            message_content = data.get("message", "") if isinstance(data, dict) else str(data)

            if not message_content:
                logger.warning(f"Socket.IO AI message from {sid}: Empty message")
                return

            # Get database session
            db_gen = get_db()
            db = next(db_gen)

            try:
                # Send status message
                status_message = {
                    "type": "status",
                    "content": "Processing your message..."
                }
                await socketio_manager.send_message(status_message, session_id, client_id)

                # Create new AI message in database
                db_message = AIMessage(
                    session_id=session_id,
                    message=message_content
                )

                db.add(db_message)
                db.commit()
                db.refresh(db_message)

                # Get AI service and previous messages for context
                ai_service = get_ai_service()

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

                # Generate AI response
                response_data = await ai_service.generate_response(message_content, context)

                # Handle response based on type (same logic as WebSocket)
                if isinstance(response_data, dict):
                    response_message = response_data.get("message", "")
                    is_summary = response_data.get("isSummary", False)

                    db_message.response = response_message
                    db_message.is_summary = is_summary
                else:
                    response_message = response_data
                    is_summary = question_count >= 5 and "summary" in response_message.lower()
                    db_message.response = response_message
                    db_message.is_summary = is_summary

                db.commit()

                # Send response to client
                response_json = {
                    "message": response_message,
                    "isSummary": is_summary
                }

                ws_response = {
                    "type": "ai_response",
                    "message_id": db_message.id,
                    "content": response_json,
                    "question_count": question_count
                }
                await socketio_manager.send_message(ws_response, session_id, client_id)

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Socket.IO AI message error for {sid}: {str(e)}")
            # Send error message to client
            error_message = {
                "type": "error",
                "content": "An error occurred while processing your message."
            }
            try:
                session_info = await sio.get_session(sid)
                if session_info:
                    await socketio_manager.send_message(
                        error_message,
                        session_info.get('session_id'),
                        session_info.get('client_id')
                    )
            except:
                pass
