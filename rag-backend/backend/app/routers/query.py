
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=schemas.QueryRead, status_code=status.HTTP_201_CREATED)
def create_query(payload: schemas.QueryCreate, db: Session = Depends(get_db)):
    query = models.Query(
        question=payload.question,
        source=payload.source,
        status="received",
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


@router.get("/{query_id}", response_model=schemas.QueryRead)
def get_query(query_id: int, db: Session = Depends(get_db)):
    query = db.get(models.Query, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    return query


@router.get("/", response_model=List[schemas.QueryRead])
def list_queries(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(models.Query)
        .order_by(models.Query.created_at.desc())
        .limit(limit)
        .all()
    )
