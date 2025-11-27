from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from .db import Base


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(32), default="received", nullable=False)
    source = Column(String(64), nullable=True)  # z.B. "web", "internal"

    feedback = relationship("Feedback", back_populates="query")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # z.B. 1–5 oder -1 / +1
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    query = relationship("Query", back_populates="feedback")


class Document(Base):
    """
    Platzhalter für Inhalte, die du später per Data-Ingestor befüllst.
    Text selbst hier speichern, Embedding in Qdrant.
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, nullable=True)  # z.B. CMS-ID
    title = Column(String(512), nullable=False)
    text = Column(Text, nullable=False)
    meta  = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
