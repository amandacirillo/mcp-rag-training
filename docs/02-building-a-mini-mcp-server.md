# 2. Building a mini MCP server — code walkthrough

This lesson walks through `mini_mcp/` file by file. Read it with the code
open side by side.

## `db.py` — the app's own data

```python
DB_PATH = Path(__file__).parent / "library.db"
```

A single SQLite file, created and seeded with a small book catalog the first
time it's opened. This stands in for "your application's real database" —
in a production system this would be Postgres, MySQL, etc., but the pattern
is identical regardless of which database you use: tools read from it,
models never touch it directly.

## `tools.py` — the registry

This is the part to study closely. Each tool is plain Python:

```python
def get_book_availability(title: str, **_: Any) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT title, copies_available FROM books WHERE title LIKE ?",
        (f"%{title}%",),
    ).fetchone()
    ...
```

...registered alongside a name, description, and JSON Schema:

```python
TOOLS = {
    "get_book_availability": {
        "description": "Check how many copies of a specific book ... are available to borrow.",
        "parameters": {
            "type": "object",
            "properties": {"title": {"type": "string", ...}},
            "required": ["title"],
        },
        "handler": get_book_availability,
    },
    ...
}
```

Two functions expose this registry to the rest of the app:

- `tool_schemas()` — returns just the name/description/parameters for every
  tool. This is what gets shown to a model. Notice it **never** includes the
  handler function — the model can't call Python directly, only ask the host
  to run a tool by name.
- `dispatch(name, arguments)` — the single chokepoint where a tool name +
  arguments dict turns into a real function call. Every tool call in the
  whole system goes through this one function, which makes it a natural
  place to add logging, rate-limiting, or permission checks later.

## `server.py` — the decide → dispatch → respond loop

Two model implementations behind one shape:

- `MockModel` — offline, deterministic, rule-based. It exists purely so this
  training module runs without an API key. `decide()` looks at the user's
  text and returns a `ToolCall` (or `None`), standing in for what a real
  model's tool-calling decision would look like.
- `OpenAIModel` — a real chat-completions call with `tools=` set to
  `tool_schemas()`. If the model's response includes `tool_calls`, each one
  is dispatched and the result is appended to the conversation as a `role:
  "tool"` message before asking the model for its final answer. **This is
  the real, production-shaped round trip** — the mock model exists only to
  make the lesson runnable offline; the dispatch mechanics
  (`dispatch(call.function.name, args)`) are identical either way.

`run_turn()` picks whichever model is available:

```python
def run_turn(user_message: str) -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIModel().run(user_message)
    ...  # MockModel path
```

## `cli.py` — tying it together

A plain input loop. Every line you type becomes one call to `run_turn()`.

## Try it

```powershell
python -m mini_mcp.cli
```

```
You: is Clean Code available?
Assistant: [tool=get_book_availability] result={'found': True, 'title': 'Clean Code', 'copies_available': 0, 'can_borrow': False}

You: recommend some sci-fi
Assistant: [tool=recommend_books] result={'genre': 'sci-fi', 'recommendations': [...]}
```

(With `MockModel`, the "answer" is intentionally the raw tool result so you
can see exactly what was dispatched. Set `OPENAI_API_KEY` and re-run to see a
real model turn the same tool result into a natural-language sentence.)

## Exercises

1. Set `OPENAI_API_KEY` in your shell and re-run `python -m mini_mcp.cli`.
   Compare the raw mock output to the real model's natural-language answers
   for the same questions — the *tools* and *data* are identical either way.
2. Add input validation to `get_book_availability` so an empty `title`
   returns a clear error dict instead of matching every book. Add a test.
3. Add a write-capable tool, e.g. `reserve_book(title)` that decrements
   `copies_available` (floor at 0). Think about why a real system might want
   extra guardrails (confirmation, auth, rate limits) on tools that write
   data versus the read-only ones here.

Next: [03-what-is-rag.md](03-what-is-rag.md)
