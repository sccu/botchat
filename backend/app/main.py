from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio
from .db.session import engine, Base, get_db, SessionLocal
from .models import models
from .schemas import schemas
from .core.llm import llm_connector

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Local LLM Multi-Agent Chat App API")

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    if db.query(models.Persona).count() == 0:
        personas = [
            models.Persona(name="Gemini (Standard)", instruction="You are a helpful assistant powered by Google Gemini.", engine_type="gemini"),
            models.Persona(name="Logic Pro", instruction="You are a logic expert. Always provide structured, logical reasoning for your answers.", engine_type="gemini"),
            models.Persona(name="Creative Writer", instruction="You are a creative writer. Use rich language and storytelling techniques in your responses.", engine_type="gemini")
        ]
        db.add_all(personas)
        db.commit()
    
    db.close()

@app.on_event("shutdown")
async def shutdown_event():
    await llm_connector.cleanup()

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Persona CRUD
@app.post("/api/personas", response_model=schemas.Persona)
def create_persona(persona: schemas.PersonaCreate, db: Session = Depends(get_db)):
    db_persona = models.Persona(**persona.dict())
    db.add(db_persona)
    db.commit()
    db.refresh(db_persona)
    return db_persona

@app.get("/api/personas", response_model=List[schemas.Persona])
def read_personas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Persona).offset(skip).limit(limit).all()

@app.get("/api/personas/{persona_id}", response_model=schemas.Persona)
def read_persona(persona_id: int, db: Session = Depends(get_db)):
    db_persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if db_persona is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    return db_persona

@app.put("/api/personas/{persona_id}", response_model=schemas.Persona)
def update_persona(persona_id: int, persona: schemas.PersonaUpdate, db: Session = Depends(get_db)):
    db_persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if db_persona is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    for key, value in persona.dict(exclude_unset=True).items():
        setattr(db_persona, key, value)
    db.commit()
    db.refresh(db_persona)
    return db_persona

@app.delete("/api/personas/{persona_id}")
def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    db_persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if db_persona is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    db.delete(db_persona)
    db.commit()
    return {"message": "Persona deleted"}

# Session CRUD
@app.post("/api/sessions", response_model=schemas.Session)
def create_session(session: schemas.SessionCreate, db: Session = Depends(get_db)):
    db_session = models.Session(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/api/sessions", response_model=List[schemas.Session])
def read_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Session).order_by(models.Session.created_at.desc()).offset(skip).limit(limit).all()

@app.get("/api/sessions/{session_id}", response_model=schemas.Session)
def read_session(session_id: int, db: Session = Depends(get_db)):
    db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

# WebSocket for Chat
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            session_id = payload.get("session_id")
            persona_id = payload.get("persona_id")
            content = payload.get("content")
            
            if not session_id or not persona_id:
                continue
            
            # Pull context (last 10 messages)
            context_msgs = db.query(models.Message).filter(
                models.Message.session_id == session_id
            ).order_by(models.Message.created_at.desc()).limit(10).all()
            
            # Context formatting (oldest first)
            context = []
            for m in reversed(context_msgs):
                context.append({
                    "sender_type": m.sender_type,
                    "content": m.content,
                    "persona_name": m.persona.name if m.persona else "Agent"
                })

            # Save user message if content provided
            if content:
                user_msg = models.Message(
                    session_id=session_id,
                    sender_type="user",
                    content=content
                )
                db.add(user_msg)
                db.commit()

            # Get Persona
            persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
            system_prompt = persona.instruction if persona else None

            # Stream from LLM
            full_response = ""
            async for chunk in llm_connector.send_message(
                persona_id=persona_id, 
                prompt=content, 
                context=context, 
                system_prompt=system_prompt
            ):
                full_response += chunk
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk,
                    "persona_name": persona.name if persona else "Agent"
                })
            
            # Save Agent message
            agent_msg = models.Message(
                session_id=session_id,
                sender_type="agent",
                persona_id=persona_id,
                content=full_response
            )
            db.add(agent_msg)
            db.commit()
            
            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        db.close()
