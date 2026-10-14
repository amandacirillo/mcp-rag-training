"""Turns text into a fixed-length vector so we can compare meaning with
cosine similarity.

Two implementations behind one function, `embed_text()`:

- Offline fallback: a deterministic 'hashed bag-of-words' embedding. It is
  not as good as a real model's embeddings, but it needs zero installs and
  zero network access, and is good enough for this demo's small vocabulary
  to show retrieval actually working.
- Real embeddings: used automatically when OPENAI_API_KEY is set, calling
  the standard embeddings endpoint.
"""
from __future__ import annotations

import hashlib
import math
import os
import re

VECTOR_SIZE = 256


def embed_text(text: str) -> list[float]:
    if os.environ.get("OPENAI_API_KEY"):
        return _embed_openai(text)
    return _embed_hashed_bow(text)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must be the same length to compare")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embed_hashed_bow(text: str, size: int = VECTOR_SIZE) -> list[float]:
    """Hash each word into one of `size` buckets and count occurrences.

    This is the 'hashing trick': a simple, dependency-free way to turn
    variable-length text into a fixed-length vector where texts sharing
    words land close together under cosine similarity.
    """
    vector = [0.0] * size
    words = re.findall(r"[a-z0-9]+", text.lower())
    for word in words:
        bucket = int(hashlib.sha256(word.encode()).hexdigest(), 16) % size
        vector[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def _embed_openai(text: str, model: str = "text-embedding-3-small") -> list[float]:
    from openai import OpenAI  # imported lazily on purpose

    client = OpenAI()
    response = client.embeddings.create(model=model, input=text)
    return list(response.data[0].embedding)
