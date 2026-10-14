"""Interactive CLI for the self-improving help-desk RAG demo.

Run with:  python -m mini_rag.app

Flow per question:
1. Search the knowledge base for similar *accepted* past answers.
2. If a good match is found, answer grounded in it.
   Otherwise, produce a best-effort draft answer.
3. Ask the user: was this helpful?
4. If yes, embed and store the question/answer pair as a new accepted entry —
   so the next person who asks something similar gets a grounded answer too.

This is the whole 'continually influenced by accepted results from its own
application' loop, in about 60 lines.
"""
from __future__ import annotations

import os

from mini_rag.knowledge_base import add_entry, find_similar

SIMILARITY_THRESHOLD = 0.35


def draft_answer(question: str) -> str:
    """Best-effort answer when nothing similar has been accepted yet.

    Uses a real model if OPENAI_API_KEY is set, otherwise a canned stand-in
    so the demo still runs offline.
    """
    if os.environ.get("OPENAI_API_KEY"):
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a concise help-desk assistant."},
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content or ""
    return (
        f"(best-effort draft, no prior accepted answer found) "
        f"Here's a general answer to '{question}': please consult the docs "
        f"or ask a teammate — once someone accepts a good answer here, "
        f"I'll remember it for next time."
    )


def answer_question(question: str) -> tuple[str, bool]:
    """Returns (answer_text, was_grounded_in_accepted_kb)."""
    matches = find_similar(question, top_k=1, accepted_only=True)
    if matches and matches[0].similarity is not None and matches[0].similarity >= SIMILARITY_THRESHOLD:
        best = matches[0]
        return (
            f"(grounded in an accepted answer, similarity={best.similarity:.2f})\n"
            f"Q: {best.question}\nA: {best.answer}",
            True,
        )
    return draft_answer(question), False


def main() -> None:
    print("Self-Improving Help Desk — ask a question.")
    print("Every answer you mark as helpful is remembered for future questions.")
    print("Type 'quit' to exit.\n")
    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in {"quit", "exit"}:
            break

        answer, grounded = answer_question(question)
        print(f"\nAnswer: {answer}\n")

        if grounded:
            continue  # already a previously-accepted answer; nothing new to learn

        choice = input("Was this helpful? Mark it accepted so the KB learns from it? [y/N]: ").strip().lower()
        if choice == "y":
            add_entry(question, answer, accepted=True)
            print("Stored as an accepted answer — future similar questions will use it.\n")
        else:
            print("Not stored. The knowledge base is unchanged.\n")


if __name__ == "__main__":
    main()
