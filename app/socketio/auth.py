import socketio
from sqlalchemy.orm import Session
import logging
from typing import Optional

from app.db.database import get_db
from app.models.user import User
from app.dependencies import get_current_user_ws

# Configure logging
logger = logging.getLogger(__name__)

async def authenticate_socketio_user(auth_data: dict, db: Session) -> Optional[User]:
    """Authenticate a Socket.IO user using JWT token"""
    try:
        # Extract token from auth data
        token = auth_data.get('token')
        if not token:
            logger.warning("Socket.IO connection attempt without token")
            return None
            
        # Use the existing WebSocket authentication function
        current_user = await get_current_user_ws(token, db)
        if not current_user:
            logger.warning("Socket.IO authentication failed")
            return None
            
        logger.info(f"Socket.IO auth successful for user {current_user.email} (ID: {current_user.id})")
        return current_user
        
    except Exception as e:
        logger.error(f"Socket.IO authentication error: {str(e)}")
        return None

def create_socketio_auth_middleware():
    """Create Socket.IO authentication middleware"""
    
    async def auth_middleware(sid, environ, auth):
        """Socket.IO authentication middleware"""
        try:
            # Get database session
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Authenticate user
                if not auth or not isinstance(auth, dict):
                    logger.warning(f"Socket.IO connection {sid} rejected: Invalid auth data")
                    return False
                    
                user = await authenticate_socketio_user(auth, db)
                if not user:
                    logger.warning(f"Socket.IO connection {sid} rejected: Authentication failed")
                    return False
                    
                # Store user info in environ for later use
                environ['socketio_user'] = user
                environ['socketio_user_entity_id'] = auth.get('user_entity_id')
                
                logger.info(f"Socket.IO connection {sid} authenticated for user {user.id}")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Socket.IO auth middleware error for {sid}: {str(e)}")
            return False
    
    return auth_middleware
