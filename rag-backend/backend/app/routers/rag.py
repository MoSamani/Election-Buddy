from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from openai import OpenAI

from .. import schemas, models
from ..deps import get_db
from ..config import settings
from ..embeddings import embed_text
import requests

router = APIRouter(prefix="/rag_answer", tags=["rag"])


def retrieve_context(
    question: str,
    top_k: int,
    db: Session,
    peer_reviewed_only: bool = False,
) -> List[schemas.SearchResult]:
    """
    Nutzt dieselbe Logik wie /search:
    - Query embedden
    - Qdrant REST-API callen
    - Dokumente aus Postgres holen
    - SearchResult-Liste zurückgeben

    Wenn peer_reviewed_only=True, werden nur Punkte mit payload.is_peer_reviewed == True berücksichtigt.
    """
    from ..schemas import SearchResult  # reuse

    # 1) Embedding
    query_vector = embed_text(question)

    # 2) Qdrant search
    qdrant_search_url = f"{settings.qdrant_url}/collections/{settings.qdrant_collection}/points/search"

    body = {
        "vector": query_vector,
        "limit": top_k,
        "with_payload": True,
    }

    # 🔹 Filter nach peer-reviewed Quellen (bool-Feld im Payload)
    if peer_reviewed_only:
        body["filter"] = {
            "must": [
                {
                    "key": "is_peer_reviewed",
                    "match": {"value": True},
                }
            ]
        }

    resp = requests.post(qdrant_search_url, json=body, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=f"Qdrant error {resp.status_code}: {resp.text}",
        )
    data = resp.json()
    hits = data.get("result", [])

    if not hits:
        return []

    # Dokument-IDs aus Payload einsammeln
    doc_ids = {
        (hit.get("payload") or {}).get("document_id")
        for hit in hits
    }
    doc_ids = {d for d in doc_ids if d is not None}

    documents = (
        db.query(models.Document)
        .filter(models.Document.id.in_(doc_ids))
        .all()
    )
    docs_by_id = {doc.id: doc for doc in documents}

    results: List[SearchResult] = []
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
            SearchResult(
                document_id=doc_id,
                chunk_index=chunk_index,
                score=score,
                title=title,
                chunk_text=chunk_text,
                meta=meta,
            )
        )

    return results


def build_system_prompt() -> str:
    return (
        "Du bist ein Assistent für Wissenschaftsjournalismus.\n"
        "Antworte sachlich, präzise und verständlich auf Deutsch.\n"
        "Nutze ausschließlich die bereitgestellten Kontexte aus wissenschaftlichen Artikeln, "
        "Papers und Pressemitteilungen.\n"
        "Wenn die Kontexte nicht ausreichen, sage ehrlich, dass die Informationslage unklar ist.\n"
        "Erfinde keine Studien, keine Zahlen und keine Zitate.\n"
    )


def build_user_prompt(question: str, contexts: List[schemas.SearchResult]) -> str:
    parts = []
    for i, ctx in enumerate(contexts):
        meta = ctx.meta or {}
        year = meta.get("year", "unbekannt")
        journal = meta.get("journal") or meta.get("source") or "unbekannt"
        parts.append(
            f"[Kontext {i+1}]\n"
            f"Titel: {ctx.title}\n"
            f"Jahr: {year}, Quelle: {journal}\n"
            f"Textauszug:\n{ctx.chunk_text}\n"
        )

    context_block = "\n\n".join(parts) if parts else "Keine passenden Kontexte gefunden.\n"

    return (
        f"Frage:\n{question}\n\n"
        f"Kontexte:\n{context_block}\n\n"
        "Aufgabe:\n"
        "Formuliere eine Antwort auf die Frage, die sich eng an die Kontexte hält. "
        "Weise auf Unsicherheiten hin, falls die Evidenzlage unklar ist.\n"
    )


@router.post("/", response_model=schemas.RagAnswerResponse)
def rag_answer(payload: schemas.RagAnswerRequest, db: Session = Depends(get_db)):
    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=settings.openai_api_key)

    # 1) Retrieval
    contexts = retrieve_context(
        question=payload.question,
        top_k=payload.top_k,
        db=db,
        peer_reviewed_only=getattr(payload, "peer_reviewed_only", False),
    )

    # 1a) Filter nach Score (z.B. >= 0.5)
    score_threshold = 0.5
    filtered_contexts = [c for c in contexts if c.score >= score_threshold]

    # Fallback: wenn nichts den Threshold schafft, nimm einfach den besten
    if not filtered_contexts and contexts:
        filtered_contexts = [contexts[0]]

    # 2) Prompt bauen mit filtered_contexts
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(payload.question, filtered_contexts)

    # 3) LLM Call
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        answer_text = completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    # 4) Sources ebenfalls nur aus filtered_contexts bauen
    sources = [
        schemas.RagSource(
            document_id=ctx.document_id,
            chunk_index=ctx.chunk_index,
            title=ctx.title,
            chunk_text=ctx.chunk_text,
            meta=ctx.meta,
            score=ctx.score,
        )
        for ctx in filtered_contexts
    ]

    return schemas.RagAnswerResponse(
        question=payload.question,
        answer=answer_text,
        sources=sources,
    )
