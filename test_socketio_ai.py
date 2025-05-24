import socketio
import asyncio
import json
import sys
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SocketIOAIClient:
    def __init__(self, url, token, session_id, user_entity_id=None):
        self.url = url
        self.token = token
        self.session_id = session_id
        self.user_entity_id = user_entity_id
        self.sio = socketio.AsyncClient()
        
        # Set up event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('ai_message', self.on_ai_message)
        
    async def on_connect(self):
        logger.info("Connected to Socket.IO AI Assistant")
        
    async def on_disconnect(self):
        logger.info("Disconnected from Socket.IO AI Assistant")
        
    async def on_ai_message(self, data):
        logger.info(f"Received AI message: {json.dumps(data, indent=2)}")
        
    async def connect(self):
        """Connect to the Socket.IO server"""
        try:
            # Prepare authentication data
            auth_data = {
                'token': self.token,
                'session_id': self.session_id
            }
            
            if self.user_entity_id:
                auth_data['user_entity_id'] = self.user_entity_id
                
            logger.info(f"Connecting to {self.url} with auth: {auth_data}")
            
            await self.sio.connect(self.url, auth=auth_data)
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return False
            
    async def disconnect(self):
        """Disconnect from the Socket.IO server"""
        await self.sio.disconnect()
        
    async def send_message(self, message):
        """Send a message to the AI assistant"""
        try:
            message_data = {"message": message}
            logger.info(f"Sending message: {message}")
            await self.sio.emit('ai_message', message_data)
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            
    async def interactive_chat(self):
        """Start an interactive chat session"""
        logger.info("Starting interactive chat. Type 'quit' to exit.")
        
        try:
            while True:
                message = input("\nYou: ")
                if message.lower() in ['quit', 'exit', 'q']:
                    break
                    
                if message.strip():
                    await self.send_message(message)
                    # Wait a bit for the response
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Chat interrupted by user")
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")

async def main():
    parser = argparse.ArgumentParser(description="Test Socket.IO AI Assistant")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--token", required=True, help="Authentication token")
    parser.add_argument("--session-id", required=True, help="AI Session ID")
    parser.add_argument("--user-entity-id", help="User Entity ID")
    parser.add_argument("--message", help="Single message to send (non-interactive)")
    
    args = parser.parse_args()
    
    # Create client
    client = SocketIOAIClient(
        url=args.url,
        token=args.token,
        session_id=args.session_id,
        user_entity_id=args.user_entity_id
    )
    
    # Connect
    if not await client.connect():
        logger.error("Failed to connect")
        return
        
    try:
        if args.message:
            # Send single message
            await client.send_message(args.message)
            # Wait for response
            await asyncio.sleep(3)
        else:
            # Interactive mode
            await client.interactive_chat()
            
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)
