# 3. What is RAG? (Retrieval-Augmented Generation)

## The core problem

A language model's knowledge is frozen at training time and is general-
purpose — it doesn't know your product's quirks, your team's past decisions,
or which of its own previous answers people actually found useful. Asking it
to "just know" your domain means either fine-tuning (expensive, slow to
update) or accepting mediocre, generic answers.

**RAG (Retrieval-Augmented Generation)** takes a different approach:

1. Keep a store of real, trustworthy text (documents, past answers, approved
   examples) outside the model.
2. When a new question comes in, **retrieve** the most relevant pieces from
   that store.
3. Feed those retrieved pieces to the model **alongside** the question, so it
   generates an answer *grounded* in real material instead of guessing.

## Embeddings: how "similar" is measured

To retrieve "the most relevant" text, you need a notion of similarity that
isn't just keyword matching. An **embedding** is a fixed-length vector of
numbers representing a piece of text's meaning — texts with similar meaning
produce vectors that point in similar directions.

```python
embed_text("reset my password")       -> [0.02, -0.11, 0.04, ...]
embed_text("I forgot my password")    -> [0.03, -0.09, 0.05, ...]  # similar!
embed_text("order a pizza")           -> [-0.40, 0.33, -0.02, ...] # different
```

**Cosine similarity** measures how close two vectors point (1.0 = identical
direction, 0.0 = unrelated, -1.0 = opposite):

```python
cosine_similarity(embed_text("reset my password"),
                   embed_text("I forgot my password"))   # high, e.g. 0.8+
```

Real systems typically use a hosted embeddings model (OpenAI, Cohere,
open-source sentence-transformers, etc.) producing vectors with hundreds or
thousands of dimensions, stored in a vector-capable database (pgvector,
FAISS, Chroma, etc.) so similarity search stays fast even at millions of
rows.

This training module's offline fallback (`mini_rag/embeddings.py`) uses a
much simpler **hashed bag-of-words** vector — good enough to demonstrate the
retrieval mechanics with zero installs, not a production-grade embedding.
When `OPENAI_API_KEY` is set, the exact same function call transparently uses
real embeddings instead.

## The retrieval step

```
                     ┌─────────────────────────┐
  new question  ───► │ embed + cosine-similarity│ ───► top-K most similar
                     │   search over stored      │      stored entries
                     │   embeddings              │
                     └─────────────────────────┘
```

Only the top few most-similar stored entries are handed to the model as
context — not the whole knowledge base. This keeps answers fast, cheap, and
focused.

## Where "self-improving" comes in

A static RAG system retrieves from a knowledge base someone manually wrote
and curated. A **self-improving** RAG system does something more interesting:
it grows its own knowledge base from the application's real usage —
specifically, from answers a human has explicitly approved as good. That's
the subject of the next lesson.

## Exercises

1. In a Python shell, run:
   ```python
   from mini_rag.embeddings import embed_text, cosine_similarity
   a = embed_text("how do I cancel my subscription")
   b = embed_text("how can I stop my subscription")
   c = embed_text("what's the weather today")
   print(cosine_similarity(a, b), cosine_similarity(a, c))
   ```
   Confirm the similar-meaning pair scores higher than the unrelated pair.
2. Try two sentences that mean the same thing but share *no* words at all
   (e.g. "my password doesn't work" vs. "I can't log in"). Does the
   hashed-bag-of-words fallback still see them as similar? Why or why not?
   (This is a good illustration of why production systems use real embedding
   models instead of hashing tricks — real embeddings capture meaning, not
   just shared vocabulary.)

Next: [04-building-a-self-improving-rag.md](04-building-a-self-improving-rag.md)
