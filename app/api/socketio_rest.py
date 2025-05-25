"""
Socket.IO-like REST API endpoints for HTTP polling compatibility.

This module provides REST API endpoints that mimic Socket.IO behavior
but work reliably with HTTP polling from tools like Postman.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import asyncio
import uuid
from datetime import datetime, timedelta

from jose import jwt
from app.config import settings
from app.db.database import get_db
from app.models.ai import AISession, AIMessage
from app.services.ai import get_ai_service
from sqlalchemy.orm import Session

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/socketio", tags=["Socket.IO REST"])

# Store active sessions and pending responses
active_sessions: Dict[str, Dict[str, Any]] = {}
pending_responses: Dict[str, List[Dict[str, Any]]] = {}


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        Dict containing token payload or None if invalid
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        exp: int = payload.get("exp")

        # Check if token has required fields
        if user_id is None or token_type is None or exp is None:
            return None

        # Check if token is an access token
        if token_type != "access":
            return None

        # Check if token has expired
        if datetime.fromtimestamp(exp) < datetime.now():
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None
    except Exception:
        return None


class SocketIOInitRequest(BaseModel):
    """Request model for Socket.IO session initialization"""
    pass


class SocketIOConnectRequest(BaseModel):
    """Request model for Socket.IO authentication"""
    token: str
    session_id: str
    user_entity_id: str


class SocketIOMessageRequest(BaseModel):
    """Request model for Socket.IO messages"""
    message: str
    token: str
    session_id: str
    user_entity_id: str


class SocketIOResponse(BaseModel):
    """Response model for Socket.IO operations"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    sid: Optional[str] = None


@router.get("/init")
async def initialize_socketio_session():
    """
    Initialize a Socket.IO-like session.

    Returns:
        Dict containing session ID and connection parameters
    """
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Store session info
        active_sessions[session_id] = {
            'created_at': datetime.now(),
            'authenticated': False
        }

        # Initialize pending responses queue
        pending_responses[session_id] = []

        logger.info(f"✅ Socket.IO REST session initialized: {session_id}")

        return {
            "sid": session_id,
            "upgrades": ["websocket"],
            "pingInterval": 25000,
            "pingTimeout": 60000,
            "maxPayload": 1000000
        }

    except Exception as e:
        logger.error(f"❌ Failed to initialize Socket.IO session: {e}")
        raise HTTPException(status_code=500, detail=f"Session initialization failed: {str(e)}")


@router.post("/connect/{sid}")
async def connect_socketio_session(sid: str, request: SocketIOConnectRequest):
    """
    Authenticate a Socket.IO-like session.

    Args:
        sid: Session ID
        request: Authentication data

    Returns:
        Connection confirmation
    """
    try:
        # Check if session exists
        if sid not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify JWT token
        try:
            payload = verify_token(request.token)
            user_id = payload.get("sub")

            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid authentication token")

        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

        # Update session with auth info
        active_sessions[sid].update({
            'authenticated': True,
            'user_id': user_id,
            'ai_session_id': request.session_id,
            'user_entity_id': request.user_entity_id,
            'token': request.token
        })

        # Add connection confirmation to pending responses
        pending_responses[sid].append({
            'event': 'connected',
            'data': {
                'status': 'success',
                'message': 'Connected to AI Assistant via Socket.IO REST',
                'session_id': request.session_id,
                'user_id': user_id
            },
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"✅ Socket.IO REST session authenticated: {sid}, User: {user_id}")

        return SocketIOResponse(
            status="success",
            message="Authentication successful",
            sid=sid
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Socket.IO REST authentication failed: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/ai_message/{sid}")
async def send_ai_message(sid: str, request: SocketIOMessageRequest, db: Session = Depends(get_db)):
    """
    Send a message to the AI assistant.

    Args:
        sid: Session ID
        request: Message data
        db: Database session

    Returns:
        Message processing confirmation
    """
    try:
        # Check if session exists and is authenticated
        if sid not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        session_info = active_sessions[sid]
        if not session_info.get('authenticated'):
            raise HTTPException(status_code=401, detail="Session not authenticated")

        # Verify token matches session
        if session_info.get('token') != request.token:
            raise HTTPException(status_code=401, detail="Token mismatch")

        # Get AI service
        ai_service = get_ai_service()

        # Get previous messages for context
        previous_messages = db.query(AIMessage).filter(
            AIMessage.session_id == request.session_id
        ).order_by(AIMessage.timestamp.asc()).all()

        context = []
        for prev_msg in previous_messages:
            if prev_msg.message:
                context.append({"role": "user", "content": prev_msg.message})
            if prev_msg.response:
                context.append({"role": "assistant", "content": prev_msg.response})

        # Track question count
        question_count = len([msg for msg in context if msg["role"] == "user"])

        # Create new AI message in database
        db_message = AIMessage(
            session_id=request.session_id,
            message=request.message
        )

        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # Add message to context
        context.append({"role": "user", "content": request.message})
        question_count += 1

        # Generate AI response
        response_data = await ai_service.generate_response(request.message, context)

        # Handle response based on type
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

        # Add AI response to pending responses
        pending_responses[sid].append({
            'event': 'ai_response',
            'data': {
                'status': 'success',
                'message': response_message,
                'session_id': request.session_id,
                'message_id': db_message.id,
                'is_summary': is_summary,
                'question_count': question_count
            },
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"✅ AI message processed for session: {sid}")

        return SocketIOResponse(
            status="success",
            message="AI message processed",
            sid=sid
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI message processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI message processing failed: {str(e)}")


@router.get("/poll/{sid}")
async def poll_responses(sid: str):
    """
    Poll for pending responses.

    Args:
        sid: Session ID

    Returns:
        List of pending responses
    """
    try:
        # Check if session exists
        if sid not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get pending responses
        responses = pending_responses.get(sid, [])

        # Clear pending responses after returning them
        pending_responses[sid] = []

        return {
            "status": "success",
            "responses": responses,
            "count": len(responses)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Polling failed: {e}")
        raise HTTPException(status_code=500, detail=f"Polling failed: {str(e)}")


@router.delete("/disconnect/{sid}")
async def disconnect_session(sid: str):
    """
    Disconnect and cleanup session.

    Args:
        sid: Session ID

    Returns:
        Disconnection confirmation
    """
    try:
        # Clean up session data
        if sid in active_sessions:
            del active_sessions[sid]

        if sid in pending_responses:
            del pending_responses[sid]

        logger.info(f"✅ Socket.IO REST session disconnected: {sid}")

        return SocketIOResponse(
            status="success",
            message="Session disconnected",
            sid=sid
        )

    except Exception as e:
        logger.error(f"❌ Disconnection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Disconnection failed: {str(e)}")
