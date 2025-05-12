from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from app.db.database import Base

class MessageType(str, enum.Enum):
    TEXT = "text"
    AUDIO = "audio"
    FILE = "file"

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    doctor_id = Column(String, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    doctor = relationship("Doctor", back_populates="chats")
    patient = relationship("Patient", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    ai_sessions = relationship("AISession", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    chat_id = Column(String, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String, nullable=False)  # User ID of the sender
    receiver_id = Column(String, nullable=False)  # User ID of the receiver
    message = Column(String, nullable=False)
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.TEXT)
    file_details = Column(JSON, nullable=True)  # JSON object with file details
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
