# 5. Putting it together — one assistant, both patterns

So far these have been two separate demos. Real assistants usually combine
both patterns into a single tool-calling loop:

- **MCP-style tools** let the assistant query live, structured, authoritative
  data (inventory counts, order status, catalog contents).
- **Self-improving RAG** lets the assistant surface *unstructured*,
  human-approved knowledge (good example answers, previously solved
  questions) that keeps getting better as real usage accumulates.

## How they fit in one loop

Imagine extending `mini_mcp`'s tool registry with one more tool:

```python
"find_accepted_answers": {
    "description": "Search the help-desk knowledge base for previously "
                    "accepted answers similar to a question.",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
    "handler": lambda query, **_: {
        "matches": [
            {"question": e.question, "answer": e.answer, "similarity": e.similarity}
            for e in find_similar(query, top_k=3)
        ]
    },
},
```

Now the exact same decide → dispatch → respond loop from lesson 2 can pull
in retrieval-augmented context from lesson 4's knowledge base — the model
decides *when* to look something up, structured or not, through the same
uniform tool-calling interface. This is exactly how the real system this
training module is modeled on works: a chat assistant with read-only tools
over its own database, where one of those tools performs similarity search
over a continually-growing table of human-accepted items, instead of relying
on static embeddings baked in ahead of time.

## The feedback loop, end to end

```
 user asks the assistant something
          │
          ▼
 model decides which tool(s) to call (could be a DB lookup, could be a
 knowledge-base similarity search, could be both in sequence)
          │
          ▼
 host dispatches each tool call against real, authoritative data
          │
          ▼
 model writes a grounded final answer
          │
          ▼
 (if applicable) a human reviews/accepts the output somewhere in the app
          │
          ▼
 accepted output gets embedded and stored back into the knowledge base
          │
          └──────────────► makes the *next* similar question's retrieval better
```

The knowledge base isn't a one-time import of documentation — it's a living
record of what real users in the app actually found useful, continuously
re-fed into future answers.

## Design notes worth discussing

- **Read-only vs. write tools**: everything in `mini_mcp/tools.py` only
  reads. Before giving an assistant a tool that *writes* data (reserving a
  book, accepting an answer, canceling an order), think about what
  confirmation, authorization, or rate-limiting that tool needs that a
  read-only lookup doesn't.
- **Why gate retrieval on `accepted_only`**: covered in lesson 4 — without
  it, a self-improving system can reinforce bad answers just as easily as
  good ones.
- **Why keep the registry dependency-free**: this training module (and the
  real system it's based on) intentionally avoids pulling in a full protocol
  SDK for the tool registry itself — the *shape* (name/description/schema/
  dispatch) is what matters pedagogically, and it is straightforward to
  re-expose later behind a real MCP server, a different chat framework, or
  an HTTP API without changing how tools are defined.
- **Where this diverges from a "real" MCP server**: a production MCP server
  speaks a standard protocol over a transport (often JSON-RPC over
  stdio/HTTP) so *any* compliant client can discover and call its tools
  without custom integration code. `mini_mcp/` skips the protocol layer on
  purpose to stay runnable with zero extra services — the lesson is the tool
  registry pattern, not the wire format.

## Final exercise

Build the combined assistant described above:

1. Copy `mini_rag/knowledge_base.py`'s `find_similar` into a new tool in
   `mini_mcp/tools.py` (or import it directly — both modules are plain
   Python with no circular dependency issues).
2. Add a rule to `MockModel.decide()` so a question like "has anyone asked
   this before?" routes to your new tool.
3. Pre-seed the knowledge base with a couple of accepted entries using
   `mini_rag.knowledge_base.add_entry(..., accepted=True)`, then ask the
   combined assistant a related question and confirm it retrieves them.
4. Write a test exercising the whole path: seed → ask → assert the tool call
   and its result.

You've now built, end to end, a miniature version of both patterns used
together — the same architecture shape used by real production assistants
that combine live tool access with a continually-learning knowledge base.
