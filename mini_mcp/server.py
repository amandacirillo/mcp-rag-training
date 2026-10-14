"""The tool-calling loop ('the model decides, the server dispatches').

Two model clients are provided behind the same interface:

- `MockModel`  — a tiny rule-based stand-in so the whole demo runs offline,
  with no API key, in classrooms/airplanes/etc. It looks at the user's text
  and decides which tool (if any) a real model would plausibly have called.
- `OpenAIModel` — a thin wrapper around a real chat-completions call with
  function/tool calling, used automatically when OPENAI_API_KEY is set.

`run_turn()` is the actual MCP-shaped loop: send the user message + tool
schemas to the model -> if the model asks for a tool call, dispatch it against
our own database -> feed the tool result back to the model -> return the
final answer. This is the same round trip a real MCP client/host performs.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from mini_mcp.tools import dispatch, tool_schemas


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


class MockModel:
    """Deterministic, offline stand-in for an LLM with tool-calling.

    Not meant to be clever — just enough pattern matching to demonstrate the
    tool-calling round trip without needing network access or an API key.
    """

    GENRES = ["fantasy", "sci-fi", "science", "software", "history"]

    def decide(self, user_message: str) -> ToolCall | None:
        text = user_message.lower()

        title_match = re.search(r"(?:copies of|availability of|is)\s+['\"]?([a-z0-9 ,'-]+?)['\"]?(?:\?|$)", text)
        if "available" in text or "copies" in text or "borrow" in text:
            if title_match:
                return ToolCall("get_book_availability", {"title": title_match.group(1).strip()})

        if "genre" in text and "list" in text:
            return ToolCall("list_genres")

        if "recommend" in text or "suggest" in text:
            for genre in self.GENRES:
                if genre in text:
                    return ToolCall("recommend_books", {"genre": genre})

        author_match = re.search(r"by\s+([a-z. ]+)", text)
        if author_match:
            return ToolCall("search_books", {"author": author_match.group(1).strip()})

        for genre in self.GENRES:
            if genre in text:
                return ToolCall("search_books", {"genre": genre})

        return None

    def finish(self, user_message: str, tool_name: str | None, tool_result: dict | None) -> str:
        if tool_name is None:
            return (
                "I'm not sure which catalog lookup that needs — try asking about "
                "a genre, an author, a specific book's availability, or ask me to "
                "recommend something."
            )
        return f"[tool={tool_name}] result={tool_result}"


class OpenAIModel:
    """Thin wrapper that uses a real model with tool/function calling.

    Only constructed (and only imports `openai`) when OPENAI_API_KEY is set,
    so the rest of the demo works with zero installs beyond stdlib.
    """

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        from openai import OpenAI  # imported lazily on purpose

        self.client = OpenAI()
        self.model = model

    def run(self, user_message: str) -> str:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": schema["parameters"],
                },
            }
            for schema in tool_schemas()
        ]
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": "You are a helpful library assistant. Use the provided "
                "tools to answer questions about the catalog instead of guessing.",
            },
            {"role": "user", "content": user_message},
        ]
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or ""

        messages.append(message)
        for call in message.tool_calls:
            import json

            args = json.loads(call.function.arguments or "{}")
            result = dispatch(call.function.name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                }
            )

        follow_up = self.client.chat.completions.create(model=self.model, messages=messages)
        return follow_up.choices[0].message.content or ""


def run_turn(user_message: str) -> str:
    """Run one assistant turn. Picks a real or mock model automatically."""
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIModel().run(user_message)

    model = MockModel()
    call = model.decide(user_message)
    if call is None:
        return model.finish(user_message, None, None)

    result = dispatch(call.name, call.arguments)
    return model.finish(user_message, call.name, result)
