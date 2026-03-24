from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.session import Base

class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    instruction = Column(Text)
    engine_type = Column(String, default="gemini")
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    sender_type = Column(String)  # 'user' or 'agent'
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=True)
    content = Column(Text)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="messages")
    persona = relationship("Persona")
