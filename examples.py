#!/usr/bin/env python3
"""
Example queries demonstrating the RAG pipeline capabilities.
Run after ingestion: python ingest.py && python examples.py
"""
from chain import ask_with_sources
from retriever import load_vector_store

EXAMPLE_QUESTIONS = [
    "What is the first step in the INR Trial App flow?",
    "How much does the Basic Monthly plan cost in INR?",
    "What payment methods are available on the Razorpay checkout?",
    "What pages come pre-built with the app after creation?",
    "When does the trial period expire?",
    "What onboarding questions does the user need to answer?",
    "What URL is used for the Razorpay checkout?",
    "What categories can I choose when creating an app?",
    "What features can be added in the app editor?",
    "What security badges are shown on the payment page?",
]


def main():
    print("=" * 60)
    print("  RAG Pipeline — Example Queries")
    print("=" * 60)

    vector_store = load_vector_store()

    for i, question in enumerate(EXAMPLE_QUESTIONS, 1):
        print(f"\n{'─' * 60}")
        print(f"  Q{i}: {question}")
        print(f"{'─' * 60}")

        result = ask_with_sources(question, vector_store)
        print(f"\n  Answer: {result['answer']}")
        print(f"\n  [Used {result['num_chunks_used']} source chunks]")


if __name__ == "__main__":
    main()
