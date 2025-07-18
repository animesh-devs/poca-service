"""
Socket.IO Server Implementation - Clean Implementation
Provides native Socket.IO support with AI assistance similar to WebSocket implementation.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from app.db.database import get_db
from app.models.ai import AISession, AIMessage
from app.models.chat import Chat
from app.models.user import User, UserRole
from app.dependencies import get_current_user_ws
from app.services.ai import get_ai_service

logger = logging.getLogger(__name__)

# Global Socket.IO server instance
sio_server = None
active_sessions = {}

def create_socketio_server():
    """Create and configure Socket.IO server following official documentation"""
    global sio_server

    try:
        import socketio

        # Create AsyncServer for ASGI integration
        sio_server = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins="*",
            logger=False,  # Disable Socket.IO debug logging
            engineio_logger=False,  # Disable EngineIO debug logging
        )

        logger.info("Socket.IO server created successfully")

        # Register handlers directly on the server instance (official pattern)
        register_socketio_handlers()

        return sio_server

    except ImportError:
        logger.warning("Socket.IO module not available")
        return None
    except Exception as e:
        logger.error(f"Failed to create Socket.IO server: {e}")
        return None

def register_socketio_handlers():
    """Register Socket.IO event handlers following official documentation"""
    if not sio_server:
        logger.error("No Socket.IO server available for handler registration")
        return

    logger.info("Registering Socket.IO handlers")

    # Register catch-all handler for debugging (can be disabled in production)
    # @sio_server.on('*')
    # async def catch_all(event, sid, data):
    #     logger.debug(f"Socket.IO event: {event} from {sid}")

    # Register handlers for /socket.io namespace (where Postman connects)
    @sio_server.event(namespace='/socket.io')
    async def connect(sid, environ, auth):
        """Handle client connection to /socket.io namespace with optional authentication"""
        logger.info(f"Socket.IO client connected: {sid}")

        # Check for authentication in query string
        query_string = environ.get('QUERY_STRING', '')
        logger.debug(f"Query string: {query_string}")

        # Parse query parameters
        params = {}
        if query_string:
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value

        token = params.get('token')
        session_id = params.get('session_id')  # AI session ID from query params
        user_entity_id = params.get('user_entity_id')

        # Try to authenticate if token is provided
        auth_data = None
        if token:
            auth_data = await authenticate_socketio_connection(query_string)
            if auth_data:
                logger.info(f"Authenticated user: {auth_data['user'].email}")

                # Check if this is an AI session connection (WebSocket equivalent)
                if session_id:
                    # This is equivalent to WebSocket /ws/{session_id}?token={token}
                    try:
                        # Get database session
                        db = next(get_db())
                        current_user = auth_data['user']

                        # Verify AI session exists and user has access
                        ai_session = db.query(AISession).filter(AISession.id == session_id).first()
                        if not ai_session:
                            await sio_server.emit('error', {
                                'status': 'error',
                                'message': f'AI session {session_id} not found'
                            }, room=sid, namespace='/socket.io')
                            return False

                        # Get the associated chat
                        chat = db.query(Chat).filter(Chat.id == ai_session.chat_id).first()
                        if not chat:
                            await sio_server.emit('error', {
                                'status': 'error',
                                'message': f'Chat not found for AI session {session_id}'
                            }, room=sid, namespace='/socket.io')
                            return False

                        # Access control (same as WebSocket)
                        has_access = False

                        if current_user.role == UserRole.ADMIN:
                            has_access = True
                        elif current_user.role == UserRole.DOCTOR:
                            if user_entity_id == chat.doctor_id:
                                has_access = True
                        elif current_user.role == UserRole.PATIENT:
                            if user_entity_id == chat.patient_id:
                                from app.models.mapping import UserPatientRelation
                                relation = db.query(UserPatientRelation).filter(
                                    UserPatientRelation.user_id == current_user.id,
                                    UserPatientRelation.patient_id == chat.patient_id
                                ).first()
                                if relation:
                                    has_access = True

                        if not has_access:
                            logger.warning(f"User {current_user.id} denied access to AI session {session_id}")
                            await sio_server.emit('error', {
                                'status': 'error',
                                'message': 'Access denied to this AI session'
                            }, room=sid, namespace='/socket.io')
                            return False

                        # Store AI session data
                        auth_data['session_id'] = session_id
                        auth_data['ai_session_connected'] = True
                        active_sessions[sid] = auth_data

                        # Send AI session welcome message (WebSocket equivalent)
                        await sio_server.emit('connected', {
                            'type': 'system',
                            'content': 'Connected to AI Assistant. You can start chatting now.',
                            'session_id': session_id,
                            'user_id': current_user.id
                        }, room=sid, namespace='/socket.io')

                        logger.info(f"AI session {session_id} connected for user {current_user.email}")

                    except Exception as ai_error:
                        logger.error(f"AI session connection error: {ai_error}")
                        await sio_server.emit('error', {
                            'status': 'error',
                            'message': 'AI session connection failed'
                        }, room=sid, namespace='/socket.io')
                        return False
                else:
                    # Regular authenticated connection (no AI session)
                    active_sessions[sid] = auth_data
                    await sio_server.emit('connected', {
                        'message': f'Welcome {auth_data["user"].email}! You are authenticated and connected to Socket.IO',
                        'sid': sid,
                        'authenticated': True,
                        'user_id': auth_data['user_id']
                    }, room=sid, namespace='/socket.io')
            else:
                logger.warning(f"Authentication failed for {sid}")
                # Store as unauthenticated session
                active_sessions[sid] = {'user_id': 'unauthenticated', 'authenticated': False}

                await sio_server.emit('connected', {
                    'message': 'Connected but authentication failed. AI assistance requires authentication.',
                    'sid': sid,
                    'authenticated': False
                }, room=sid, namespace='/socket.io')
        else:
            # No authentication attempted - basic connection
            active_sessions[sid] = {'user_id': 'test-user', 'authenticated': False}

            await sio_server.emit('connected', {
                'message': 'Welcome! You are connected to /socket.io namespace (no authentication)',
                'sid': sid,
                'authenticated': False
            }, room=sid, namespace='/socket.io')

        return True

    @sio_server.event(namespace='/socket.io')
    async def disconnect(sid, reason):
        """Handle client disconnection from /socket.io namespace"""
        logger.info(f"Socket.IO client disconnected: {sid}")

        if sid in active_sessions:
            del active_sessions[sid]

    @sio_server.event(namespace='/socket.io')
    async def message(sid, data):
        """Handle message events - automatically routes to AI if AI session is connected"""
        logger.debug(f"Socket.IO message from {sid}")

        # Check if this is an AI session
        if sid in active_sessions and active_sessions[sid].get('ai_session_connected'):
            # Route to AI processing (WebSocket equivalent)
            await handle_ai_message(sid, data)
        else:
            # Regular message echo
            await sio_server.emit('message_echo', {
                'status': 'success',
                'message': f'Server received: {data}',
                'sid': sid
            }, room=sid, namespace='/socket.io')

    logger.info("Socket.IO handlers registered successfully")

async def handle_ai_message(sid, data):
    """Handle AI message processing (WebSocket equivalent logic)"""
    try:
        session_info = active_sessions[sid]
        session_id = session_info['session_id']

        # Parse message data
        if isinstance(data, str):
            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                message_data = {'message': data}
        else:
            message_data = data

        message_content = message_data.get('message', data if isinstance(data, str) else '')
        if not message_content:
            await sio_server.emit('error', {
                'status': 'error',
                'message': 'Message content is required'
            }, room=sid, namespace='/socket.io')
            return

        # Send status message
        await sio_server.emit('ai_status', {
            'type': 'status',
            'content': 'Processing your message...'
        }, room=sid, namespace='/socket.io')

        # Get database session
        db = next(get_db())

        # Get AI session and chat for context
        from app.models.ai import AISession
        from app.models.chat import Chat

        ai_session = db.query(AISession).filter(AISession.id == session_id).first()
        if not ai_session:
            await sio_server.emit('error', {
                'status': 'error',
                'message': 'AI session not found'
            }, room=sid, namespace='/socket.io')
            return

        chat = db.query(Chat).filter(Chat.id == ai_session.chat_id).first()
        if not chat:
            await sio_server.emit('error', {
                'status': 'error',
                'message': 'Chat not found for AI session'
            }, room=sid, namespace='/socket.io')
            return

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

        # Build context
        context = []
        question_count = 0
        for prev_msg in previous_messages[:-1]:  # Exclude current message
            if prev_msg.message:
                context.append({"role": "user", "content": prev_msg.message})
                question_count += 1
            if prev_msg.response:
                context.append({"role": "assistant", "content": prev_msg.response})

        # Add current message to context
        context.append({"role": "user", "content": message_content})
        question_count += 1

        # Get AI session and chat for context
        from app.models.ai import AISession
        from app.models.chat import Chat

        ai_session = db.query(AISession).filter(AISession.id == session_id).first()
        if not ai_session:
            await sio_server.emit('error', {
                'status': 'error',
                'message': 'AI session not found'
            }, room=sid, namespace='/socket.io')
            return

        chat = db.query(Chat).filter(Chat.id == ai_session.chat_id).first()
        if not chat:
            await sio_server.emit('error', {
                'status': 'error',
                'message': 'Chat not found for AI session'
            }, room=sid, namespace='/socket.io')
            return

        # Fetch patient and doctor context for AI prompt resolution
        from app.models.patient import Patient
        from app.models.doctor import Doctor
        from app.models.mapping import UserPatientRelation
        from app.models.case_history import CaseHistory
        from app.models.user import User, UserRole

        patient_data = None
        doctor_data = None
        case_summary = None
        patient_relation = None

        # Get current user for relation checking
        current_user = db.query(User).filter(User.id == session_info.get('user_id')).first()

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
            if current_user and current_user.role == UserRole.PATIENT:
                patient_relation = db.query(UserPatientRelation).filter(
                    UserPatientRelation.user_id == current_user.id,
                    UserPatientRelation.patient_id == patient.id
                ).first()

        # Get doctor information
        doctor = db.query(Doctor).filter(Doctor.id == chat.doctor_id).first()
        if doctor:
            doctor_data = doctor

        # Generate AI response with context
        response_data = await ai_service.generate_response(
            message_content,
            context,
            patient_data=patient_data,
            doctor_data=doctor_data,
            case_summary=case_summary,
            patient_relation=patient_relation
        )

        # Handle response
        if isinstance(response_data, dict):
            response_message = response_data.get("message", "")
            is_summary = response_data.get("isSummary", False)
        else:
            response_message = response_data
            is_summary = question_count >= 5 and "summary" in response_message.lower()

        # Update database
        db_message.response = response_message
        db_message.is_summary = is_summary
        db.commit()

        # Send AI response
        await sio_server.emit('ai_response', {
            'type': 'ai_response',
            'message_id': db_message.id,
            'content': {
                'message': response_message,
                'isSummary': is_summary
            },
            'question_count': question_count
        }, room=sid, namespace='/socket.io')

        logger.debug(f"AI response sent for session {session_id}")

    except Exception as e:
        logger.error(f"Error in AI message processing: {e}")
        await sio_server.emit('error', {
            'status': 'error',
            'message': 'AI message processing failed'
        }, room=sid, namespace='/socket.io')

# Clean implementation - all old handlers removed

# Clean implementation - all old handlers removed

async def authenticate_socketio_connection(query_string: str) -> Optional[Dict[str, Any]]:
    """Authenticate Socket.IO connection using token from query parameters (similar to WebSocket)"""
    try:
        # Parse query string parameters
        params = {}
        if query_string:
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value

        token = params.get('token')
        if not token:
            logger.warning("No token provided in Socket.IO connection")
            return None

        # Get user from database using WebSocket authentication method
        try:
            db = next(get_db())
            user = await get_current_user_ws(token, db)
            if not user:
                logger.warning("Invalid token or user not found in Socket.IO connection")
                return None
        except Exception as db_error:
            logger.error(f"Database error during authentication: {db_error}")
            return None

        logger.info(f"User authenticated: {user.email} (ID: {user.id})")

        return {
            'user_id': user.id,
            'user': user,
            'session_id': params.get('session_id'),
            'user_entity_id': params.get('user_entity_id'),
            'token': token
        }

    except Exception as e:
        logger.error(f"Authentication error in Socket.IO connection: {e}")
        return None

def get_socketio_app(fastapi_app=None):
    """Get Socket.IO ASGI application following official documentation"""
    if not sio_server:
        return None

    try:
        import socketio

        if fastapi_app:
            # Official pattern: Socket.IO can be combined with FastAPI
            socketio_app = socketio.ASGIApp(sio_server, fastapi_app)
            logger.info("Socket.IO integrated with FastAPI")
        else:
            # Official pattern: standalone Socket.IO ASGI app
            socketio_app = socketio.ASGIApp(sio_server)
            logger.info("Socket.IO standalone ASGI app created")

        return socketio_app

    except Exception as e:
        logger.error(f"Failed to create Socket.IO ASGI app: {e}")
        return None

def initialize_socketio():
    """Initialize Socket.IO server and handlers"""
    server = create_socketio_server()
    if server:
        # Handlers are already set up inline during server creation
        logger.info("Socket.IO server initialized successfully")
        return True
    return False

def get_active_sessions():
    """Get active Socket.IO sessions"""
    return active_sessions.copy()

def get_session_count():
    """Get count of active Socket.IO sessions"""
    return len(active_sessions)

def get_server():
    """Get the Socket.IO server instance"""
    return sio_server