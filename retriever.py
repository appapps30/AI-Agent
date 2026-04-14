"""
Retriever module — loads the persisted FAISS vector store and provides
a retriever interface for the RAG chain.
"""
import sys
import os

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from rag_config import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    VECTOR_STORE_PATH,
    TOP_K,
    SEARCH_TYPE,
    MMR_FETCH_K,
    MMR_LAMBDA,
)


def load_vector_store():
    """
    Load the persisted FAISS vector store from disk.
    """
    if not os.path.exists(VECTOR_STORE_PATH):
        print(f"ERROR: Vector store not found at '{VECTOR_STORE_PATH}'.")
        print("  Run 'python ingest.py' first to build the vector store.")
        sys.exit(1)

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

    vector_store = FAISS.load_local(
        VECTOR_STORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return vector_store


def get_retriever(vector_store=None):
    """
    Return a LangChain retriever from the vector store.

    Supports two search strategies:
      - "similarity" : plain cosine-similarity top-k
      - "mmr"        : Maximal Marginal Relevance (diversity + relevance)
    """
    if vector_store is None:
        vector_store = load_vector_store()

    if SEARCH_TYPE == "mmr":
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": TOP_K,
                "fetch_k": MMR_FETCH_K,
                "lambda_mult": MMR_LAMBDA,
            },
        )
    else:
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": TOP_K},
        )

    return retriever


def retrieve(query: str, retriever=None):
    """
    Retrieve relevant chunks for a given query string.
    Returns a list of Document objects.
    """
    if retriever is None:
        retriever = get_retriever()

    results = retriever.invoke(query)
    return results


if __name__ == "__main__":
    # Quick test
    query = "What happens after the payment is successful?"
    print(f"Query: {query}\n")
    docs = retrieve(query)
    for i, doc in enumerate(docs, 1):
        print(f"--- Chunk {i} (score: n/a for retriever) ---")
        print(doc.page_content[:300])
        print()
