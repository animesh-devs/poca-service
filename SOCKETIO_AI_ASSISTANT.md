# Socket.IO AI Assistant Documentation

This document describes the Socket.IO implementation for the AI Assistant feature, which provides the same functionality as the WebSocket implementation but using Socket.IO for real-time communication.

## Overview

The Socket.IO AI Assistant provides real-time communication between patients and an AI assistant for medical interviews. It implements the same business logic as the WebSocket version but uses Socket.IO for better browser compatibility and additional features like automatic reconnection.

## Architecture

### Components

1. **Socket.IO Server** (`app/socketio/server.py`)
   - Main Socket.IO server configuration
   - ASGI app integration with FastAPI

2. **Connection Manager** (`app/socketio/connection_manager.py`)
   - Manages Socket.IO connections and sessions
   - Handles message routing and broadcasting

3. **AI Assistant Handlers** (`app/socketio/ai_assistant.py`)
   - Event handlers for AI assistant functionality
   - Authentication and authorization logic
   - AI service integration

4. **Authentication** (`app/socketio/auth.py`)
   - JWT token validation for Socket.IO connections
   - User authentication middleware

## Connection Flow

### 1. Client Connection

Clients connect to the Socket.IO endpoint with authentication data:

```javascript
const socket = io('http://localhost:8000', {
    auth: {
        token: 'your_jwt_token',
        session_id: 'ai_session_id',
        user_entity_id: 'optional_entity_id'
    }
});
```

### 2. Authentication

The server validates the JWT token and checks user permissions:
- Validates JWT token format and expiration
- Checks user role and entity permissions
- Verifies access to the specified AI session

### 3. Session Management

Once authenticated, the client is added to the session:
- Generates unique client ID
- Joins session room for message broadcasting
- Stores session information for message routing

## Events

### Client to Server Events

#### `ai_message`
Send a message to the AI assistant.

**Payload:**
```json
{
    "message": "I'm not feeling well today"
}
```

### Server to Client Events

#### `ai_message`
Receive messages from the server (system messages, AI responses, status updates).

**System Message:**
```json
{
    "type": "system",
    "content": "Connected to AI Assistant. You can start chatting now."
}
```

**Status Message:**
```json
{
    "type": "status",
    "content": "Processing your message..."
}
```

**AI Response:**
```json
{
    "type": "ai_response",
    "message_id": 123,
    "content": {
        "message": "I understand you're not feeling well. Can you describe your symptoms?",
        "isSummary": false
    },
    "question_count": 1
}
```

**Error Message:**
```json
{
    "type": "error",
    "content": "An error occurred while processing your message."
}
```

## Authentication

### JWT Token Requirements

The Socket.IO connection requires a valid JWT token with the following claims:
- `sub`: User ID
- `type`: Must be "access"
- `exp`: Token expiration timestamp

### User Entity ID

The `user_entity_id` parameter specifies which entity the user is operating as:
- **Doctor**: Must match the doctor ID in the chat
- **Patient**: Must match a patient ID the user has access to
- **Admin**: Can access any session
- **Hospital**: Must match the hospital ID

If not provided, the system will automatically determine the entity ID based on user role and relationships.

## Access Control

### Role-Based Permissions

1. **Admin Users**
   - Can access any AI session
   - No entity ID restrictions

2. **Doctor Users**
   - Can only access sessions where they are the assigned doctor
   - Entity ID must match the chat's doctor_id

3. **Patient Users**
   - Can access sessions for patients they have relationships with
   - Entity ID must match a patient they're related to via UserPatientRelation

4. **Hospital Users**
   - Access based on hospital relationships
   - Entity ID must match their hospital profile

## Error Handling

### Connection Errors

- **Authentication Failed**: Invalid or expired JWT token
- **Session Not Found**: AI session doesn't exist
- **Access Denied**: User doesn't have permission to access the session
- **Missing Parameters**: Required authentication data not provided

### Runtime Errors

- **Database Errors**: Handled gracefully with error messages to client
- **AI Service Errors**: Fallback error responses sent to client
- **Network Errors**: Socket.IO handles reconnection automatically

## Testing

### HTML Test Client

Use `socketio_ai_test.html` for browser-based testing:

1. Open the HTML file in a browser
2. Enter server URL, session ID, and JWT token
3. Optionally provide user entity ID
4. Click "Connect" to establish connection
5. Send messages and receive AI responses

### Python Test Client

Use `test_socketio_ai.py` for programmatic testing:

```bash
python test_socketio_ai.py --token YOUR_JWT_TOKEN --session-id SESSION_ID --message "Hello AI"
```

### Interactive Mode

```bash
python test_socketio_ai.py --token YOUR_JWT_TOKEN --session-id SESSION_ID
```

## Configuration

### CORS Settings

The Socket.IO server is configured with permissive CORS settings for development:

```python
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # Configure for production
    logger=True,
    engineio_logger=True
)
```

For production, configure specific allowed origins.

### Integration with FastAPI

The Socket.IO app is mounted on the FastAPI application:

```python
app.mount("/socket.io", socketio_app)
```

## Comparison with WebSocket Implementation

| Feature | WebSocket | Socket.IO |
|---------|-----------|-----------|
| Protocol | Native WebSocket | Socket.IO (WebSocket + fallbacks) |
| Browser Support | Modern browsers | All browsers (with fallbacks) |
| Reconnection | Manual | Automatic |
| Message Format | JSON strings | Native objects |
| Namespaces | No | Yes |
| Rooms | Manual | Built-in |
| Authentication | Query parameters | Auth object |

## Business Logic Compatibility

The Socket.IO implementation maintains 100% compatibility with the WebSocket version:

- Same authentication and authorization logic
- Identical AI service integration
- Same database operations (AISession, AIMessage)
- Same message formats and response structure
- Same access control and permission checks
- Same error handling and logging

## Dependencies

The Socket.IO implementation requires:

```
python-socketio>=5.8.0
```

This is automatically included in `requirements.txt`.

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if server is running
   - Verify Socket.IO endpoint is mounted correctly

2. **Authentication Failed**
   - Verify JWT token is valid and not expired
   - Check token format and required claims

3. **Access Denied**
   - Verify user has permission to access the AI session
   - Check user entity ID matches expected values

4. **No Response from AI**
   - Check AI service configuration
   - Verify OpenAI API key is set correctly
   - Check database connectivity

### Debugging

Enable Socket.IO logging for detailed debugging:

```python
sio = socketio.AsyncServer(
    logger=True,
    engineio_logger=True
)
```

Check application logs for authentication and permission errors.
