import pytest

from mini_mcp import db, tools
from mini_mcp.server import MockModel, run_turn


@pytest.fixture(autouse=True)
def fresh_db():
    db.reset_database()
    yield
    db.reset_database()


def test_list_genres_returns_seeded_genres():
    result = tools.list_genres()
    assert "fantasy" in result["genres"]
    assert "software" in result["genres"]


def test_search_books_by_genre():
    result = tools.search_books(genre="fantasy")
    titles = {b["title"] for b in result["books"]}
    assert "The Hobbit" in titles
    assert "Dune" not in titles


def test_search_books_by_author_partial_match():
    result = tools.search_books(author="tolkien")
    assert any(b["title"] == "The Hobbit" for b in result["books"])


def test_get_book_availability_found_and_unavailable():
    result = tools.get_book_availability(title="Clean Code")
    assert result["found"] is True
    assert result["copies_available"] == 0
    assert result["can_borrow"] is False


def test_get_book_availability_not_found():
    result = tools.get_book_availability(title="Nonexistent Book Title")
    assert result["found"] is False


def test_recommend_books_orders_by_year_desc():
    result = tools.recommend_books(genre="sci-fi", limit=2)
    years = [r["year"] for r in result["recommendations"]]
    assert years == sorted(years, reverse=True)


def test_dispatch_unknown_tool_raises():
    with pytest.raises(KeyError):
        tools.dispatch("not_a_real_tool", {})


def test_dispatch_routes_to_handler():
    result = tools.dispatch("list_genres", {})
    assert "genres" in result


def test_mock_model_routes_availability_question():
    model = MockModel()
    call = model.decide("is Dune available?")
    assert call is not None
    assert call.name == "get_book_availability"


def test_mock_model_routes_recommendation_question():
    model = MockModel()
    call = model.decide("recommend some fantasy books")
    assert call is not None
    assert call.name == "recommend_books"
    assert call.arguments["genre"] == "fantasy"


def test_run_turn_end_to_end_offline(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    answer = run_turn("recommend some software books")
    assert "recommend_books" in answer
