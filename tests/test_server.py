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


def test_ensure_geniusai_server_available_succeeds_on_first_ping(monkeypatch):
    calls = {"count": 0}

    def fake_ping(*args, **kwargs):
        calls["count"] += 1

    monkeypatch.setattr(server, "_ping", fake_ping)

    server._ensure_geniusai_server_available()

    assert calls["count"] == 1


def test_ensure_geniusai_server_available_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(server, "GENIUSAI_STARTUP_PING_RETRIES", 3)
    monkeypatch.setattr(server, "GENIUSAI_STARTUP_PING_INTERVAL_SECONDS", 0)
    sleeps = []
    monkeypatch.setattr(server.time, "sleep", lambda s: sleeps.append(s))

    calls = {"count": 0}

    def fake_ping(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            raise geniusai_client.GeniusAISearchError("not up yet")

    monkeypatch.setattr(server, "_ping", fake_ping)

    server._ensure_geniusai_server_available()

    assert calls["count"] == 3
    assert len(sleeps) == 2


def test_ensure_geniusai_server_available_exits_after_exhausting_retries(monkeypatch, capsys):
    monkeypatch.setattr(server, "GENIUSAI_STARTUP_PING_RETRIES", 2)
    monkeypatch.setattr(server, "GENIUSAI_STARTUP_PING_INTERVAL_SECONDS", 0)

    def fake_ping(*args, **kwargs):
        raise geniusai_client.GeniusAISearchError("Could not reach geniusai-server")

    monkeypatch.setattr(server, "_ping", fake_ping)

    with pytest.raises(SystemExit) as exc_info:
        server._ensure_geniusai_server_available()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not reachable" in captured.err
    assert "Could not reach geniusai-server" in captured.err


def test_main_serves_http_when_geniusai_server_is_up(monkeypatch):
    monkeypatch.setattr(server, "_ping", lambda *a, **k: None)

    run_calls = []
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: run_calls.append(kwargs))

    server.main()

    assert run_calls == [
        {"transport": "http", "host": server.MCP_SERVER_HOST, "port": server.MCP_SERVER_PORT}
    ]


def test_main_never_starts_http_server_when_geniusai_server_is_down(monkeypatch):
    monkeypatch.setattr(server, "GENIUSAI_STARTUP_PING_RETRIES", 1)

    def fake_ping(*args, **kwargs):
        raise geniusai_client.GeniusAISearchError("down")

    monkeypatch.setattr(server, "_ping", fake_ping)

    run_calls = []
    monkeypatch.setattr(server.mcp, "run", lambda **kwargs: run_calls.append(kwargs))

    with pytest.raises(SystemExit):
        server.main()

    assert run_calls == []


def test_main_exits_quietly_on_keyboard_interrupt(monkeypatch):
    monkeypatch.setattr(server, "_ping", lambda *a, **k: None)

    def fake_run(**kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(server.mcp, "run", fake_run)

    server.main()  # must not raise
