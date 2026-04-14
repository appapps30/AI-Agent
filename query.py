#!/usr/bin/env python3
"""
Interactive query interface for the INR Trial App RAG pipeline.

Usage:
    python query.py                      # interactive REPL mode
    python query.py "your question"      # single question mode
    python query.py --sources "question" # show source chunks too
"""
import sys
import json

from rag_config import OPENAI_API_KEY
from retriever import load_vector_store
from chain import build_chain, ask_with_sources


def print_banner():
    print()
    print("=" * 60)
    print("  Appy Pie INR Trial App — RAG Query Interface")
    print("=" * 60)
    print("  Type your question and press Enter.")
    print("  Commands: 'quit' / 'exit' to leave, 'sources' to toggle source display")
    print("=" * 60)
    print()


def run_interactive():
    """Interactive REPL mode."""
    if not OPENAI_API_KEY:
        print("ERROR: Set OPENAI_API_KEY environment variable first.")
        sys.exit(1)

    print_banner()
    print("Loading vector store...")
    vector_store = load_vector_store()
    chain = build_chain(vector_store)
    show_sources = False

    print("Ready! Ask away.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if question.lower() == "sources":
            show_sources = not show_sources
            state = "ON" if show_sources else "OFF"
            print(f"  [Source display: {state}]\n")
            continue

        try:
            if show_sources:
                result = ask_with_sources(question, vector_store)
                print(f"\nAssistant: {result['answer']}\n")
                print(f"  [{result['num_chunks_used']} chunks used]")
                for i, src in enumerate(result["sources"], 1):
                    print(f"  Source {i}: ...{src['content'][:120]}...")
                print()
            else:
                answer = chain.invoke(question)
                print(f"\nAssistant: {answer}\n")

        except Exception as e:
            print(f"\nError: {e}\n")


def run_single(question: str, with_sources: bool = False):
    """Single question mode."""
    if not OPENAI_API_KEY:
        print("ERROR: Set OPENAI_API_KEY environment variable first.")
        sys.exit(1)

    if with_sources:
        result = ask_with_sources(question)
        print(json.dumps(result, indent=2))
    else:
        vector_store = load_vector_store()
        chain = build_chain(vector_store)
        answer = chain.invoke(question)
        print(answer)


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        run_interactive()
    elif args[0] == "--sources" and len(args) > 1:
        run_single(" ".join(args[1:]), with_sources=True)
    else:
        run_single(" ".join(args))
