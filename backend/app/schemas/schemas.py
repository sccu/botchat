from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PersonaBase(BaseModel):
    name: str
    instruction: str
    engine_type: str = "gemini"
    is_favorite: bool = False

class PersonaCreate(PersonaBase):
    pass

class PersonaUpdate(PersonaBase):
    name: Optional[str] = None
    instruction: Optional[str] = None

class Persona(PersonaBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    sender_type: str
    content: str
    persona_id: Optional[int] = None
    metadata_json: Optional[dict] = None

class MessageCreate(MessageBase):
    session_id: int

class Message(MessageBase):
    id: int
    session_id: int
    created_at: datetime
    persona: Optional[Persona] = None

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    title: str

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    messages: List[Message] = []

    class Config:
        from_attributes = True
