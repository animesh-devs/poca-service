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
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
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
   python init_db.py
   ```

2. Start the service:
   ```bash
   uvicorn app.main:app --reload
   ```

3. The service will be available at:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

## 🐳 Docker Deployment

1. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. The service will be available at http://localhost:8000

## 🧪 Testing

Run the tests with pytest:
```bash
pytest
```

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

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/doctor/signup` - Doctor signup
- `POST /api/v1/auth/patient/signup` - Patient signup
- `POST /api/v1/auth/hospital/signup` - Hospital signup

#### Users
- `GET /api/v1/users` - Get all users (admin only)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user

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

#### AI Assistant
- `POST /api/v1/ai/chat` - Chat with AI
- `POST /api/v1/ai/summarize` - Summarize text with AI
- `POST /api/v1/ai/analyze` - Analyze medical text with AI

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
