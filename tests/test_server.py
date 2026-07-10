import asyncio

import pytest
from fastmcp import Client

import geniusai_client
import server


def _run(coro):
    return asyncio.run(coro)


def test_search_photos_tool_returns_results(monkeypatch):
    def fake_search_photos(**kwargs):
        assert kwargs["term"] == "sunset over lake"
        return [{"uuid": "abc", "filename": "a.jpg", "pertinence_score": 0.9}]

    monkeypatch.setattr(server, "_search_photos", fake_search_photos)

    async def scenario():
        async with Client(server.mcp) as client:
            result = await client.call_tool("search_photos", {"query": "sunset over lake"})
            return result

    result = _run(scenario())
    assert result.data == [{"uuid": "abc", "filename": "a.jpg", "pertinence_score": 0.9}]


def test_search_photos_tool_surfaces_server_error(monkeypatch):
    def fake_search_photos(**kwargs):
        raise geniusai_client.GeniusAISearchError(
            "Provide a search term, explicit filters, or both", status_code=400
        )

    monkeypatch.setattr(server, "_search_photos", fake_search_photos)

    async def scenario():
        async with Client(server.mcp) as client:
            with pytest.raises(Exception) as exc_info:
                await client.call_tool("search_photos", {"query": ""})
            return exc_info

    exc_info = _run(scenario())
    assert "Provide a search term" in str(exc_info.value)
