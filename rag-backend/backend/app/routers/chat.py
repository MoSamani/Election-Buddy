from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..deps import get_db
from .. import models, schemas

router = APIRouter(prefix="/chat_sessions", tags=["chat"])


@router.get("/", response_model=list[schemas.ChatSessionListItem])
def list_sessions(db: Session = Depends(get_db)):
    return (
        db.query(models.ChatSession)
        .order_by(models.ChatSession.updated_at.desc())
        .all()
    )


@router.get("/{session_id}", response_model=schemas.ChatSessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="ChatSession not found")
    return session
