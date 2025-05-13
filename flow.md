# POCA Service Flow Documentation

This document outlines the complete flow for the POCA (Patient-Doctor Chat Assistant) service, including all API endpoints that need to be called sequentially to achieve the desired functionality.

## Complete User Flow

### 1. Registration and Setup Flow

1. **Register/Sign Up Hospital**
   - Endpoint: `POST /api/v1/auth/hospital-signup`
   - Payload: Hospital details (name, address, email, password, etc.)
   - Response: Authentication token for the hospital user

2. **Register Admin User**
   - Endpoint: `POST /api/v1/auth/signup`
   - Payload: Admin user details (name, email, password, role="admin")
   - Response: Authentication token for the admin user
   - Note: This requires an existing admin user to create another admin

3. **Register Doctor User**
   - Endpoint: `POST /api/v1/auth/doctor-signup`
   - Payload: Doctor details (name, email, password, designation, experience, etc.)
   - Response: Authentication token for the doctor user

4. **Admin Maps Doctor to Hospital**
   - Endpoint: `POST /api/v1/mappings/hospital-doctor`
   - Payload: Hospital ID and Doctor ID
   - Response: Mapping details with mapping ID

5. **Register Patient User**
   - Endpoint: `POST /api/v1/auth/patient-signup`
   - Payload: Patient details (name, email, password, dob, gender, etc.)
   - Response: Authentication token for the patient user

6. **Add Patients to User (User-Patient Mapping)**
   - Endpoint: `POST /api/v1/mappings/user-patient`
   - Payload: User ID, Patient ID, and relation (self, spouse, child, etc.)
   - Response: Mapping details with mapping ID

7. **Admin Maps Patient to Hospital**
   - Endpoint: `POST /api/v1/mappings/hospital-patient`
   - Payload: Hospital ID and Patient ID
   - Response: Mapping details with mapping ID

8. **Admin Maps Patient with Doctor**
   - Endpoint: `POST /api/v1/mappings/doctor-patient`
   - Payload: Doctor ID and Patient ID
   - Response: Mapping details with mapping ID

9. **Admin Creates Case History for Patient**
   - Endpoint: `POST /api/v1/patients/{patient_id}/case-history`
   - Payload: Patient ID, summary, and optional documents
   - Response: Case history details with case history ID

10. **Admin Updates Documents for Case History**
    - Endpoint: `PUT /api/v1/patients/{patient_id}/case-history`
    - Payload: Case history ID and updated documents
    - Response: Updated case history details

### 2. Patient-AI Interaction Flow

11. **Patient User Login**
    - Endpoint: `POST /api/v1/auth/login`
    - Payload: Email and password
    - Response: Authentication token for the patient user

12. **Patient Selects Patient Profile**
    - Endpoint: `GET /api/v1/mappings/user/{user_id}/patients`
    - Response: List of patients associated with the user
    - Note: User selects one of the patients from the list

13. **Patient Connects to AI Assistant via WebSocket**
    - WebSocket Endpoint: `WebSocket /api/v1/ai-assistant/ws/{session_id}`
    - Note: Before connecting to WebSocket, create an AI session

14. **Create AI Session**
    - Endpoint: `POST /api/v1/ai-assistant/sessions`
    - Payload: Chat ID
    - Response: AI session details with session ID

15. **AI Assistant Asks Questions and Gathers Information**
    - WebSocket Communication: Patient sends messages and receives responses
    - Alternative REST API:
      - Send Message: `POST /api/v1/ai-assistant/sessions/{session_id}/messages`
      - Payload: Session ID and message content
      - Response: Message details with AI response

16. **AI Assistant Generates Summary**
    - After gathering sufficient information, the AI generates a summary
    - This happens automatically after a predefined number of questions or when triggered by a command

17. **Patient Reviews and Finalizes Summary**
    - Endpoint: `PUT /api/v1/ai-assistant/sessions/{session_id}/summary`
    - Payload: Session ID and edited summary
    - Response: Updated session details with finalized summary

18. **End AI Session**
    - Endpoint: `PUT /api/v1/ai/sessions/{session_id}/end`
    - Payload: Session ID
    - Response: Updated session details with end timestamp

19. **Send Summary to Doctor**
    - Endpoint: `POST /api/v1/messages`
    - Payload: Chat ID, sender ID (patient), receiver ID (doctor), message (summary)
    - Response: Message details with message ID

### 3. Doctor Interaction Flow

20. **Doctor User Login**
    - Endpoint: `POST /api/v1/auth/login`
    - Payload: Email and password
    - Response: Authentication token for the doctor user

21. **Doctor Views Unread Chats**
    - Endpoint: `GET /api/v1/chats?is_read=false`
    - Response: List of unread chat sessions

22. **Doctor Views Chat with Summary**
    - Endpoint: `GET /api/v1/chats/{chat_id}/messages`
    - Response: List of messages in the chat, including the summary

23. **AI Generates Suggested Response for Doctor**
    - Endpoint: `POST /api/v1/ai/sessions`
    - Payload: Chat ID
    - Response: AI session details with session ID
    - Then: `POST /api/v1/ai/messages`
    - Payload: Session ID and summary as message
    - Response: AI-generated suggested response

24. **Doctor Edits and Sends Response to Patient**
    - Endpoint: `POST /api/v1/messages`
    - Payload: Chat ID, sender ID (doctor), receiver ID (patient), message (edited response)
    - Response: Message details with message ID

### 4. Additional Features

25. **View Case History**
    - Endpoint: `GET /api/v1/patients/{patient_id}/case-history`
    - Response: Case history details with documents

26. **Create Case History (if not exists)**
    - Endpoint: `GET /api/v1/patients/{patient_id}/case-history?create_if_not_exists=true`
    - Response: Case history details (newly created if it didn't exist)

27. **Upload Documents in Chat**
    - Endpoint: `POST /api/v1/messages`
    - Payload: Chat ID, sender ID, receiver ID, message, message_type="file", file_details
    - Response: Message details with message ID

28. **Get Patient Reports**
    - Endpoint: `GET /api/v1/patients/{patient_id}/reports`
    - Response: List of reports for the patient

29. **Get Specific Report**
    - Endpoint: `GET /api/v1/patients/{patient_id}/reports/{report_id}`
    - Response: Report details with documents

30. **Create Patient Report**
    - Endpoint: `POST /api/v1/patients/{patient_id}/reports`
    - Payload: Title, description, report_type
    - Response: Report details with report ID

31. **Update Patient Report**
    - Endpoint: `PUT /api/v1/patients/{patient_id}/reports/{report_id}`
    - Payload: Updated title, description, report_type
    - Response: Updated report details

32. **Upload Report Document**
    - Endpoint: `POST /api/v1/patients/{patient_id}/reports/{report_id}/documents`
    - Payload: File (multipart/form-data) and optional remark
    - Response: Document details with document ID

33. **Get Suggested Problems/Messages**
    - Endpoint: `GET /api/v1/suggestions`
    - Response: List of suggested problems/messages

34. **View Booked Appointments**
    - For Doctor: `GET /api/v1/appointments/doctor/{doctor_id}`
    - For Patient: `GET /api/v1/appointments/patient/{patient_id}`
    - Response: List of appointments

35. **Book Appointment**
    - Endpoint: `POST /api/v1/appointments`
    - Payload: Doctor ID, patient ID, time slot, hospital ID, type
    - Response: Appointment details with appointment ID

36. **Update Appointment**
    - Endpoint: `PUT /api/v1/appointments/{appointment_id}`
    - Payload: Updated appointment details
    - Response: Updated appointment details

37. **View Previous Messages**
    - Endpoint: `GET /api/v1/chats/{chat_id}/messages`
    - Response: List of messages in the chat

## API Sequence Diagrams

### Registration and Setup Flow
```
Hospital User -> POST /api/v1/auth/hospital-signup
Admin User -> POST /api/v1/auth/signup
Doctor User -> POST /api/v1/auth/doctor-signup
Admin User -> POST /api/v1/mappings/hospital-doctor
Patient User -> POST /api/v1/auth/patient-signup
Admin User -> POST /api/v1/mappings/user-patient
Admin User -> POST /api/v1/mappings/hospital-patient
Admin User -> POST /api/v1/mappings/doctor-patient
Admin User -> POST /api/v1/patients/{patient_id}/case-history
Admin User -> PUT /api/v1/patients/{patient_id}/case-history
Admin User -> POST /api/v1/patients/{patient_id}/reports
Admin User -> POST /api/v1/patients/{patient_id}/reports/{report_id}/documents
```

### Patient-AI Interaction Flow
```
Patient User -> POST /api/v1/auth/login
Patient User -> GET /api/v1/mappings/user/{user_id}/patients
Patient User -> GET /api/v1/patients/{patient_id}/case-history?create_if_not_exists=true
Patient User -> GET /api/v1/patients/{patient_id}/reports
Patient User -> POST /api/v1/ai-assistant/sessions
Patient User -> WebSocket /api/v1/ai-assistant/ws/{session_id}
  or
Patient User -> POST /api/v1/ai-assistant/sessions/{session_id}/messages (multiple times)
Patient User -> PUT /api/v1/ai-assistant/sessions/{session_id}/summary
Patient User -> PUT /api/v1/ai/sessions/{session_id}/end
Patient User -> POST /api/v1/messages (to send summary to doctor)
```

### Doctor Interaction Flow
```
Doctor User -> POST /api/v1/auth/login
Doctor User -> GET /api/v1/chats?is_read=false
Doctor User -> GET /api/v1/chats/{chat_id}/messages
Doctor User -> GET /api/v1/patients/{patient_id}/case-history
Doctor User -> GET /api/v1/patients/{patient_id}/reports
Doctor User -> GET /api/v1/patients/{patient_id}/reports/{report_id}
Doctor User -> POST /api/v1/patients/{patient_id}/reports (create new report if needed)
Doctor User -> POST /api/v1/patients/{patient_id}/reports/{report_id}/documents (upload report documents)
Doctor User -> POST /api/v1/ai/sessions
Doctor User -> POST /api/v1/ai/messages
Doctor User -> POST /api/v1/messages (to send response to patient)
```

## Implementation Status

The implementation now includes all the necessary components to support the expected flow:

1. **WebSocket Implementation**: WebSocket endpoints have been implemented for real-time AI chat, allowing patients to interact with the AI assistant in real-time.

2. **Summary Handling**: The AI service now generates a summary after 5 questions, and there's an endpoint for patients to edit the summary before sending it to the doctor.

3. **AI System Prompt**: The AI service has been updated to include a system prompt for patient interviews with the 5-question format and summarization capability.

4. **Suggested Response for Doctors**: The implementation now includes functionality for generating suggested responses for doctors based on the patient summary.

5. **Message Read Status**: The implementation for tracking message read status is in place.

6. **File Upload in Messages**: The implementation for handling file uploads in messages is in place.

7. **Case History Management**: The implementation now includes endpoints for creating, retrieving, and updating case histories for patients, with support for creating a case history if it doesn't exist.

8. **Report Management**: The implementation now includes endpoints for creating, retrieving, and updating reports for patients, as well as uploading documents to reports.

9. **Document Management**: The implementation now includes support for adding remarks to documents and associating documents with case histories and reports.

10. **JSON Response Format**: The AI responses are now formatted as JSON objects with the following structure:
   ```json
   {
       "message": "The AI response text",
       "isSummary": true/false
   }
   ```
   This allows the frontend to easily distinguish between regular responses and summaries.

## Testing the Implementation

To test the complete flow, follow these steps:

1. **Start the Server**:
   ```bash
   cd poca-service
   python3 run.py
   ```

   Note: The server runs on port 8000 by default. If port 8000 is already in use, you can specify a different port:
   ```bash
   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

2. **Update the Database Schema**:
   ```bash
   python3 update_db_schema.py
   ```

3. **Initialize the Database**:
   If the database already exists and you want to start fresh:
   ```bash
   rm -f app.db && python3 simple_init_db.py
   ```
   Otherwise:
   ```bash
   python3 simple_init_db.py
   ```

4. **Authentication Requirements**:
   All API endpoints require authentication except for the login endpoints. The test scripts use the following credentials:
   - Email: admin@example.com
   - Password: password123

   The authentication token must be included in the Authorization header for all API requests:
   ```
   Authorization: Bearer YOUR_ACCESS_TOKEN
   ```

   For WebSocket connections, the token is included as a query parameter:
   ```
   ws://localhost:8000/api/v1/ai-assistant/ws/{session_id}?token=YOUR_ACCESS_TOKEN
   ```

5. **Create Test Data**:
   ```bash
   python3 testing-scripts/create_test_data.py
   ```
   This creates comprehensive test data including hospitals, doctors, patients, and mappings.

6. **Test API Flow (Non-Docker)**:
   ```bash
   python3 testing-scripts/test_api_flow.py
   ```
   This tests all flows by hitting actual APIs in non-docker environment.

7. **Test Docker Flow**:
   ```bash
   python3 testing-scripts/test_docker_flow.py
   ```
   This tests all flows by hitting actual APIs in docker environment.

## Additional Enhancements

While the current implementation supports the expected flow, there are some additional enhancements that could be made:

1. **Improved Error Handling**: Add more robust error handling for edge cases.

2. **Performance Optimization**: Optimize the AI service for better performance with large conversations.

3. **Security Enhancements**: Add additional security measures for the WebSocket connections.

4. **Monitoring and Logging**: Enhance monitoring and logging for better debugging and analytics.

5. **User Experience Improvements**: Add features like typing indicators, read receipts, and message delivery status.
