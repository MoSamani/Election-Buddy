from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=schemas.FeedbackRead, status_code=status.HTTP_201_CREATED)
def create_feedback(payload: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    query = db.get(models.Query, payload.query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    feedback = models.Feedback(
        query_id=payload.query_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/", response_model=List[schemas.FeedbackRead])
def list_feedback(limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(models.Feedback)
        .order_by(models.Feedback.created_at.desc())
        .limit(limit)
        .all()
    )
