"""
RAG Chain module — connects the retriever to the OpenAI LLM via a
LangChain prompt template to produce grounded answers.
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from rag_config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    TEMPERATURE,
    SYSTEM_PROMPT,
    USER_PROMPT,
)
from retriever import get_retriever, load_vector_store


def format_docs(docs):
    """
    Concatenate retrieved document chunks into a single context string.
    """
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        formatted.append(f"[Chunk {i} | Source: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)


def build_chain(vector_store=None):
    """
    Build the full RAG chain:
      question → retriever → format context → prompt → LLM → parse output
    """
    retriever = get_retriever(vector_store)

    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        openai_api_key=OPENAI_API_KEY,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])

    # LCEL chain
    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask(question: str, chain=None, vector_store=None):
    """
    Ask a question and get a grounded answer from the RAG pipeline.
    Returns the answer string.
    """
    if chain is None:
        chain = build_chain(vector_store)

    answer = chain.invoke(question)
    return answer


def ask_with_sources(question: str, vector_store=None):
    """
    Ask a question and return both the answer and the source chunks used.
    """
    if vector_store is None:
        vector_store = load_vector_store()

    retriever = get_retriever(vector_store)

    # Retrieve source docs
    source_docs = retriever.invoke(question)

    # Build and run chain
    chain = build_chain(vector_store)
    answer = chain.invoke(question)

    sources = []
    for doc in source_docs:
        sources.append({
            "content": doc.page_content[:200] + "...",
            "source": doc.metadata.get("source", "unknown"),
        })

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "num_chunks_used": len(source_docs),
    }
