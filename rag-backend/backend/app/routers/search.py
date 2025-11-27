from typing import List

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db
from ..config import settings
from ..embeddings import embed_text

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=schemas.SearchResponse)
def search_documents(payload: schemas.SearchRequest, db: Session = Depends(get_db)):
    # 1) Query → Embedding
    query_vector = embed_text(payload.query)

    # 2) Qdrant per REST-API aufrufen
    qdrant_search_url = (
        f"{settings.qdrant_url}/collections/"
        f"{settings.qdrant_collection}/points/search"
    )

    try:
        resp = requests.post(
            qdrant_search_url,
            json={
                "vector": query_vector,
                "limit": payload.top_k,
                "with_payload": True,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Qdrant request failed: {e}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Qdrant error {resp.status_code}: {resp.text}",
        )

    data = resp.json()
    hits = data.get("result", [])

    if not hits:
        return schemas.SearchResponse(query=payload.query, results=[])

    # 3) Dokument-IDs aus Payload holen
    doc_ids = {
        (hit.get("payload") or {}).get("document_id")
        for hit in hits
    }
    doc_ids = {d for d in doc_ids if d is not None}

    if not doc_ids:
        return schemas.SearchResponse(query=payload.query, results=[])

    # 4) Dokumente aus Postgres holen
    documents = (
        db.query(models.Document)
        .filter(models.Document.id.in_(doc_ids))
        .all()
    )
    docs_by_id = {doc.id: doc for doc in documents}

    results: List[schemas.SearchResult] = []

    # 5) Hits in API-Response-Format umbauen
    for hit in hits:
        payload_data = hit.get("payload") or {}
        doc_id = payload_data.get("document_id")
        if doc_id not in docs_by_id:
            continue

        chunk_index = payload_data.get("chunk_index", 0)
        chunk_text = payload_data.get("chunk_text", "")
        title = payload_data.get("title") or docs_by_id[doc_id].title
        meta = payload_data.get("meta", docs_by_id[doc_id].meta)
        score = hit.get("score", 0.0)

        results.append(
            schemas.SearchResult(
                document_id=doc_id,
                chunk_index=chunk_index,
                score=score,
                title=title,
                chunk_text=chunk_text,
                meta=meta,
            )
        )

    return schemas.SearchResponse(
        query=payload.query,
        results=results,
    )
