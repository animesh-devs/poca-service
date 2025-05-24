import socketio
from typing import Dict, List, Any, Optional
import logging
import json
import uuid

# Configure logging
logger = logging.getLogger(__name__)

class SocketIOConnectionManager:
    """Manager for Socket.IO connections"""
    
    def __init__(self):
        # Active connections: {session_id: {client_id: sid}}
        self.active_connections: Dict[str, Dict[str, str]] = {}
        # Reverse mapping: {sid: (session_id, client_id)}
        self.sid_mapping: Dict[str, tuple] = {}
        # Socket.IO server instance
        self.sio: Optional[socketio.AsyncServer] = None
        
    def set_socketio_server(self, sio: socketio.AsyncServer) -> None:
        """Set the Socket.IO server instance"""
        self.sio = sio
        
    async def connect(self, sid: str, session_id: str, client_id: str = None) -> str:
        """Connect a client to a session"""
        if not client_id:
            client_id = str(uuid.uuid4())
            
        # Initialize session if it doesn't exist
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        
        # Add client to session
        self.active_connections[session_id][client_id] = sid
        self.sid_mapping[sid] = (session_id, client_id)
        
        # Join the session room
        if self.sio:
            await self.sio.enter_room(sid, session_id)
            
        logger.info(f"Socket.IO client {client_id} (sid: {sid}) connected to session {session_id}")
        return client_id
        
    async def disconnect(self, sid: str) -> None:
        """Disconnect a client"""
        if sid in self.sid_mapping:
            session_id, client_id = self.sid_mapping[sid]
            
            # Remove from active connections
            if session_id in self.active_connections:
                if client_id in self.active_connections[session_id]:
                    del self.active_connections[session_id][client_id]
                    
                # Clean up empty sessions
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
            
            # Remove from sid mapping
            del self.sid_mapping[sid]
            
            # Leave the session room
            if self.sio:
                await self.sio.leave_room(sid, session_id)
                
            logger.info(f"Socket.IO client {client_id} (sid: {sid}) disconnected from session {session_id}")
    
    async def send_message(self, message: Any, session_id: str, client_id: str = None, sid: str = None) -> None:
        """Send a message to a specific client or all clients in a session"""
        if not self.sio:
            logger.error("Socket.IO server not initialized")
            return
            
        # Convert message to dict if it's not already
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                message = {"content": message}
        
        if sid:
            # Send to specific socket ID
            await self.sio.emit('ai_message', message, room=sid)
            logger.debug(f"Message sent to sid {sid}")
        elif client_id:
            # Send to specific client
            if session_id in self.active_connections and client_id in self.active_connections[session_id]:
                target_sid = self.active_connections[session_id][client_id]
                await self.sio.emit('ai_message', message, room=target_sid)
                logger.debug(f"Message sent to client {client_id} (sid: {target_sid}) in session {session_id}")
            else:
                logger.warning(f"Attempted to send message to non-existent client {client_id} in session {session_id}")
        else:
            # Send to all clients in the session (broadcast to room)
            await self.sio.emit('ai_message', message, room=session_id)
            logger.debug(f"Message broadcast to all clients in session {session_id}")
    
    def get_connected_clients(self, session_id: str) -> List[str]:
        """Get a list of client IDs connected to a session"""
        if session_id in self.active_connections:
            return list(self.active_connections[session_id].keys())
        return []
    
    def is_client_connected(self, session_id: str, client_id: str) -> bool:
        """Check if a client is connected to a session"""
        return (session_id in self.active_connections and 
                client_id in self.active_connections[session_id])
    
    def get_active_sessions(self) -> List[str]:
        """Get a list of active session IDs"""
        return list(self.active_connections.keys())
    
    def get_session_info(self, sid: str) -> Optional[tuple]:
        """Get session and client info for a socket ID"""
        return self.sid_mapping.get(sid)

# Create a global Socket.IO connection manager instance
socketio_manager = SocketIOConnectionManager()
