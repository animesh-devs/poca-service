# POCA Service

A comprehensive backend service for doctor-patient communication with AI assistance. The service enables real-time communication between doctors and patients, provides AI-powered medical assistance, and manages patient case histories.

## 🚀 Features

- User authentication with role-based access (doctor, patient, admin, hospital)
- Hospital, doctor, and patient profile management
- Multiple relationship mappings (hospital-doctor, hospital-patient, doctor-patient, user-patient)
- Appointment scheduling and management with different types and status tracking
- Async chat between doctors and patients using API
- Realtime AI assistant for patient and medical assistance using websocket
- Case history management with document uploads
- Medical problem suggestions for doctors
- RESTful API for all functionality

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI (Python 3.9+)
- **ORM**: SQLAlchemy
- **Data Validation**: Pydantic
- **Authentication**: JWT-based
- **Real-time Communication**: WebSockets
- **Database**: SQLite (development), PostgreSQL (production)
- **AI Integration**: OpenAI GPT-4 and Google Gemini

## 📋 Requirements

- Python 3.9+
- pip (Python package manager)
- Virtual environment (recommended)

## 🔧 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/poca-service.git
   cd poca-service
   ```

2. Create and activate a virtual environment:
   ```bash
   # Create the virtual environment
   python -m venv venv  # or python3 -m venv venv

   # Activate the virtual environment
   # On macOS/Linux:
   . venv/bin/activate  # or source venv/bin/activate

   # On Windows:
   # venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file to set your configuration values.

## 🏃‍♂️ Running the Service

1. Initialize the database:
   ```bash
   # For a clean database
   python init_db.py

   # For a database with test data
   ./init_test_db.sh
   ```

2. Start the service:
   ```bash
   # Using the run.py script (recommended)
   python run.py

   # To specify a different port
   python run.py --port 9000

   # Or using uvicorn directly
   uvicorn app.main:app --reload
   ```

3. The service will be available at:
   - API: http://localhost:8000 (or the port you specified)
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

   If you used a different port (e.g., 9000), replace 8000 with your port number in the URLs above.

## 🐳 Docker Deployment

1. Make sure Docker Desktop is running:
   - On macOS: Open Docker Desktop from the Applications folder
   - On Windows: Open Docker Desktop from the Start menu
   - On Linux: Start the Docker daemon with `sudo systemctl start docker`

2. Build and run with Docker Compose:
   ```bash
   # For Docker Compose V2 (newer versions)
   docker compose up -d

   # For Docker Compose V1 (older versions)
   docker-compose up -d
   ```

3. Check if the container is running:
   ```bash
   docker ps
   ```

4. The service will be available at http://localhost:8000

5. To stop the containers:
   ```bash
   # For Docker Compose V2
   docker compose down

   # For Docker Compose V1
   docker-compose down
   ```

6. To reset the database and restart the containers:
   ```bash
   # Make the script executable
   chmod +x reset_db_docker.sh

   # Run the script
   ./reset_db_docker.sh
   ```

## 🧪 Testing

### Running Unit Tests
Run the unit tests with pytest:
```bash
pytest
```

### Creating Test Data
Create comprehensive test data for the service:
```bash
python testing-scripts/create_test_data.py
```

This script creates multiple hospitals, doctors, patients, and maps them together. See `testing.md` for details on the test data created.

### Running End-to-End Tests
Run the API flow test (without Docker):
```bash
python testing-scripts/test_api_flow.py
```

Run the Docker flow test (requires Docker and Docker Compose):
```bash
python testing-scripts/test_docker_flow.py
```

These test scripts verify all the functionality of the service by hitting actual APIs, including authentication, mapping, chat, and AI assistant flows.

For more detailed information about testing, see the `testing.md` file.

## 🤖 AI Integration

The service supports both OpenAI GPT-4 and Google Gemini models for AI assistance.

### OpenAI Integration
1. Set `AI_PROVIDER=openai` in your `.env` file
2. Provide your OpenAI API key as `OPENAI_API_KEY`
3. Optionally specify the model with `OPENAI_MODEL` (defaults to "gpt-4")

### Google Gemini Integration
1. Set `AI_PROVIDER=gemini` in your `.env` file
2. Provide your Google API key as `GOOGLE_API_KEY`
3. Optionally specify the model with `GEMINI_MODEL` (defaults to "gemini-pro")

## 📚 API Documentation

The API documentation is available at `/api/v1/docs` when the service is running. It provides detailed information about all endpoints, request/response schemas, and authentication requirements.

### API Response Format

All API responses follow a standardized format:

```json
{
  "status_code": 200,
  "status": true,
  "message": "successful",
  "data": { ... }
}
```

For more details on the API response format, see the [API Response Format](docs/api_response_format.md) documentation.

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/doctor-signup` - Doctor signup
- `POST /api/v1/auth/patient-signup` - Patient signup
- `POST /api/v1/auth/hospital-signup` - Hospital signup
- `POST /api/v1/auth/signup` - Create a new user (admin only)

#### Users
- `GET /api/v1/users` - Get all users (admin only)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile

#### Hospitals
- `POST /api/v1/hospitals` - Create hospital
- `GET /api/v1/hospitals` - Get all hospitals
- `GET /api/v1/hospitals/{hospital_id}` - Get hospital by ID
- `PUT /api/v1/hospitals/{hospital_id}` - Update hospital
- `DELETE /api/v1/hospitals/{hospital_id}` - Delete hospital
- `GET /api/v1/hospitals/{hospital_id}/doctors` - Get hospital doctors
- `GET /api/v1/hospitals/{hospital_id}/patients` - Get hospital patients

#### Patients
- `GET /api/v1/patients/{patient_id}/case-history` - Get patient case history (with option to create if not exists)
- `POST /api/v1/patients/{patient_id}/case-history` - Create patient case history
- `PUT /api/v1/patients/{patient_id}/case-history` - Update patient case history
- `GET /api/v1/patients/{patient_id}/documents` - Get patient documents

#### Reports
- `GET /api/v1/patients/{patient_id}/reports` - Get all reports for a patient
- `GET /api/v1/patients/{patient_id}/reports/{report_id}` - Get a specific report for a patient
- `POST /api/v1/patients/{patient_id}/reports` - Create a new report for a patient
- `PUT /api/v1/patients/{patient_id}/reports/{report_id}` - Update a report for a patient
- `POST /api/v1/patients/{patient_id}/reports/{report_id}/documents` - Upload a document for a patient's report

#### Mappings
- `POST /api/v1/mappings/hospital-doctor` - Map a hospital to a doctor
- `POST /api/v1/mappings/hospital-patient` - Map a hospital to a patient
- `POST /api/v1/mappings/doctor-patient` - Map a doctor to a patient
- `POST /api/v1/mappings/user-patient` - Create user-patient relation
- `PUT /api/v1/mappings/user-patient/{relation_id}` - Update user-patient relation
- `DELETE /api/v1/mappings/hospital-doctor/{mapping_id}` - Delete a hospital-doctor mapping
- `DELETE /api/v1/mappings/hospital-patient/{mapping_id}` - Delete a hospital-patient mapping
- `DELETE /api/v1/mappings/doctor-patient/{mapping_id}` - Delete a doctor-patient mapping
- `DELETE /api/v1/mappings/user-patient/{relation_id}` - Delete user-patient relation

#### Chats
- `POST /api/v1/chats` - Create a new chat
- `GET /api/v1/chats` - Get all chats for the current user
- `GET /api/v1/chats/{chat_id}` - Get a specific chat
- `PUT /api/v1/chats/{chat_id}/deactivate` - Deactivate a chat
- `DELETE /api/v1/chats/{chat_id}` - Delete a chat (admin only)
- `WebSocket /api/v1/chats/ws/{chat_id}?token={authToken}` - Real-time chat communication

#### Messages
- `POST /api/v1/messages` - Send a message
- `GET /api/v1/messages/chat/{chat_id}` - Get all messages for a chat (primary endpoint)
- `GET /api/v1/chats/{chat_id}/messages` - Get all messages for a chat (alternative endpoint, same functionality)
- `PUT /api/v1/messages/read-status` - Update read status for multiple messages
- `PUT /api/v1/messages/{message_id}/read` - Update read status for a single message

> **Note**: Both `GET /api/v1/messages/chat/{chat_id}` and `GET /api/v1/chats/{chat_id}/messages` provide the same functionality. The first is the primary endpoint, while the second is provided as an alternative for convenience.

#### Appointments
- `POST /api/v1/appointments` - Create a new appointment
- `GET /api/v1/appointments` - List all appointments (admin only)
- `GET /api/v1/appointments/{appointment_id}` - Get appointment details
- `PUT /api/v1/appointments/{appointment_id}` - Update appointment
- `DELETE /api/v1/appointments/{appointment_id}` - Cancel appointment
- `PUT /api/v1/appointments/{appointment_id}/cancel` - Cancel appointment with reason
- `PUT /api/v1/appointments/{appointment_id}/status` - Update appointment status
- `GET /api/v1/appointments/doctor/{doctor_id}` - Get all appointments for a doctor
- `GET /api/v1/appointments/patient/{patient_id}` - Get all appointments for a patient
- `GET /api/v1/appointments/hospital/{hospital_id}` - Get all appointments for a hospital

#### Suggestions
- `POST /api/v1/suggestions` - Create a new suggestion (doctor only)
- `GET /api/v1/suggestions` - List all suggestions (admin only)
- `GET /api/v1/suggestions?doctor_id={doctor_id}` - List suggestions for a specific doctor
- `GET /api/v1/suggestions/{suggestion_id}` - Get suggestion details
- `PUT /api/v1/suggestions/{suggestion_id}` - Update suggestion
- `DELETE /api/v1/suggestions/{suggestion_id}` - Delete suggestion

#### Documents
- `POST /api/v1/documents/upload` - Upload a document
- `GET /api/v1/documents/{document_id}` - Get document metadata
- `GET /api/v1/documents/{document_id}/download` - Download a document (requires authentication)
- `POST /api/v1/documents/{document_id}/download-token` - Create temporary download token for browser downloads
- `GET /api/v1/documents/download-with-token?token={temp_token}` - Download using temporary token (no auth required)
- `PUT /api/v1/documents/{document_id}/link` - Link document to an entity (case history, report, etc.)
- `GET /api/v1/documents/storage/stats` - Get storage statistics (admin only)

> **Document Download**: All document APIs include `download_link` fields. For browser downloads, use the download token endpoint to generate temporary URLs that don't require authentication headers. See [Document Download Guide](DOCUMENT_DOWNLOAD_GUIDE.md) for detailed examples.

#### AI Assistant
- `POST /api/v1/ai/sessions` - Create a new AI session
- `GET /api/v1/ai/sessions/{session_id}` - Get an AI session
- `POST /api/v1/ai/messages` - Send a message to AI
- `GET /api/v1/ai/sessions/{session_id}/messages` - Get all messages for an AI session
- `PUT /api/v1/ai/sessions/{session_id}/end` - End an AI session
- `POST /api/v1/ai/suggested-response` - Generate a suggested response for a doctor based on a patient summary
- `WebSocket /api/v1/ai-assistant/ws/{aiSessionId}?token={authToken}` - Real-time AI assistant communication

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributors

- Your Name <your.email@example.com>

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [OpenAI](https://openai.com/)
- [Google Gemini](https://ai.google.dev/)
