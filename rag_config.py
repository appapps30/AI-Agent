"""
Configuration for the RAG Pipeline.
"""
import os

# --- LLM Settings ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o"
TEMPERATURE = 0.2

# --- Vector Store Settings ---
VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "vector_store")
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")

# --- Chunking Settings ---
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
SEPARATORS = ["\n---\n", "\n## ", "\n### ", "\n\n", "\n", " "]

# --- Retrieval Settings ---
TOP_K = 5  # Number of chunks to retrieve
SEARCH_TYPE = "mmr"  # "similarity" or "mmr" (Maximal Marginal Relevance)
MMR_FETCH_K = 10
MMR_LAMBDA = 0.7  # 0 = max diversity, 1 = max relevance

# --- Prompt Template ---
SYSTEM_PROMPT = """You are an expert QA assistant for the Appy Pie App Builder platform.
You answer questions about the INR Trial App creation flow — covering every step from
landing on the homepage, through app creation, authentication, onboarding, Razorpay payment,
and post-purchase app editing.

Use ONLY the provided context to answer. If the context does not contain enough information,
say so clearly. Always reference specific step numbers, URLs, or UI elements when relevant.

Context:
{context}
"""

USER_PROMPT = """Question: {question}

Answer:"""
