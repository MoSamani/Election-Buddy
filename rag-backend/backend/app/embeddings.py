from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"  # 768-Dim, passt zu Qdrant


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    # Wird beim ersten Aufruf geladen, danach gecached
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> List[float]:
    model = get_embedding_model()
    return model.encode(text).tolist()
