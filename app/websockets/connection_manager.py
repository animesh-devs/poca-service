from fastapi import WebSocket
from typing import Dict, List, Set, Any
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manager for WebSocket connections"""
    
    def __init__(self):
        # Active connections: {session_id: {client_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str, client_id: str) -> None:
        """Connect a client to a session"""
        await websocket.accept()
        
        # Initialize session if it doesn't exist
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        
        # Add client to session
        self.active_connections[session_id][client_id] = websocket
        logger.info(f"Client {client_id} connected to session {session_id}")
        
    def disconnect(self, session_id: str, client_id: str) -> None:
        """Disconnect a client from a session"""
        if session_id in self.active_connections and client_id in self.active_connections[session_id]:
            del self.active_connections[session_id][client_id]
            logger.info(f"Client {client_id} disconnected from session {session_id}")
            
            # Remove session if no clients are connected
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                logger.info(f"Session {session_id} removed (no clients connected)")
    
    async def send_message(self, message: Any, session_id: str, client_id: str = None) -> None:
        """Send a message to a specific client or all clients in a session"""
        if session_id not in self.active_connections:
            logger.warning(f"Attempted to send message to non-existent session {session_id}")
            return
        
        # Convert message to JSON string if it's not already a string
        if not isinstance(message, str):
            message = json.dumps(message)
        
        if client_id:
            # Send to specific client
            if client_id in self.active_connections[session_id]:
                await self.active_connections[session_id][client_id].send_text(message)
                logger.debug(f"Message sent to client {client_id} in session {session_id}")
            else:
                logger.warning(f"Attempted to send message to non-existent client {client_id} in session {session_id}")
        else:
            # Send to all clients in the session
            for client_websocket in self.active_connections[session_id].values():
                await client_websocket.send_text(message)
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

# Create a global connection manager instance
manager = ConnectionManager()
