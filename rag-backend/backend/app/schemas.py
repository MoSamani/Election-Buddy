from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from typing import List

# Query

class QueryCreate(BaseModel):
    question: str = Field(..., min_length=1)
    source: Optional[str] = Field(default=None)


class QueryRead(BaseModel):
    id: int
    question: str
    created_at: datetime
    status: str
    source: Optional[str]

    class Config:
        from_attributes = True


# Feedback

class FeedbackCreate(BaseModel):
    query_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class FeedbackRead(BaseModel):
    id: int
    query_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Document – für späteren Ingestor

class DocumentCreate(BaseModel):
    external_id: Optional[str] = None
    title: str
    text: str
    meta: Optional[dict] = None


class DocumentRead(BaseModel):
    id: int
    external_id: Optional[str]
    title: str
    text: str
    meta: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    document_id: int
    chunk_index: int
    score: float
    title: str
    chunk_text: str
    meta: Optional[dict] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

class RagAnswerRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)


class RagSource(BaseModel):
    document_id: int
    chunk_index: int
    title: str
    chunk_text: str
    meta: Optional[dict] = None
    score: float


class RagAnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[RagSource]