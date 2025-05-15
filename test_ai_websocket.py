import websocket
import json
import time
import sys
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def on_message(ws, message):
    logger.info(f"Received: {message}")

def on_error(ws, error):
    logger.error(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    logger.info(f"Connection closed: {close_status_code} - {close_msg}")

def on_open(ws):
    logger.info("Connection established")

    # Send a test message
    message = {
        "message": "Hello, this is a test message"
    }

    logger.info(f"Sending: {json.dumps(message)}")
    ws.send(json.dumps(message))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test AI WebSocket connection")
    parser.add_argument("--protocol", choices=["ws", "wss"], default="ws", help="WebSocket protocol (ws or wss)")
    parser.add_argument("--host", default="localhost:8000", help="Host and port (e.g., localhost:8000)")
    parser.add_argument("--session-id", required=True, help="AI Session ID")
    parser.add_argument("--token", required=True, help="Authentication token")
    parser.add_argument("--entity-id", help="User entity ID (optional)")

    args = parser.parse_args()

    # Construct the WebSocket URL
    url = f"{args.protocol}://{args.host}/api/v1/ai-assistant/ws/{args.session_id}?token={args.token}"
    if args.entity_id:
        url += f"&user_entity_id={args.entity_id}"

    logger.info(f"Connecting to: {url}")

    # Create headers if entity ID is provided
    headers = {}
    if args.entity_id:
        headers["user-entity-id"] = args.entity_id
        logger.info(f"Using user-entity-id: {args.entity_id}")

    # Enable trace for debugging
    websocket.enableTrace(True)

    # Create a WebSocket connection
    ws = websocket.WebSocketApp(
        url,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    # Start the WebSocket connection
    ws.run_forever()
