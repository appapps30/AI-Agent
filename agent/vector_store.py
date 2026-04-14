"""
Vector Store module — ChromaDB for storing and searching page element embeddings.
"""
import json
import chromadb
from config import CHROMA_COLLECTION, TOP_K_RESULTS
from agent.embedder import Embedder


class VectorStore:
    def __init__(self, embedder: Embedder, collection_name: str = None):
        self.embedder = embedder
        self._collection_name = collection_name or CHROMA_COLLECTION
        self.client = chromadb.Client()  # in-memory, resets each run
        self.collection = self.client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._id_counter = 0

    def reset(self):
        """Clear the collection for a new page."""
        self.client.delete_collection(self._collection_name)
        self.collection = self.client.create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._id_counter = 0

    def store_chunks(self, chunks: list[dict]):
        """
        Store a list of chunks. Each chunk must have a 'text' key.
        Additional keys are stored as metadata.
        """
        texts = [c["text"] for c in chunks]
        if not texts:
            return

        embeddings = self.embedder.embed_texts(texts)

        ids = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            self._id_counter += 1
            ids.append(f"chunk_{self._id_counter}")
            meta = {"source": "page"}
            if "elements" in chunk:
                meta["elements"] = json.dumps(chunk["elements"])
            if "html_tag" in chunk:
                meta["html_tag"] = chunk["html_tag"]
            metadatas.append(meta)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        """Search for chunks most relevant to the query."""
        query_embedding = self.embedder.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )

        matches = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            elements = []
            if "elements" in meta:
                elements = json.loads(meta["elements"])

            matches.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "distance": results["distances"][0][i],
                "elements": elements,
                "html_tag": meta.get("html_tag", ""),
            })

        return matches
