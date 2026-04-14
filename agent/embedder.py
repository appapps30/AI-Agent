"""
Embedder module — Generates vector embeddings using sentence-transformers.
"""
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL


class Embedder:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        return self.model.encode(query, show_progress_bar=False).tolist()
