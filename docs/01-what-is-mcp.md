# 1. What is MCP? (Model Context Protocol / tool-calling)

## The core problem

Language models are good at *language*, not at knowing live facts about your
system: how many copies of a book are left, what a customer's order status
is, what's actually in your database right now. Ask a plain chat model "is
*Clean Code* available to borrow?" and it will either refuse or — worse —
confidently make something up.

**Tool-calling** (the pattern MCP — the Model Context Protocol — standardizes)
fixes this by giving the model a menu of **named, described, schema-validated
functions** it can ask to have run on its behalf, instead of answering from
memory.

## The shape of a tool

Every tool in this kind of system has the same four parts:

| Part | Purpose |
|---|---|
| `name` | A stable identifier the model refers to, e.g. `get_book_availability` |
| `description` | Plain English explanation of what it does and when to use it |
| `parameters` (JSON Schema) | What arguments it takes, and their types |
| `handler` | The actual function that runs against your real data |

The model never sees your database, your code, or your credentials. It only
ever sees the `name` + `description` + `parameters` of each tool — a kind of
menu — and it asks the host application to run one by name with some
arguments. The host runs it and hands back the result as plain text/JSON,
which the model then uses to write its final answer.

## The round trip

```
 user message
       │
       ▼
┌─────────────┐   "call get_book_availability(title='Clean Code')"
│    model    │ ───────────────────────────────────────────────►  ┌──────────┐
└─────────────┘                                                   │   host   │
       ▲                                                          │ (your    │
       │        {"found": true, "copies_available": 0}            │  app)    │
       └────────────────────────────────────────────────────────  └──────────┘
                                                                         │
                                                                         ▼
                                                                  queries YOUR
                                                                  real database
```

1. The host sends the user's message **and** the list of available tool
   schemas to the model.
2. The model decides: answer directly, or ask to call a tool (by name, with
   arguments matching its schema).
3. If it asks for a tool call, the host **dispatches** it — runs the real
   function against the real data — and sends the result back to the model
   as a new message.
4. The model writes its final answer, now grounded in real data instead of
   a guess.

This can repeat for several tool calls in a row before the model gives a
final answer (e.g. "list genres" then "recommend books in that genre").

## Why this matters in production

- **Correctness**: the model can't hallucinate "yes, 3 copies available" —
  it has to go through `get_book_availability`, which hits the real table.
- **Least privilege**: the model can only do what a tool explicitly allows.
  There's no tool called `delete_everything`, so it can't.
- **Auditability**: every tool call is a discrete, loggable event — you know
  exactly what data left your database and when.
- **Incrementally adoptable**: you can start with a handful of read-only
  tools (list, search, get-status) long before trusting an assistant with
  anything that writes data.

## What "MCP-style" means in this training module

A full MCP server speaks a specific JSON-RPC-based protocol so that *any*
MCP-compatible client (not just one specific chat app) can discover and call
its tools. For teaching purposes, `mini_mcp/` in this repo implements the
exact same **shape** — name/description/schema/dispatch, and the same
decide → dispatch → respond loop — using plain Python function calls instead
of a network protocol. That keeps the lesson runnable with zero extra
services, while making it trivial to swap in a real MCP server later: the
tool registry itself (`mini_mcp/tools.py`) wouldn't need to change at all.

## Exercises

1. Open `mini_mcp/tools.py`. Add a new tool, `count_books_by_genre`, that
   returns how many books exist in each genre. Give it a `name`,
   `description`, JSON Schema `parameters`, and a handler, then add it to the
   `TOOLS` registry.
2. Write a test in `tests/test_mini_mcp.py` that calls
   `tools.dispatch("count_books_by_genre", {})` and checks the result.
3. In `mini_mcp/server.py`, extend `MockModel.decide()` so a question like
   "how many fantasy books do you have?" routes to your new tool.
4. Run `python -m mini_mcp.cli` and ask your new question.

Next: [02-building-a-mini-mcp-server.md](02-building-a-mini-mcp-server.md)
