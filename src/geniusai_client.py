from typing import Any

import requests

from config import GENIUSAI_SEARCH_TIMEOUT_SECONDS, GENIUSAI_SERVER_URL


class GeniusAISearchError(Exception):
    """Raised when geniusai-server's /search endpoint cannot be reached or rejects the request."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _extract_error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"
    if isinstance(body, dict) and "error" in body:
        return str(body["error"])
    return response.text or f"HTTP {response.status_code}"


def search_photos(
    term: str = "",
    filters: dict[str, Any] | None = None,
    min_pertinence_score: float | None = None,
    limit: int | None = None,
    return_metadata: bool = False,
    uuids: list[str] | None = None,
    quality_sort: str | None = None,
    base_url: str = GENIUSAI_SERVER_URL,
    timeout: float = GENIUSAI_SEARCH_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    """Call geniusai-server's POST /search endpoint and return the list of matching photos.

    Raises GeniusAISearchError if the request fails (network error, or a 4xx/5xx
    response), carrying the server's own error message when one is available.
    """
    payload: dict[str, Any] = {"term": term}
    if filters is not None:
        payload["filters"] = filters
    if min_pertinence_score is not None:
        payload["min_pertinence_score"] = min_pertinence_score
    if limit is not None:
        payload["limit"] = limit
    if return_metadata:
        payload["return_metadata"] = True
    if uuids is not None:
        payload["uuids"] = uuids
    if quality_sort is not None:
        payload["quality_sort"] = quality_sort

    try:
        response = requests.post(f"{base_url}/search", json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise GeniusAISearchError(f"Could not reach geniusai-server at {base_url}: {exc}") from exc

    if response.status_code >= 400:
        raise GeniusAISearchError(_extract_error_message(response), status_code=response.status_code)

    return response.json()
