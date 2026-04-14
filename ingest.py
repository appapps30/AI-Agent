"""
Ingestion module — loads documents from the knowledge base, chunks them,
generates embeddings via OpenAI, and persists a FAISS vector store.
"""
import os
import sys

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from rag_config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    KNOWLEDGE_BASE_DIR,
    VECTOR_STORE_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    SEPARATORS,
)


def validate_api_key():
    """Ensure the OpenAI API key is configured."""
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY is not set.")
        print("  export OPENAI_API_KEY='sk-...'")
        sys.exit(1)


def load_documents(directory: str):
    """
    Load all Markdown (.md) and text (.txt) files from the knowledge base.
    """
    loaders = {
        "**/*.md": TextLoader,
        "**/*.txt": TextLoader,
    }

    all_docs = []
    for glob_pattern, loader_cls in loaders.items():
        try:
            loader = DirectoryLoader(
                directory,
                glob=glob_pattern,
                loader_cls=loader_cls,
                loader_kwargs={"encoding": "utf-8"},
                show_progress=True,
            )
            docs = loader.load()
            print(f"  Loaded {len(docs)} file(s) matching '{glob_pattern}'")
            all_docs.extend(docs)
        except Exception as e:
            print(f"  Warning: Could not load '{glob_pattern}': {e}")

    if not all_docs:
        print(f"ERROR: No documents found in {directory}")
        sys.exit(1)

    return all_docs


def chunk_documents(documents):
    """
    Split documents into overlapping chunks using recursive character splitting.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = splitter.split_documents(documents)
    print(f"  Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


def build_vector_store(chunks):
    """
    Generate embeddings and build a FAISS vector store.
    """
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

    print(f"  Generating embeddings with '{EMBEDDING_MODEL}'...")
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store


def save_vector_store(vector_store):
    """
    Persist the FAISS vector store to disk.
    """
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    vector_store.save_local(VECTOR_STORE_PATH)
    print(f"  Vector store saved to '{VECTOR_STORE_PATH}'")


def ingest():
    """
    Full ingestion pipeline: load → chunk → embed → save.
    """
    print("=" * 60)
    print("  RAG PIPELINE — INGESTION")
    print("=" * 60)

    validate_api_key()

    print("\n[1/4] Loading documents...")
    documents = load_documents(KNOWLEDGE_BASE_DIR)

    print("\n[2/4] Chunking documents...")
    chunks = chunk_documents(documents)

    print("\n[3/4] Building vector store...")
    vector_store = build_vector_store(chunks)

    print("\n[4/4] Saving vector store...")
    save_vector_store(vector_store)

    print("\n" + "=" * 60)
    print("  INGESTION COMPLETE")
    print(f"  Documents: {len(documents)}")
    print(f"  Chunks:    {len(chunks)}")
    print(f"  Store:     {VECTOR_STORE_PATH}")
    print("=" * 60)

    return vector_store


if __name__ == "__main__":
    ingest()
