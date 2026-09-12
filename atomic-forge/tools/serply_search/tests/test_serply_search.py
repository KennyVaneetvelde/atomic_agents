import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tool.serply_search import (  # noqa: E402
    SerplySearchResultItem,
    SerplySearchTool,
    SerplySearchToolConfig,
    SerplySearchToolInputSchema,
    SerplySearchToolOutputSchema,
)


SEARCH_HIT = {
    "title": "Welcome to Python.org",
    "description": "Python is a programming language that lets you work quickly.",
    "position": 1,
    "realPosition": 1,
    "result_type": "organic",
    "link": "https://www.python.org/",
}

NEWS_HIT = {
    "title": "Python 3.14 released - example.com",
    "link": "https://example.com/python-3-14",
    "published": "Wed, 10 Jun 2026 07:00:00 GMT",
    "summary": '<a href="https://example.com/python-3-14">Python 3.14 released</a>',
    "source": {"href": "https://example.com", "title": "example.com"},
}

SCHOLAR_HIT = {
    "title": "SciPy 1.0: fundamental algorithms for scientific computing in Python",
    "link": "https://example.com/scipy-1-0",
    "id": "W3003257820",
    "author": {"names": "Pauli Virtanen, Ralf Gommers"},
    "description": "SciPy is an open-source scientific computing library.",
    "extras": {"citations": {"count": 12345}},
}


def _mock_session(status: int, payload: dict, reason: str = "OK") -> MagicMock:
    session = MagicMock()
    response = SimpleNamespace(status=status, reason=reason, json=AsyncMock(return_value=payload))
    session.get.return_value.__aenter__.return_value = response
    return session


@pytest.fixture
def tool():
    return SerplySearchTool(config=SerplySearchToolConfig(api_key="test-key", hl="de", gl="ch"))


def test_to_item_search(tool):
    item = SerplySearchTool._to_item(SEARCH_HIT, "python")
    assert isinstance(item, SerplySearchResultItem)
    assert item.query == "python"
    assert item.title == "Welcome to Python.org"
    assert item.url == "https://www.python.org/"
    assert item.description.startswith("Python is a programming language")
    assert item.position == 1
    assert item.published is None
    assert item.authors is None


def test_to_item_news(tool):
    """News entries carry a summary, a publish date, and a source dict."""
    item = SerplySearchTool._to_item(NEWS_HIT, "python")
    assert item.description.startswith("<a href=")
    assert item.published == "Wed, 10 Jun 2026 07:00:00 GMT"
    assert item.source == "example.com"
    assert item.position is None


def test_to_item_scholar(tool):
    """Scholar articles carry authors and a citation count."""
    item = SerplySearchTool._to_item(SCHOLAR_HIT, "scipy")
    assert item.authors == "Pauli Virtanen, Ralf Gommers"
    assert item.citations == 12345
    assert item.description == "SciPy is an open-source scientific computing library."


@pytest.mark.asyncio
async def test_fetch_builds_request(tool):
    session = _mock_session(200, {"results": [SEARCH_HIT]})

    items = await tool._fetch(session, "python", "search", 5)

    assert len(items) == 1
    assert items[0].url == "https://www.python.org/"
    call_args = session.get.call_args
    assert call_args[0][0] == "https://api.serply.io/v1/search/"
    assert call_args[1]["params"] == {"q": "python", "num": "5", "hl": "de", "gl": "ch"}


@pytest.mark.asyncio
async def test_fetch_news_trims_to_max_results(tool):
    """The news endpoint ignores num, so the tool cuts the entries client side."""
    session = _mock_session(200, {"entries": [NEWS_HIT] * 5})

    items = await tool._fetch(session, "python", "news", 2)

    assert len(items) == 2
    assert session.get.call_args[0][0] == "https://api.serply.io/v1/news/"


@pytest.mark.asyncio
async def test_fetch_skips_hits_without_title_or_link(tool):
    hits = [SEARCH_HIT, {"title": "no link"}, {"link": "https://example.com/no-title"}]
    session = _mock_session(200, {"results": hits})

    items = await tool._fetch(session, "python", "search", 10)

    assert [item.url for item in items] == ["https://www.python.org/"]


@pytest.mark.asyncio
async def test_fetch_raises_on_http_error(tool):
    session = _mock_session(401, {}, reason="Unauthorized")

    with pytest.raises(Exception, match="Serply search failed for 'python': 401 Unauthorized"):
        await tool._fetch(session, "python", "search", 10)


@pytest.mark.asyncio
async def test_run_async_aggregates_results(tool):
    async def fake_fetch(self, session, query, search_type, max_results):
        return [SerplySearchTool._to_item(SEARCH_HIT, query), SerplySearchTool._to_item(SCHOLAR_HIT, query)]

    with patch.object(SerplySearchTool, "_fetch", fake_fetch):
        out = await tool.run_async(SerplySearchToolInputSchema(queries=["q1", "q2"]))

    assert isinstance(out, SerplySearchToolOutputSchema)
    assert len(out.results) == 4
    assert {r.query for r in out.results} == {"q1", "q2"}


@pytest.mark.asyncio
async def test_run_async_skips_failing_query(tool):
    async def fake_fetch(self, session, query, search_type, max_results):
        if query == "bad":
            raise Exception("rate limited")
        return [SerplySearchTool._to_item(SEARCH_HIT, query)]

    with patch.object(SerplySearchTool, "_fetch", fake_fetch):
        out = await tool.run_async(SerplySearchToolInputSchema(queries=["bad", "good"]))

    assert len(out.results) == 1
    assert out.results[0].query == "good"


@pytest.mark.asyncio
async def test_run_async_sends_api_key_header(tool):
    captured = {}

    class FakeSession:
        def __init__(self, headers=None, timeout=None):
            captured["headers"] = headers

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    async def fake_fetch(self, session, query, search_type, max_results):
        return []

    with patch("tool.serply_search.aiohttp.ClientSession", FakeSession), patch.object(SerplySearchTool, "_fetch", fake_fetch):
        await tool.run_async(SerplySearchToolInputSchema(queries=["q"]))

    assert captured["headers"]["X-Api-Key"] == "test-key"
    assert "User-Agent" in captured["headers"]


@pytest.mark.asyncio
async def test_run_async_requires_api_key(monkeypatch):
    monkeypatch.delenv("SERPLY_API_KEY", raising=False)
    tool = SerplySearchTool(config=SerplySearchToolConfig())

    with pytest.raises(ValueError, match="SERPLY_API_KEY"):
        await tool.run_async(SerplySearchToolInputSchema(queries=["q"]))


def test_api_key_falls_back_to_environment(monkeypatch):
    monkeypatch.setenv("SERPLY_API_KEY", "env-key")
    tool = SerplySearchTool(config=SerplySearchToolConfig())
    assert tool.api_key == "env-key"


def test_run_invokes_run_async(tool):
    sentinel = SerplySearchToolOutputSchema(results=[])
    with patch.object(SerplySearchTool, "run_async", AsyncMock(return_value=sentinel)):
        out = tool.run(SerplySearchToolInputSchema(queries=["x"]))
    assert out is sentinel


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
