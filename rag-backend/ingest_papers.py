import math
from typing import List, Dict, Any

import requests
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


# ===== Konfiguration =====

BACKEND_URL = "http://localhost:8000"
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "documents"

# 768-dim Modell (passt zur Qdrant-Collection)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"


# ===== Demo-Papers (später ersetzt du das durch echte Daten) =====

DEMO_PAPERS: List[Dict[str, Any]] = [
    {
        "external_id": "doi:10.1038/s41586-020-2008-3",
        "title": "Safety and efficacy of the mRNA vaccine against SARS-CoV-2",
        "text": (
            "Hintergrund: mRNA-basierte Impfstoffe wurden in Phase-3-Studien "
            "zur Prävention von COVID-19 getestet. Die Studie untersuchte Wirksamkeit "
            "und Sicherheit bei unterschiedlichen Altersgruppen, mit besonderem Fokus "
            "auf schwere Verläufe und Nebenwirkungsprofile..."
        ),
        "meta": {
            "doi": "10.1038/s41586-020-2008-3",
            "authors": ["Muster, A.", "Beispiel, B."],
            "year": 2020,
            "journal": "Nature",
            "peer_reviewed": True,
            "topics": ["COVID-19", "Impfstoff", "mRNA"],
        },
    },
    {
        "external_id": "arxiv:2301.01234",
        "title": "Retrieval-Augmented Generation for Science Journalism",
        "text": (
            "In dieser Arbeit untersuchen wir, wie Retrieval-Augmented Generation (RAG) "
            "für wissenschaftlichen Journalismus eingesetzt werden kann. Wir kombinieren "
            "semantische Vektorsuche mit kuratierten Wissensbasen, um die Zuverlässigkeit "
            "von Antworten zu erhöhen und Halluzinationen zu reduzieren..."
        ),
        "meta": {
            "source": "arXiv",
            "year": 2023,
            "peer_reviewed": False,
            "topics": ["RAG", "LLM", "Journalismus"],
        },
    },
]


# ===== Hilfsfunktionen =====

def chunk_text(
    text: str,
    max_chars: int = 800,
    overlap_chars: int = 100,
) -> List[str]:
    """
    Sehr einfache Chunking-Funktion:
    - based on characters (nicht Tokens, aber für Prototyp ok)
    - mit Overlap, damit Sätze nicht ganz zerschnitten werden
    """
    chunks: List[str] = []

    if not text:
        return chunks

    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        # Overlap
        start = end - overlap_chars

    return chunks


def create_document_in_backend(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    Paper via /documents-API im Backend anlegen.
    Wenn external_id schon existiert, versuch es nicht doppelt.
    """
    url = f"{BACKEND_URL}/documents/"
    payload = {
        "external_id": paper.get("external_id"),
        "title": paper["title"],
        "text": paper["text"],
        "meta": paper.get("meta", {}),
    }

    resp = requests.post(url, json=payload)
    if resp.status_code == 400 and "already exists" in resp.text:
        # Dann holen wir das existierende Dokument
        print(f"[Info] Document {paper.get('external_id')} existiert bereits. Hole bestehendes...")
        doc = fetch_document_by_external_id(paper["external_id"])
        return doc

    resp.raise_for_status()
    doc = resp.json()
    print(f"[OK] Document in Backend gespeichert: id={doc['id']} title={doc['title']}")
    return doc


def fetch_document_by_external_id(external_id: str) -> Dict[str, Any]:
    """
    Einfacher Workaround: hol alle Documents und filter lokal nach external_id.
    Für Prototyp ok, später besser eigenen Filter-Endpoint bauen.
    """
    url = f"{BACKEND_URL}/documents/"
    resp = requests.get(url, params={"limit": 500})
    resp.raise_for_status()
    docs = resp.json()
    for d in docs:
        if d.get("external_id") == external_id:
            return d
    raise RuntimeError(f"Document mit external_id={external_id} nicht gefunden")


def upsert_chunks_to_qdrant(
    qdrant: QdrantClient,
    model: SentenceTransformer,
    doc: dict,
    chunks: list[str],
):
    if not chunks:
        print(f"[Warn] Dokument {doc['id']} hat keinen Text / keine Chunks.")
        return

    vectors = model.encode(chunks).tolist()

    points: list[PointStruct] = []
    for idx, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
        # IDs als Integer, nicht als "1-0"
        point_id = doc["id"] * 10000 + idx

        payload = {
            "document_id": doc["id"],
            "chunk_index": idx,
            "title": doc["title"],
            "meta": doc.get("meta", {}),
            "chunk_text": chunk_text,
        }

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        )

    qdrant.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points,
    )
    print(f"[OK] {len(points)} Chunks für doc_id={doc['id']} in Qdrant gespeichert.")



def main():
    # 1. Embedding-Modell laden
    print(f"[Init] Lade Embedding-Modell: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # 2. Qdrant-Client initialisieren
    print(f"[Init] Verbinde mit Qdrant: {QDRANT_URL}")
    qdrant = QdrantClient(url=QDRANT_URL)

    # 3. Papers durchgehen
    for paper in DEMO_PAPERS:
        print(f"\n=== Ingest für Paper: {paper['title']} ===")

        # a) Paper in Backend speichern (Postgres)
        doc = create_document_in_backend(paper)

        # b) Text chunking
        chunks = chunk_text(doc["text"], max_chars=800, overlap_chars=100)
        print(f"[Info] {len(chunks)} Chunks erzeugt.")

        # c) Chunks in Qdrant upserten
        upsert_chunks_to_qdrant(qdrant, model, doc, chunks)

    print("\n[Done] Ingest-Prozess abgeschlossen.")


if __name__ == "__main__":
    main()
