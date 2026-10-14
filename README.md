# Mini MCP + Self-Improving RAG — Training Module

A small, dependency-light, **runnable** training module that teaches two ideas
by building tiny working versions of them:

1. **MCP-style tool-calling** — how an AI assistant can be given a registry of
   named, schema-described tools that query *its own* database, instead of
   hallucinating answers. (`mini_mcp/`)
2. **Self-improving RAG** — a knowledge base that starts empty and grows over
   time, fed only by answers that a human in the loop explicitly *accepts*.
   Later questions get better answers because the system learns from its own
   accepted output. (`mini_rag/`)

Both modules run **completely offline** with no API keys and no external
services — they use a local SQLite database and a deterministic, dependency-free
embedding fallback. If you set an `OPENAI_API_KEY` environment variable, both
modules will automatically switch to real LLM calls / real embeddings instead
of the offline stand-ins, so you can see the exact same code work either way.

This project is a standalone teaching example. It is not tied to any specific
company's internal systems, infrastructure, or cloud provider — every piece
here can be read top to bottom.

## Who this is for

Anyone curious about:
- What "MCP" (Model Context Protocol) tool-calling actually looks like in code
- What "RAG" (Retrieval-Augmented Generation) actually looks like in code
- How a production app can combine both: an assistant that calls tools *and*
  continually learns from the answers people approve

No prior AI/ML experience required — just basic Python.

## Setup

```powershell
cd mcp-rag-training
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

(Everything also works with zero installs beyond `pytest` if you just want to
read/run the core demos — `openai` is only imported lazily if you set an API key.)

## Run the demos

```powershell
# Part 1: mini MCP tool-calling assistant (library catalog)
python -m mini_mcp.cli

# Part 2: mini self-improving RAG help desk
python -m mini_rag.app
```

## Run the tests

```powershell
pytest
```

## Learning path

Read these in order — each has hands-on exercises at the end:

1. [`docs/01-what-is-mcp.md`](docs/01-what-is-mcp.md) — What MCP tool-calling is and why it matters
2. [`docs/02-building-a-mini-mcp-server.md`](docs/02-building-a-mini-mcp-server.md) — Walkthrough of `mini_mcp/`
3. [`docs/03-what-is-rag.md`](docs/03-what-is-rag.md) — What RAG is and why it matters
4. [`docs/04-building-a-self-improving-rag.md`](docs/04-building-a-self-improving-rag.md) — Walkthrough of `mini_rag/`
5. [`docs/05-putting-it-together.md`](docs/05-putting-it-together.md) — Combining both patterns in a real app

## Project layout

```
mini_mcp/        # Tool registry + dispatch + offline/online model client + CLI
mini_rag/        # Embeddings + vector-similarity knowledge base + accept-to-learn CLI
docs/            # The five lessons
tests/           # Unit tests for both modules
```
