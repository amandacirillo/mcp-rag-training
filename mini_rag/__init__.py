"""mini_rag — a tiny 'self-improving help desk' knowledge base.

The knowledge base starts empty. Every time a user accepts an answer as
good, that question/answer pair gets embedded and stored. Future questions
are answered by first retrieving the most similar *accepted* past answers —
this is the embed-on-accept pattern: the knowledge base is continually
influenced by what the application's own users have approved.
"""
