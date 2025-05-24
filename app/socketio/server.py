import socketio
import logging

from app.socketio.connection_manager import socketio_manager
from app.socketio.ai_assistant import create_ai_assistant_handlers

# Configure logging
logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # Configure based on your CORS requirements
    logger=True,
    engineio_logger=True
)

# Set up connection manager
socketio_manager.set_socketio_server(sio)

# Create AI assistant handlers for the main namespace
create_ai_assistant_handlers(sio)

# Create ASGI app
socketio_app = socketio.ASGIApp(sio)

def get_socketio_app():
    """Get the Socket.IO ASGI app"""
    return socketio_app

def get_socketio_server():
    """Get the Socket.IO server instance"""
    return sio
