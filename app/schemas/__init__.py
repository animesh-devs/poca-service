from app.schemas.auth import (
    Token, TokenPayload, UserCreate, UserLogin, RefreshToken
)
from app.schemas.user import (
    UserBase, UserUpdate, UserResponse, UserListResponse
)
from app.schemas.hospital import (
    HospitalBase, HospitalCreate, HospitalUpdate, HospitalResponse, HospitalListResponse
)
from app.schemas.doctor import (
    DoctorBase, DoctorCreate, DoctorUpdate, DoctorResponse, DoctorListResponse
)
from app.schemas.patient import (
    PatientBase, PatientCreate, PatientUpdate, PatientResponse, PatientListResponse
)
from app.schemas.mapping import (
    HospitalDoctorMappingCreate, HospitalDoctorMappingResponse,
    HospitalPatientMappingCreate, HospitalPatientMappingResponse,
    DoctorPatientMappingCreate, DoctorPatientMappingResponse,
    UserPatientRelationCreate, UserPatientRelationUpdate, UserPatientRelationResponse
)
from app.schemas.appointment import (
    AppointmentBase, AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentListResponse, AppointmentStatusUpdate, AppointmentCancellation
)
from app.schemas.chat import (
    ChatBase, ChatCreate, ChatResponse, ChatListResponse,
    MessageBase, MessageCreate, MessageResponse, MessageListResponse,
    ReadStatusUpdate
)
from app.schemas.case_history import (
    CaseHistoryBase, CaseHistoryCreate, CaseHistoryUpdate, CaseHistoryResponse,
    DocumentBase, DocumentCreate, DocumentResponse
)
from app.schemas.ai import (
    AISessionCreate, AISessionResponse, AIMessageCreate, AIMessageResponse,
    AIMessageListResponse
)
from app.schemas.suggestion import (
    SuggestionBase, SuggestionCreate, SuggestionUpdate, SuggestionResponse,
    SuggestionListResponse
)
from app.schemas.report import (
    ReportBase, ReportCreate, ReportUpdate, ReportResponse, ReportListResponse,
    ReportDocumentBase, ReportDocumentCreate, ReportDocumentResponse,
    PatientReportMappingCreate, PatientReportMappingResponse
)
from app.schemas.document import (
    FileDocumentBase, FileDocumentCreate, FileDocumentResponse, FileDocumentListResponse
)
