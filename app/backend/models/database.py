from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Persona(Base):
    """
    에이전트의 페르소나 정보를 저장합니다.
    """
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    instruction = Column(Text, nullable=False)  # System Prompt
    engine_type = Column(String(50), default="gemini") # gemini, claude, etc.
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="persona")

class Message(Base):
    """
    대화 이력을 저장합니다.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    sender_type = Column(String(50))  # moderator, agent, system
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True) # engine_type, response_time, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    persona = relationship("Persona", back_populates="messages")
