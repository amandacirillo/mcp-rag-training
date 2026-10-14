import pytest

from mini_rag import knowledge_base as kb
from mini_rag.embeddings import cosine_similarity, embed_text
from mini_rag.app import answer_question


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    kb.reset_database()
    yield
    kb.reset_database()


def test_embed_text_is_deterministic_and_normalized():
    v1 = embed_text("how do I reset my password")
    v2 = embed_text("how do I reset my password")
    assert v1 == v2
    norm = sum(x * x for x in v1) ** 0.5
    assert abs(norm - 1.0) < 1e-6 or norm == 0.0


def test_cosine_similarity_identical_text_is_high():
    v = embed_text("reset my password please")
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_unrelated_text_is_lower():
    v1 = embed_text("reset my password")
    v2 = embed_text("order a pizza with extra cheese")
    assert cosine_similarity(v1, v1) > cosine_similarity(v1, v2)


def test_add_entry_and_find_similar_accepted_only():
    kb.add_entry("How do I reset my password?", "Go to settings > security > reset.", accepted=True)
    kb.add_entry("How do I delete my account?", "Draft, not yet reviewed.", accepted=False)

    results = kb.find_similar("I forgot my password, how do I reset it?", accepted_only=True)
    assert len(results) == 1
    assert "reset" in results[0].answer.lower()


def test_find_similar_excludes_unaccepted_by_default():
    kb.add_entry("How do I reset my password?", "unaccepted draft answer", accepted=False)
    results = kb.find_similar("how do I reset my password", accepted_only=True)
    assert results == []


def test_count_entries():
    kb.add_entry("q1", "a1", accepted=True)
    kb.add_entry("q2", "a2", accepted=False)
    assert kb.count_entries() == 2
    assert kb.count_entries(accepted_only=True) == 1


def test_answer_question_falls_back_to_draft_when_kb_empty():
    answer, grounded = answer_question("how do I reset my password?")
    assert grounded is False
    assert "draft" in answer.lower()


def test_answer_question_grounds_in_accepted_entry_once_learned():
    kb.add_entry(
        "How do I reset my password?",
        "Go to settings > security > reset.",
        accepted=True,
    )
    answer, grounded = answer_question("How do I reset my password?")
    assert grounded is True
    assert "settings" in answer.lower()


def test_set_accepted_flips_flag():
    entry_id = kb.add_entry("q", "a", accepted=False)
    assert kb.find_similar("q", accepted_only=True) == []
    kb.set_accepted(entry_id, True)
    results = kb.find_similar("q", accepted_only=True)
    assert len(results) == 1
