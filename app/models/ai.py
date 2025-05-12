from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.database import Base

class AISession(Base):
    __tablename__ = "ai_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    chat_id = Column(String, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    start_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    end_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    chat = relationship("Chat", back_populates="ai_sessions")
    messages = relationship("AIMessage", back_populates="session", cascade="all, delete-orphan")

class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("ai_sessions.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    is_summary = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("AISession", back_populates="messages")
