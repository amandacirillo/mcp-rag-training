# 4. Building a self-improving RAG — code walkthrough

This lesson walks through `mini_rag/`. The big idea: **the knowledge base
starts empty, and only grows when a real user marks an answer as accepted.**

## `embeddings.py` — text to vector

Already covered in lesson 3. One detail worth noting: both the offline and
real implementation sit behind a single `embed_text(text)` function, so
nothing else in the codebase needs to know which one is active.

## `knowledge_base.py` — the self-improving store

The schema is deliberately small:

```python
CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    embedding TEXT NOT NULL,   -- JSON-encoded vector
    accepted INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
)
```

The `accepted` flag is the whole mechanism. Compare the two entry points:

```python
def add_entry(question, answer, accepted=False) -> int:
    """Embed and store a question/answer pair. This is the 'embed-on-accept'
    step: called the moment a human approves an answer, not before."""
    ...

def find_similar(query, top_k=3, accepted_only=True) -> list[Entry]:
    """... By default only *accepted* entries are searched — this is what
    keeps the knowledge base's answers grounded in human-approved output
    instead of every unreviewed draft that was ever generated."""
    ...
```

This is a direct, simplified version of a real pattern: a production app
might draft many candidate answers, but only the ones a human explicitly
accepts get embedded and become retrievable — the rest are discarded or kept
separately for audit, never surfacing in future answers. The knowledge base's
*quality bar is whatever the humans using the app decided was good enough to
accept*, and it rises over time as more gets accepted.

## `app.py` — the full loop

```python
def answer_question(question: str) -> tuple[str, bool]:
    matches = find_similar(question, top_k=1, accepted_only=True)
    if matches and matches[0].similarity >= SIMILARITY_THRESHOLD:
        return grounded_answer(matches[0]), True   # reuse accepted knowledge
    return draft_answer(question), False           # no good match yet
```

Then in the CLI loop: if the answer wasn't already grounded in something
accepted, ask the user whether it was helpful — and if yes, call
`add_entry(question, answer, accepted=True)`. That's the entire feedback
loop: **draft → human judgement → embed → store → retrieve next time.**

```
 first user asks "how do I reset my password?"
      │
      ▼
 no similar accepted entries yet ──► draft_answer() ──► user accepts
      │                                                        │
      ▼                                                        ▼
                                                    add_entry(..., accepted=True)
                                                                 │
 second user asks "I forgot my password, help?"                 │
      │                                                         │
      ▼                                                         │
 find_similar() now returns the earlier accepted entry  ◄───────┘
      │
      ▼
 answered instantly, grounded, no draft needed
```

## Why `accepted_only=True` by default matters

If `find_similar` searched *all* entries (including rejected/unreviewed
drafts), a single bad accepted-looking answer could get amplified every time
someone asks something similar — the system would be "self-worsening"
instead of self-improving. Gating retrieval on an explicit human-approval
flag is what keeps the feedback loop pointed in the right direction.

## Try it

```powershell
python -m mini_rag.app
```

```
Question: how do I reset my password?

Answer: (best-effort draft, no prior accepted answer found) ...

Was this helpful? Mark it accepted so the KB learns from it? [y/N]: y
Stored as an accepted answer — future similar questions will use it.

Question: I forgot my password, how do I get back in?

Answer: (grounded in an accepted answer, similarity=0.71)
Q: how do I reset my password?
A: (best-effort draft, no prior accepted answer found) ...
```

## Exercises

1. Lower `SIMILARITY_THRESHOLD` in `mini_rag/app.py` and observe how it
   changes whether a loosely-related question gets grounded or re-drafted.
   What happens if you set it to `0.0`? To `0.99`?
2. Add a `reject` path: if the user says the draft answer was *not* helpful,
   still store it via `add_entry(..., accepted=False)` so it's preserved for
   audit but never retrieved. Write a test confirming rejected entries never
   appear in `find_similar()` results.
3. Add a small CLI command to list the current count of accepted vs. total
   entries (`knowledge_base.count_entries()` already supports this).

Next: [05-putting-it-together.md](05-putting-it-together.md)
