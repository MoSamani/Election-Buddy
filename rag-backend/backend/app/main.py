from fastapi import FastAPI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from .routers import search as search_router

from .config import settings
from .db import Base, engine
from .routers import query as query_router
from .routers import feedback as feedback_router
from .routers import documents as documents_router
from .routers import rag as rag_router

from fastapi.middleware.cors import CORSMiddleware

def init_db():
    # Für den Anfang einfach: Tabellen bei Start erstellen
    Base.metadata.create_all(bind=engine)


def init_qdrant():
    client = QdrantClient(url=settings.qdrant_url)
    collections = client.get_collections().collections
    names = {c.name for c in collections}
    if settings.qdrant_collection not in names:
        # Placeholder: Vektorgröße 768 – musst du später an dein Embedding anpassen
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
    return client


app = FastAPI(
    title="RAG Backend – Wissenschaftsjournalismus",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init bei Startup
qdrant_client: QdrantClient | None = None


@app.on_event("startup")
def on_startup():
    global qdrant_client
    init_db()
    qdrant_client = init_qdrant()


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# Router registrieren
app.include_router(query_router.router)
app.include_router(feedback_router.router)
app.include_router(documents_router.router)  
app.include_router(search_router.router)
app.include_router(rag_router.router) 