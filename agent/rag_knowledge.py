"""
RAG Knowledge module — Loads flow documentation and provides
stage-specific context to the LLM planner via vector search.
"""
import os
from agent.embedder import Embedder
from agent.vector_store import VectorStore


class RAGKnowledge:
    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.vector_store = VectorStore(embedder, collection_name="rag_knowledge")
        self._loaded = False

    def load_knowledge_base(self, knowledge_dir: str = None):
        """Load all .md files from the knowledge directory."""
        if knowledge_dir is None:
            knowledge_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")

        if not os.path.exists(knowledge_dir):
            print(f"  [rag] Knowledge dir not found: {knowledge_dir}")
            return

        chunks = []
        for fname in os.listdir(knowledge_dir):
            if fname.endswith(".md"):
                fpath = os.path.join(knowledge_dir, fname)
                with open(fpath, "r") as f:
                    content = f.read()

                # Split by sections (## headings)
                sections = content.split("\n## ")
                for i, section in enumerate(sections):
                    if i > 0:
                        section = "## " + section
                    text = section.strip()
                    if len(text) > 50:  # skip tiny sections
                        chunks.append({"text": text[:2000]})

        if chunks:
            self.vector_store.store_chunks(chunks)
            self._loaded = True
            print(f"  [rag] Loaded {len(chunks)} knowledge chunks from {knowledge_dir}")

    def query(self, question: str, top_k: int = 3) -> str:
        """Search knowledge base and return relevant context."""
        if not self._loaded:
            return ""

        matches = self.vector_store.search(question, top_k=top_k)
        if not matches:
            return ""

        context_parts = ["## RAG Knowledge Context\n"]
        for m in matches:
            context_parts.append(m["text"][:500])
            context_parts.append("---")

        return "\n".join(context_parts)
