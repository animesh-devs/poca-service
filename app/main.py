from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
import logging
from datetime import datetime

from app.config import settings
from app.utils.passlib_patch import patch_passlib_bcrypt
from app.db.database import engine, Base
from app.api import (
    auth,
    users,
    hospitals,
    ai,
    patients,
    patients_router,
    doctors,
    mappings,
    chats,
    messages,
    appointments,
    suggestions,
    documents,
    # socketio_rest  # Temporarily disabled to avoid conflicts
)
from app.websockets import ai_assistant, chat

from app.errors import http_exception_handler, validation_exception_handler
from app.utils.openapi import custom_openapi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Apply passlib patch for bcrypt 4.0.0+ compatibility
patch_passlib_bcrypt()

# Create database tables
Base.metadata.create_all(bind=engine)

# Load profile photos into memory storage on startup
try:
    from app.startup.profile_photos import load_profile_photos_into_storage
    load_profile_photos_into_storage()
except Exception as e:
    logging.getLogger(__name__).warning(f"Failed to load profile photos on startup: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A comprehensive service for doctor-patient communication with AI assistance",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# Note: We're using a decorator approach instead of middleware for standardizing responses
# This is because middleware has issues with streaming responses
# See app/utils/decorators.py for the implementation

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# Use custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(hospitals.router, prefix=f"{settings.API_V1_PREFIX}/hospitals", tags=["Hospitals"])
app.include_router(patients.router, prefix=f"{settings.API_V1_PREFIX}/patients", tags=["Patient Case History"])
app.include_router(patients_router.router, prefix=f"{settings.API_V1_PREFIX}/patients", tags=["Patients"])
app.include_router(doctors.router, prefix=f"{settings.API_V1_PREFIX}/doctors", tags=["Doctors"])
app.include_router(ai.router, prefix=f"{settings.API_V1_PREFIX}/ai", tags=["AI Assistant"])
app.include_router(ai_assistant.router, prefix=f"{settings.API_V1_PREFIX}/ai-assistant", tags=["AI Assistant WebSocket"])
app.include_router(chat.router, prefix=f"{settings.API_V1_PREFIX}/chats", tags=["Chat WebSocket"])
app.include_router(mappings.router, prefix=f"{settings.API_V1_PREFIX}/mappings", tags=["Mappings"])
app.include_router(chats.router, prefix=f"{settings.API_V1_PREFIX}/chats", tags=["Chats"])
app.include_router(messages.router, prefix=f"{settings.API_V1_PREFIX}/messages", tags=["Messages"])
app.include_router(appointments.router, prefix=f"{settings.API_V1_PREFIX}/appointments", tags=["Appointments"])
app.include_router(suggestions.router, prefix=f"{settings.API_V1_PREFIX}/suggestions", tags=["Suggestions"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["Documents"])
# Temporarily disable Socket.IO REST API to avoid conflicts with native Socket.IO
# app.include_router(socketio_rest.router)

# Socket.IO Integration
import logging
logger = logging.getLogger(__name__)

SOCKETIO_AVAILABLE = False

try:
    import socketio  # noqa: F401
    SOCKETIO_AVAILABLE = True
    logger.debug("Socket.IO module available")
except ImportError:
    logger.info("Socket.IO not available - continuing without native support")

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "status_code": status.HTTP_200_OK,
        "status": True,
        "message": "Welcome to POCA Service API",
        "data": {
            "name": settings.PROJECT_NAME,
            "description": "A comprehensive service for doctor-patient communication with AI assistance",
            "version": "1.0.0",
            "documentation": f"{settings.API_V1_PREFIX}/docs"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status_code": status.HTTP_200_OK,
        "status": True,
        "message": "Service is healthy",
        "data": {
            "service": "POCA API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "rest_api": True,
                "websocket": True,
                "socketio_native": SOCKETIO_AVAILABLE
            }
        }
    }

@app.get("/socketio-status")
def socketio_status():
    """Check Socket.IO native support status"""
    if SOCKETIO_AVAILABLE:
        try:
            from app.socketio_server import get_session_count
            return {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Socket.IO status",
                "data": {
                    "socketio_available": True,
                    "connection_url": "ws://localhost:8000/socket.io/",
                    "active_sessions": get_session_count(),
                    "supported_events": ["connect", "message", "ai_message", "disconnect"],
                    "authentication": "Required (token, user_entity_id, session_id)",
                    "note": "Socket.IO server with authentication similar to WebSocket"
                }
            }
        except Exception as e:
            return {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Socket.IO status",
                "data": {
                    "socketio_available": False,
                    "error": str(e),
                    "note": "Socket.IO server not properly initialized"
                }
            }
    else:
        return {
            "status_code": status.HTTP_200_OK,
            "status": True,
            "message": "Socket.IO status",
            "data": {
                "socketio_available": False,
                "reason": "Socket.IO module not installed",
                "install_command": "pip install python-socketio>=5.8.0",
                "note": "All existing APIs and WebSocket endpoints work normally"
            }
        }

@app.get("/test-socketio-connection")
def test_socketio_connection():
    """Test Socket.IO server connection"""
    if SOCKETIO_AVAILABLE:
        try:
            from app.socketio_server import get_session_count, get_server

            sio_server = get_server()

            # Check if server is properly initialized
            server_info = {
                "server_created": sio_server is not None,
                "active_sessions": get_session_count(),
                "server_type": str(type(sio_server)) if sio_server else None,
                "handlers_registered": bool(sio_server and hasattr(sio_server, 'handlers') and sio_server.handlers),
                "namespaces": list(sio_server.handlers.keys()) if sio_server and hasattr(sio_server, 'handlers') else []
            }

            return {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Socket.IO server test",
                "data": server_info
            }
        except Exception as e:
            return {
                "status_code": status.HTTP_200_OK,
                "status": False,
                "message": "Socket.IO server test failed",
                "data": {"error": str(e)}
            }
    else:
        return {
            "status_code": status.HTTP_200_OK,
            "status": False,
            "message": "Socket.IO not available",
            "data": {"socketio_available": False}
        }

@app.get("/socketio-test-page")
def socketio_test_page():
    """Simple HTML page to test Socket.IO connection"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Socket.IO Test</title>
        <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    </head>
    <body>
        <h1>Socket.IO Test Page</h1>
        <div id="status">Connecting...</div>
        <div id="messages"></div>
        <button onclick="sendTestMessage()">Send Test Message</button>

        <script>
            const socket = io('ws://localhost:8000', {
                path: '/socket.io/',
                query: { test: 'true' }
            });

            socket.on('connect', function() {
                document.getElementById('status').innerHTML = 'Connected! SID: ' + socket.id;
                console.log('Connected to Socket.IO server');
            });

            socket.on('connected', function(data) {
                console.log('Server confirmation:', data);
                document.getElementById('messages').innerHTML += '<p>Server: ' + data.message + '</p>';
            });

            socket.on('disconnect', function() {
                document.getElementById('status').innerHTML = 'Disconnected';
                console.log('Disconnected from Socket.IO server');
            });

            socket.on('message_echo', function(data) {
                console.log('Message echo:', data);
                document.getElementById('messages').innerHTML += '<p>Echo: ' + data.message + '</p>';
            });

            function sendTestMessage() {
                socket.emit('message', { message: 'Hello from test page!' });
            }
        </script>
    </body>
    </html>
    """

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

@app.get("/socketio-auth-test-page")
def socketio_auth_test_page():
    """HTML page to test Socket.IO connection with authentication"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Socket.IO Auth Test</title>
        <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    </head>
    <body>
        <h1>Socket.IO Authentication Test</h1>
        <div>
            <label>Token:</label><br>
            <input type="text" id="token" style="width: 500px;" placeholder="Enter JWT token">
        </div>
        <div>
            <label>User Entity ID:</label><br>
            <input type="text" id="user_entity_id" style="width: 300px;" placeholder="Enter user entity ID">
        </div>
        <div>
            <label>Session ID:</label><br>
            <input type="text" id="session_id" style="width: 300px;" value="test-session">
        </div>
        <button onclick="connectWithAuth()">Connect with Authentication</button>
        <button onclick="disconnect()">Disconnect</button>
        <br><br>
        <div id="status">Not connected</div>
        <div id="messages"></div>
        <button onclick="sendTestMessage()">Send Test Message</button>

        <script>
            let socket = null;

            function connectWithAuth() {
                const token = document.getElementById('token').value;
                const userEntityId = document.getElementById('user_entity_id').value;
                const sessionId = document.getElementById('session_id').value;

                if (!token || !userEntityId) {
                    alert('Please enter token and user entity ID');
                    return;
                }

                if (socket) {
                    socket.disconnect();
                }

                socket = io('ws://localhost:8000', {
                    path: '/socket.io/',
                    query: {
                        token: token,
                        user_entity_id: userEntityId,
                        session_id: sessionId
                    }
                });

                socket.on('connect', function() {
                    document.getElementById('status').innerHTML = 'Connected! SID: ' + socket.id;
                    console.log('Connected to Socket.IO server with auth');
                });

                socket.on('connected', function(data) {
                    console.log('Server confirmation:', data);
                    document.getElementById('messages').innerHTML += '<p>Server: ' + data.message + '</p>';
                });

                socket.on('welcome', function(data) {
                    console.log('Welcome message:', data);
                    document.getElementById('messages').innerHTML += '<p style="color: green;">Welcome: ' + data.message + '</p>';
                });

                socket.on('server_message', function(data) {
                    console.log('Server message:', data);
                    document.getElementById('messages').innerHTML += '<p style="color: blue;">Server: ' + data.message + '</p>';
                });

                socket.on('disconnect', function() {
                    document.getElementById('status').innerHTML = 'Disconnected';
                    console.log('Disconnected from Socket.IO server');
                });

                socket.on('message_echo', function(data) {
                    console.log('Message echo:', data);
                    document.getElementById('messages').innerHTML += '<p>Echo: ' + data.message + '</p>';
                });

                socket.on('error', function(data) {
                    console.log('Error:', data);
                    document.getElementById('messages').innerHTML += '<p style="color: red;">Error: ' + data.message + '</p>';
                });
            }

            function disconnect() {
                if (socket) {
                    socket.disconnect();
                    socket = null;
                }
            }

            function sendTestMessage() {
                if (socket) {
                    socket.emit('message', { message: 'Hello with authentication!' });
                }
            }
        </script>
    </body>
    </html>
    """

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)

@app.post("/send-socketio-message")
def send_socketio_message(message: str = "Test message from server"):
    """Send a message to all connected Socket.IO clients"""
    if SOCKETIO_AVAILABLE:
        try:
            from app.socketio_server import get_server, get_active_sessions

            sio_server = get_server()
            active_sessions = get_active_sessions()

            if not sio_server:
                return {
                    "status_code": status.HTTP_200_OK,
                    "status": False,
                    "message": "Socket.IO server not available",
                    "data": {}
                }

            if not active_sessions:
                return {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "No active Socket.IO sessions",
                    "data": {"active_sessions": 0}
                }

            # Send message to all connected clients
            import asyncio
            async def send_to_all():
                for sid in active_sessions.keys():
                    await sio_server.emit('server_message', {
                        'message': message,
                        'timestamp': datetime.now().isoformat(),
                        'from': 'server'
                    }, room=sid)

            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_to_all())
            loop.close()

            return {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": f"Message sent to {len(active_sessions)} clients",
                "data": {
                    "message": message,
                    "recipients": len(active_sessions),
                    "session_ids": list(active_sessions.keys())
                }
            }

        except Exception as e:
            return {
                "status_code": status.HTTP_200_OK,
                "status": False,
                "message": f"Failed to send message: {str(e)}",
                "data": {"error": str(e)}
            }
    else:
        return {
            "status_code": status.HTTP_200_OK,
            "status": False,
            "message": "Socket.IO not available",
            "data": {}
        }

# Socket.IO Integration
if SOCKETIO_AVAILABLE:
    try:
        from app.socketio_server import initialize_socketio, get_socketio_app

        # Initialize Socket.IO server
        if initialize_socketio():
            # Get Socket.IO ASGI app with FastAPI integration
            socketio_asgi_app = get_socketio_app(app)
            if socketio_asgi_app:
                # Replace FastAPI app with integrated Socket.IO ASGI app
                app = socketio_asgi_app
                logger.info("Socket.IO server integrated successfully")
            else:
                logger.error("Failed to create Socket.IO ASGI app")
        else:
            logger.error("Failed to initialize Socket.IO server")

    except Exception as e:
        logger.error(f"Socket.IO integration failed: {e}")
        logger.info("Continuing with standard FastAPI app")
else:
    logger.info("Socket.IO not available - using standard FastAPI app")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
