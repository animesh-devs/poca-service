from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.mapping import RelationType

class HospitalDoctorMappingCreate(BaseModel):
    hospital_id: str
    doctor_id: str

class HospitalDoctorMappingResponse(HospitalDoctorMappingCreate):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class HospitalPatientMappingCreate(BaseModel):
    hospital_id: str
    patient_id: str

class HospitalPatientMappingResponse(HospitalPatientMappingCreate):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DoctorPatientMappingCreate(BaseModel):
    doctor_id: str
    patient_id: str

class DoctorPatientMappingResponse(DoctorPatientMappingCreate):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserPatientRelationCreate(BaseModel):
    user_id: str
    patient_id: str
    relation: RelationType

class UserPatientRelationUpdate(BaseModel):
    relation: RelationType

class UserPatientRelationResponse(UserPatientRelationCreate):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
