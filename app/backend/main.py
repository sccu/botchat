from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from .database import engine, get_db, init_db
from .models import database as models

app = FastAPI(title="BotChat - Multi-Agent Platform")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "BotChat API is running"}

# Persona API
@app.get("/personas/", response_model=None) # TODO: Add Pydantic schemas
def read_personas(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    personas = db.query(models.Persona).offset(skip).limit(limit).all()
    return personas

@app.post("/personas/", response_model=None)
def create_persona(name: str, instruction: str, engine_type: str = "gemini", db: Session = Depends(get_db)):
    db_persona = models.Persona(name=name, instruction=instruction, engine_type=engine_type)
    db.add(db_persona)
    db.commit()
    db.refresh(db_persona)
    return db_persona

# Chat API (Placeholder for Phase 2)
@app.post("/chat/send")
async def send_chat_message(session_id: str, prompt: str, persona_id: int, db: Session = Depends(get_db)):
    """
    사용자가 보낸 메시지를 처리하고 에이전트의 답변을 스트리밍합니다.
    """
    # TODO: 에이전트 선택 로직 및 LLM 스트리밍 연동
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
