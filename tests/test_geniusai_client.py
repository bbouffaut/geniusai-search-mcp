import pytest

import geniusai_client


class _FakeResponse:
    def __init__(self, status_code, json_body=None, text_body=""):
        self.status_code = status_code
        self._json_body = json_body
        self.text = text_body

    def json(self):
        if self._json_body is None:
            raise ValueError("no json body")
        return self._json_body


def test_search_photos_sends_expected_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse(200, json_body=[{"uuid": "abc", "filename": "a.jpg"}])

    monkeypatch.setattr(geniusai_client.requests, "post", fake_post)

    results = geniusai_client.search_photos(
        term="sunset over lake",
        filters={"camera_make": "Fujifilm"},
        min_pertinence_score=0.4,
        limit=50,
        return_metadata=True,
        base_url="http://127.0.0.1:19819",
        timeout=5,
    )

    assert results == [{"uuid": "abc", "filename": "a.jpg"}]
    assert captured["url"] == "http://127.0.0.1:19819/search"
    assert captured["json"] == {
        "term": "sunset over lake",
        "filters": {"camera_make": "Fujifilm"},
        "min_pertinence_score": 0.4,
        "limit": 50,
        "return_metadata": True,
    }
    assert captured["timeout"] == 5


def test_search_photos_omits_unset_optional_fields(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["json"] = json
        return _FakeResponse(200, json_body=[])

    monkeypatch.setattr(geniusai_client.requests, "post", fake_post)

    geniusai_client.search_photos(term="lake", base_url="http://127.0.0.1:19819", timeout=5)

    assert captured["json"] == {"term": "lake"}


def test_search_photos_raises_on_error_response(monkeypatch):
    def fake_post(url, json, timeout):
        return _FakeResponse(400, json_body={"error": "Provide a search term, explicit filters, or both"})

    monkeypatch.setattr(geniusai_client.requests, "post", fake_post)

    with pytest.raises(geniusai_client.GeniusAISearchError) as exc_info:
        geniusai_client.search_photos(term="", base_url="http://127.0.0.1:19819", timeout=5)

    assert "Provide a search term" in str(exc_info.value)
    assert exc_info.value.status_code == 400


def test_search_photos_raises_on_connection_error(monkeypatch):
    def fake_post(url, json, timeout):
        raise geniusai_client.requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(geniusai_client.requests, "post", fake_post)

    with pytest.raises(geniusai_client.GeniusAISearchError):
        geniusai_client.search_photos(term="lake", base_url="http://127.0.0.1:19819", timeout=5)


def test_ping_succeeds_on_pong(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return _FakeResponse(200, text_body="pong")

    monkeypatch.setattr(geniusai_client.requests, "get", fake_get)

    geniusai_client.ping(base_url="http://127.0.0.1:19819", timeout=2)

    assert captured["url"] == "http://127.0.0.1:19819/ping"
    assert captured["timeout"] == 2


def test_ping_raises_on_unexpected_body(monkeypatch):
    def fake_get(url, timeout):
        return _FakeResponse(200, text_body="not pong")

    monkeypatch.setattr(geniusai_client.requests, "get", fake_get)

    with pytest.raises(geniusai_client.GeniusAISearchError):
        geniusai_client.ping(base_url="http://127.0.0.1:19819", timeout=2)


def test_ping_raises_on_connection_error(monkeypatch):
    def fake_get(url, timeout):
        raise geniusai_client.requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(geniusai_client.requests, "get", fake_get)

    with pytest.raises(geniusai_client.GeniusAISearchError):
        geniusai_client.ping(base_url="http://127.0.0.1:19819", timeout=2)
