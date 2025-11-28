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

def run_llm_judge(
    client: OpenAI,
    question: str,
    answer: str,
    reference_answer: str | None,
    contexts: list[schemas.SearchResult],
) -> tuple[float | None, str | None, str | None]:
    """
    Nutzt ein LLM als Judge, ähnlich wie in eval_rag.py.
    Gibt (score, label, explanation) zurück.
    score: 0–1 (1 = vollständig korrekt)
    """
    # Kontext kompakt zusammenbauen (optional)
    ctx_snippets = []
    for i, c in enumerate(contexts[:5]):
        ctx_snippets.append(
            f"[Kontext {i+1}] Titel: {c.title}\nTextauszug: {c.chunk_text[:400]}"
        )
    ctx_block = "\n\n".join(ctx_snippets) if ctx_snippets else "Keine Kontexte."

    # Wenn du in eval_rag.py schon einen Prompt hast, kannst du den hier verwenden.
    # Beispiel-Prompt:
    user_parts = [
        f"Frage:\n{question}",
        f"System-Antwort:\n{answer}",
        f"Kontexte (aus Retrieval):\n{ctx_block}",
    ]
    if reference_answer:
        user_parts.append(f"Referenz-Antwort (Gold):\n{reference_answer}")

    user_prompt = "\n\n".join(user_parts) + """

Bewerte die System-Antwort nach den folgenden Kriterien:
1. Faktische Korrektheit bezogen auf die Kontexte (und falls vorhanden die Referenz-Antwort)
2. Ob die Antwort bei Unsicherheit korrekt einschränkt statt zu halluzinieren
3. Ob zentrale Punkte der Referenz-Antwort abgedeckt wurden (falls vorhanden)

Gib deine Antwort im JSON-Format zurück, ohne weiteren Text, z. B.:

{
  "score": 0.85,
  "label": "teilweise korrekt",
  "explanation": "Begründung..."
}
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Du bist ein strenger, aber fairer wissenschaftlicher Gutachter. "
                        "Du bewertest nur den Wahrheitsgehalt und die Abdeckung der Antwort."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )
        raw = completion.choices[0].message.content or ""
    except Exception as e:
        print("LLM-Judge failed:", e)
        return None, None, None

    # Sehr einfache JSON-Parsing-Logik – in echt evtl. robustere Variante
    import json

    try:
        data = json.loads(raw)
        score = float(data.get("score")) if "score" in data else None
        label = data.get("label")
        explanation = data.get("explanation")
        return score, label, explanation
    except Exception as e:
        print("Parsing LLM-Judge-Output failed:", e, "raw:", raw)
        return None, None, raw[:500]  # im Zweifel Rohtext als "explanation"

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

    # 0) ChatSession holen oder neu anlegen
    conv_id = payload.conversation_id
    session_obj: models.ChatSession | None = None

    if conv_id is not None:
        session_obj = (
            db.query(models.ChatSession)
            .filter(models.ChatSession.id == conv_id)
            .first()
        )

    if session_obj is None:
        session_obj = models.ChatSession(
            title=payload.question[:180],
        )
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)

    # 1) Retrieval
    contexts = retrieve_context(
        payload.question,
        payload.top_k,
        db,
        # falls du peer_reviewed_only im retrieve_context schon eingebaut hast:
        # peer_reviewed_only=payload.peer_reviewed_only,
    )

    score_threshold = 0.4
    filtered_contexts = [c for c in contexts if c.score >= score_threshold]

    if not filtered_contexts and contexts:
        filtered_contexts = [contexts[0]]

        # 🔹 Precision@k für Retrieval berechnen (optional, wenn Ground-Truth vorhanden)
    precision_at_k: float | None = None
    if payload.relevant_document_ids:
        relevant_ids = set(payload.relevant_document_ids)
        retrieved_ids = [c.document_id for c in contexts]  # alle Top-k-Retrievals, noch ungefiltert

        k = len(retrieved_ids)
        if k > 0:
            hits = sum(1 for doc_id in retrieved_ids if doc_id in relevant_ids)
            precision_at_k = hits / k

        print(
            "DEBUG precision_at_k:",
            precision_at_k,
            "relevant:",
            relevant_ids,
            "retrieved:",
            retrieved_ids,
        )
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(payload.question, filtered_contexts)

    # 🔹 1b) Bisherigen Chat-Verlauf laden (ohne aktuelle Frage)
    # wir nehmen z.B. die letzten 8 Messages (4 User + 4 Assistant, je nach Verlauf)
    history_messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_obj.id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )

    # nur die letzten N nehmen, damit der Prompt nicht explodiert
    MAX_HISTORY_MSGS = 4
    history_messages = history_messages[-MAX_HISTORY_MSGS:]

    # in OpenAI-Format bringen
    history_for_llm = []
    for m in history_messages:
        role = "assistant" if m.role == "assistant" else "user"
        history_for_llm.append(
            {
                "role": role,
                "content": m.content,
            }
        )

    # 3) LLM Call mit Verlauf + aktuellem RAG-Prompt
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *history_for_llm,
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.2,
        )
        answer_text = completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    # 🔹 3b) Optional: LLM-Judge ausführen
    judge_score = None
    judge_label = None
    judge_explanation = None
    if payload.run_judge:
        judge_score, judge_label, judge_explanation = run_llm_judge(
            client=client,
            question=payload.question,
            answer=answer_text,
            reference_answer=payload.reference_answer,
            contexts=filtered_contexts,
        )

    # 4) Sources aus filtered_contexts bauen
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

    # 5) Messages speichern
    user_msg = models.ChatMessage(
        session_id=session_obj.id,
        role="user",
        content=payload.question,
        sources=None,
    )
    db.add(user_msg)

    assistant_msg = models.ChatMessage(
        session_id=session_obj.id,
        role="assistant",
        content=answer_text,
        sources=[s.model_dump() for s in sources],
    )
    db.add(assistant_msg)

    db.commit()

    return schemas.RagAnswerResponse(
        question=payload.question,
        answer=answer_text,
        sources=sources,
        conversation_id=session_obj.id,
        precision_at_k=precision_at_k,
        judge_score=judge_score,
        judge_label=judge_label,
        judge_explanation=judge_explanation,
    )
