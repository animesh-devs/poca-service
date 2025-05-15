# POCA Service Postman Collection

This repository contains a Postman collection for testing the POCA (Patient-Doctor Chat Assistant) service API.

## Contents

- `poca-service-postman-collection.json`: Postman collection with all API endpoints
- `poca-service-postman-environment.json`: Postman environment with variables
- `poca-service-postman-readme.md`: This README file

## Setup Instructions

### 1. Import the Collection and Environment

1. Open Postman
2. Click on "Import" in the top left corner
3. Select the `poca-service-postman-collection.json` and `poca-service-postman-environment.json` files
4. Both the collection and environment should now be imported

### 2. Select the Environment

1. In the top right corner of Postman, select the "POCA Service Environment" from the dropdown
2. This will enable the environment variables used in the collection

### 3. Configure the Base URL

1. Click on the "Environment quick look" button (eye icon) in the top right corner
2. Update the `baseUrl` variable if your API is running on a different URL than `http://localhost:8000`
3. Click "Save" to apply the changes

## Using the Collection

### Authentication

1. Start by running the "Login" request in the Authentication folder
   - This will automatically set the `authToken` variable for subsequent requests
   - Default credentials: `admin@example.com` / `admin123`

2. All other requests in the collection are pre-configured to use the `authToken` variable for authentication

### Testing Flow

Follow this sequence to test the complete flow:

1. **Registration and Setup**
   - Register a hospital using "Hospital Signup"
   - Register a doctor using "Doctor Signup"
   - Register a patient using "Patient Signup"
   - Map the hospital to the doctor using "Map Hospital to Doctor"
   - Map the hospital to the patient using "Map Hospital to Patient"
   - Map the doctor to the patient using "Map Doctor to Patient"

2. **Chat Setup**
   - Create a chat between the doctor and patient using "Create Chat"
   - The response will include a `chat_id` which will be used for AI sessions

3. **AI Assistant Interaction**
   - Create an AI session using "Create AI Session"
   - Send messages to the AI using "Send Message to AI"
   - Get AI session messages using "Get AI Session Messages"
   - Update the AI summary using "Update AI Summary"
   - End the AI session using "End AI Session"

4. **Doctor-Patient Communication**
   - Send messages between doctor and patient using "Send Message"
   - Get chat messages using "Get Chat Messages"
   - Update read status using "Update Read Status"

### WebSocket Testing

The POCA service provides two WebSocket endpoints for real-time communication. For WebSocket testing, use the separate "POCA Service WebSocket APIs" collection.

#### AI Assistant WebSocket

For testing the AI Assistant WebSocket endpoint:

1. Create an AI session using the "Create AI Session" request
2. Copy the `aiSessionId` from the response
3. In Postman, open the "POCA Service WebSocket APIs" collection
4. Select the "AI Assistant WebSocket" request
5. The WebSocket URL should be: `wss://localhost:8000/api/v1/ai-assistant/ws/{aiSessionId}?token={authToken}`
   - The `aiSessionId` and `authToken` variables will be automatically filled from your environment
6. Connect to the WebSocket
7. Send messages in JSON format:
   ```json
   {
     "message": "Hello, I'm not feeling well today."
   }
   ```
8. The AI will process your message and stream responses back in real-time

#### Chat WebSocket

For testing the Chat WebSocket endpoint (for doctor-patient communication):

1. Create a chat using the "Create Chat" request or use an existing chat
2. Copy the `chatId` from the response
3. In Postman, open the "POCA Service WebSocket APIs" collection
4. Select the "Chat WebSocket" request
5. The WebSocket URL should be: `wss://localhost:8000/api/v1/chats/ws/{chatId}?token={authToken}`
   - The `chatId` and `authToken` variables will be automatically filled from your environment
6. Connect to the WebSocket
7. Send messages in JSON format:
   ```json
   {
     "content": "Hello, this is a real-time message",
     "message_type": "text"
   }
   ```
8. All participants in the same chat room will receive the messages

> **Note**: WebSocket connections require the WSS protocol (secure WebSockets). The environment is configured with a `wssBaseUrl` variable that includes this protocol.

## Environment Variables

The collection uses the following environment variables:

- `baseUrl`: Base URL of the API (e.g., `http://localhost:8000`)
- `authToken`: Authentication token (set automatically after login)
- `refreshToken`: Refresh token (set automatically after login)
- `userId`: ID of the current user (set automatically after login)
- `userRole`: Role of the current user (set automatically after login)
- `hospitalId`: ID of a hospital (set manually or from responses)
- `doctorId`: ID of a doctor (set manually or from responses)
- `patientId`: ID of a patient (set manually or from responses)
- `chatId`: ID of a chat session (set manually or from responses)
- `messageId`: ID of a message (set manually or from responses)
- `aiSessionId`: ID of an AI session (set manually or from responses)

## API Categories

The collection is organized into the following categories:

1. **Health Checks**
   - Root, Health Check

2. **Authentication**
   - Login, Refresh Token, Doctor Signup, Patient Signup, Hospital Signup

3. **Users**
   - Get All Users, Get User by ID, Update User

4. **Hospitals**
   - Get All Hospitals, Get Hospital by ID, Create Hospital, Update Hospital

5. **Doctors**
   - Get All Doctors, Get Doctor by ID, Update Doctor

6. **Patients**
   - Get All Patients, Get Patient by ID, Update Patient

7. **Mappings**
   - Map Hospital to Doctor, Map Hospital to Patient, Map Doctor to Patient

8. **Chats**
   - Get All Chats, Get Chat by ID, Create Chat, Get Chat Messages
   - WebSocket Connection for real-time chat between users

9. **Messages**
   - Send Message, Update Read Status

10. **AI Assistant**
    - Create AI Session, Send Message to AI, Get AI Session Messages, End AI Session, Update AI Summary
    - WebSocket Connection for real-time AI chat
