from app.models.user import User, UserRole
from app.models.hospital import Hospital
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.mapping import (
    HospitalDoctorMapping,
    HospitalPatientMapping,
    DoctorPatientMapping,
    UserPatientRelation
)
from app.models.appointment import Appointment, AppointmentType, AppointmentStatus
from app.models.chat import Chat, Message, MessageType
from app.models.case_history import CaseHistory, Document, UploadedBy as CaseHistoryUploadedBy
from app.models.ai import AISession, AIMessage
from app.models.suggestion import Suggestion
from app.models.report import Report, PatientReportMapping, ReportDocument, ReportType
from app.models.document import FileDocument, DocumentType, UploadedBy
