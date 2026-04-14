# Appy Pie INR Trial App — RAG Pipeline

A Retrieval-Augmented Generation (RAG) pipeline that indexes the complete Appy Pie INR Trial App creation flow and answers questions about it using OpenAI GPT + LangChain + FAISS.

## Architecture

```
knowledge_base/          ← Markdown docs describing the flow
       ↓
   ingest.py             ← Load → Chunk → Embed → Save
       ↓
   vector_store/         ← Persisted FAISS index
       ↓
   retriever.py          ← Similarity / MMR search
       ↓
   chain.py              ← Prompt + LLM (GPT-4o)
       ↓
   query.py              ← Interactive REPL or CLI
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Ingest the knowledge base

```bash
python ingest.py
```

This reads all `.md` / `.txt` files from `knowledge_base/`, chunks them, generates embeddings via `text-embedding-3-small`, and saves a FAISS index to `vector_store/`.

### 4. Query the pipeline

**Interactive mode:**
```bash
python query.py
```

**Single question:**
```bash
python query.py "What payment methods are available?"
```

**With source chunks:**
```bash
python query.py --sources "How much does the trial cost?"
```

**Run example queries:**
```bash
python examples.py
```

## Project Structure

| File | Purpose |
|------|---------|
| `config.py` | All configuration (models, chunk sizes, prompts) |
| `ingest.py` | Document loading, chunking, embedding, FAISS persistence |
| `retriever.py` | Vector store loading and retrieval interface |
| `chain.py` | RAG chain connecting retriever → prompt → LLM |
| `query.py` | Interactive CLI and single-query interface |
| `examples.py` | 10 pre-built example queries |
| `knowledge_base/` | Source documents (Markdown) |
| `vector_store/` | Persisted FAISS index (auto-generated) |

## Configuration

Edit `config.py` to tune:

- **LLM_MODEL** — default `gpt-4o`, switch to `gpt-3.5-turbo` for lower cost
- **EMBEDDING_MODEL** — default `text-embedding-3-small`
- **CHUNK_SIZE / CHUNK_OVERLAP** — controls how documents are split
- **TOP_K** — number of chunks retrieved per query
- **SEARCH_TYPE** — `"similarity"` or `"mmr"` (Maximal Marginal Relevance)
- **TEMPERATURE** — LLM creativity (0.0 = deterministic, 1.0 = creative)

## Adding More Documents

Drop any `.md` or `.txt` files into `knowledge_base/` and re-run:

```bash
python ingest.py
```

The vector store will be rebuilt with the new content.

## Example Questions

- "What is the first step in creating an INR trial app?"
- "How much does the Basic Monthly plan cost?"
- "What categories can I choose from?"
- "What happens after payment is successful?"
- "What pages come pre-built with the app?"
- "What security badges are shown on the checkout page?"
