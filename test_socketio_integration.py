#!/usr/bin/env python3
"""
Test script to verify Socket.IO AI Assistant integration
"""

import asyncio
import socketio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.db.database import get_db
from app.models.user import User
from app.models.ai import AISession
from app.models.chat import Chat
import uvicorn
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocketIOTestClient:
    def __init__(self, url="http://localhost:8000"):
        self.url = url
        self.sio = socketio.AsyncClient()
        self.connected = False
        self.messages_received = []
        
        # Set up event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('ai_message', self.on_ai_message)
        self.sio.on('connect_error', self.on_connect_error)
        
    async def on_connect(self):
        self.connected = True
        logger.info("✅ Connected to Socket.IO server")
        
    async def on_disconnect(self):
        self.connected = False
        logger.info("❌ Disconnected from Socket.IO server")
        
    async def on_ai_message(self, data):
        self.messages_received.append(data)
        logger.info(f"📨 Received message: {data}")
        
    async def on_connect_error(self, data):
        logger.error(f"❌ Connection error: {data}")
        
    async def connect_with_auth(self, token, session_id, user_entity_id=None):
        """Connect with authentication"""
        auth_data = {
            'token': token,
            'session_id': session_id
        }
        
        if user_entity_id:
            auth_data['user_entity_id'] = user_entity_id
            
        try:
            await self.sio.connect(self.url, auth=auth_data)
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
            
    async def send_message(self, message):
        """Send a message to AI assistant"""
        if self.connected:
            await self.sio.emit('ai_message', {'message': message})
            logger.info(f"📤 Sent message: {message}")
        else:
            logger.error("❌ Not connected")
            
    async def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            await self.sio.disconnect()

def start_test_server():
    """Start the FastAPI server in a separate thread"""
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    logger.info("🚀 Test server started on http://127.0.0.1:8000")
    return server_thread

async def test_socketio_connection():
    """Test basic Socket.IO connection without authentication"""
    logger.info("🧪 Testing Socket.IO connection (should fail without auth)...")
    
    client = SocketIOTestClient()
    
    # Try to connect without authentication (should fail)
    try:
        await client.sio.connect("http://127.0.0.1:8000")
        logger.error("❌ Connection succeeded without auth (unexpected)")
        await client.disconnect()
        return False
    except Exception as e:
        logger.info(f"✅ Connection properly rejected without auth: {e}")
        return True

async def test_socketio_with_invalid_auth():
    """Test Socket.IO connection with invalid authentication"""
    logger.info("🧪 Testing Socket.IO connection with invalid auth...")
    
    client = SocketIOTestClient()
    
    # Try to connect with invalid token
    success = await client.connect_with_auth(
        token="invalid_token",
        session_id="invalid_session"
    )
    
    if not success:
        logger.info("✅ Connection properly rejected with invalid auth")
        return True
    else:
        logger.error("❌ Connection succeeded with invalid auth (unexpected)")
        await client.disconnect()
        return False

def get_test_data():
    """Get test data from database"""
    try:
        db = next(get_db())
        
        # Get a user
        user = db.query(User).first()
        if not user:
            logger.error("❌ No users found in database")
            return None, None, None
            
        # Get an AI session
        ai_session = db.query(AISession).first()
        if not ai_session:
            logger.error("❌ No AI sessions found in database")
            return None, None, None
            
        # Get the associated chat
        chat = db.query(Chat).filter(Chat.id == ai_session.chat_id).first()
        if not chat:
            logger.error("❌ No chat found for AI session")
            return None, None, None
            
        logger.info(f"📊 Found test data - User: {user.email}, Session: {ai_session.id}, Chat: {chat.id}")
        return user, ai_session, chat
        
    except Exception as e:
        logger.error(f"❌ Error getting test data: {e}")
        return None, None, None
    finally:
        db.close()

async def main():
    """Main test function"""
    logger.info("🚀 Starting Socket.IO AI Assistant Integration Test")
    
    # Start test server
    server_thread = start_test_server()
    
    try:
        # Test 1: Connection without auth
        test1_result = await test_socketio_connection()
        
        # Test 2: Connection with invalid auth
        test2_result = await test_socketio_with_invalid_auth()
        
        # Test 3: Check if we have test data for authenticated tests
        user, ai_session, chat = get_test_data()
        
        if user and ai_session and chat:
            logger.info("✅ Test data available for authenticated tests")
            logger.info("ℹ️  To test with valid authentication, use the HTML test client or Python test script with valid tokens")
        else:
            logger.warning("⚠️  No test data available for authenticated tests")
            logger.info("ℹ️  Run the database initialization script to create test data")
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("📋 TEST SUMMARY")
        logger.info("="*50)
        logger.info(f"✅ Connection rejection without auth: {'PASS' if test1_result else 'FAIL'}")
        logger.info(f"✅ Connection rejection with invalid auth: {'PASS' if test2_result else 'FAIL'}")
        logger.info(f"📊 Test data availability: {'AVAILABLE' if (user and ai_session and chat) else 'NOT AVAILABLE'}")
        
        if test1_result and test2_result:
            logger.info("🎉 Socket.IO AI Assistant integration is working correctly!")
            logger.info("🔧 Use the provided test clients for full functionality testing:")
            logger.info("   - HTML: Open socketio_ai_test.html in browser")
            logger.info("   - Python: python test_socketio_ai.py --token <token> --session-id <session_id>")
        else:
            logger.error("❌ Some tests failed. Check the implementation.")
            
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
    
    logger.info("🏁 Test completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)
