from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document(payload: schemas.DocumentCreate, db: Session = Depends(get_db)):
    # optional: prüfen, ob external_id schon existiert
    if payload.external_id:
        existing = (
            db.query(models.Document)
            .filter(models.Document.external_id == payload.external_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Document with this external_id already exists",
            )

    doc = models.Document(
        external_id=payload.external_id,
        title=payload.title,
        text=payload.text,
        meta=payload.meta,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/", response_model=List[schemas.DocumentRead])
def list_documents(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Document).order_by(models.Document.created_at.desc())

    if search:
        # super simple Volltext-Filter (LIKE) – reicht für jetzt
        like = f"%{search}%"
        query = query.filter(
            models.Document.title.ilike(like)
            | models.Document.text.ilike(like)
        )

    return query.offset(offset).limit(limit).all()


@router.get("/{doc_id}", response_model=schemas.DocumentRead)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
