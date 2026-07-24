import sys
import time
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from config import (
    GENIUSAI_SERVER_URL,
    GENIUSAI_STARTUP_PING_INTERVAL_SECONDS,
    GENIUSAI_STARTUP_PING_RETRIES,
    MCP_SERVER_HOST,
    MCP_SERVER_PORT,
)
from geniusai_client import GeniusAISearchError
from geniusai_client import ping as _ping
from geniusai_client import search_photos as _search_photos

mcp = FastMCP("geniusai-search")


def _ensure_geniusai_server_available() -> None:
    """Poll geniusai-server's /ping endpoint before starting; exit if it's not up.

    The MCP server is useless without geniusai-server, so this fails fast at
    startup with a clear message instead of only failing on the first search.
    """
    attempts = max(1, GENIUSAI_STARTUP_PING_RETRIES)
    last_error: GeniusAISearchError | None = None

    for attempt in range(1, attempts + 1):
        try:
            _ping()
            return
        except GeniusAISearchError as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(GENIUSAI_STARTUP_PING_INTERVAL_SECONDS)

    print(
        f"error: geniusai-server is not reachable at {GENIUSAI_SERVER_URL} "
        f"after {attempts} attempt(s): {last_error}",
        file=sys.stderr,
    )
    print(
        "Start geniusai-server first, or set GENIUSAI_SERVER_URL to point at "
        "the correct host/port.",
        file=sys.stderr,
    )
    sys.exit(1)


@mcp.tool
def search_photos(
    query: str = "",
    filters: dict[str, Any] | None = None,
    min_pertinence_score: float | None = None,
    limit: int | None = None,
    return_metadata: bool = False,
    uuids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search indexed Lightroom photos via geniusai-server's semantic/metadata search.

    Provide a free-text `query`, structured `filters`, or both — geniusai-server
    requires at least one of them to be non-empty.

    `filters` supports keys such as capture_time, aperture_f_number, iso,
    focal_length_mm, focal_length_35mm, shutter_speed, exposure_bias, camera_make,
    camera_model, and lens. Each may be a scalar or an object with gte/gt/lte/lt/eq
    operators, e.g. {"aperture_f_number": {"lte": 2.8}, "camera_make": "Fujifilm"}.

    Args:
        query: Free-text semantic search term (e.g. "sunset over lake").
        filters: Structured filters dict, e.g. {"capture_time": "2026-05"}.
        min_pertinence_score: Minimum relevance score (0-1) to keep a match.
            Defaults to geniusai-server's own default (0.35) when omitted.
        limit: Maximum number of results to return (1-10000). Defaults to
            geniusai-server's own default (300) when omitted.
        return_metadata: If true, include each photo's full stored metadata payload.
        uuids: Optional list of photo UUIDs to restrict/re-score the search to.

    Returns:
        A list of photo matches, each with uuid, filename, capture_time, match_type
        ("semantic", "semantic+metadata", or "metadata"), pertinence_score, distance,
        ai_model, and ai_rundate — plus metadata when return_metadata is true.
    """
    try:
        return _search_photos(
            term=query,
            filters=filters,
            min_pertinence_score=min_pertinence_score,
            limit=limit,
            return_metadata=return_metadata,
            uuids=uuids,
        )
    except GeniusAISearchError as exc:
        raise ToolError(str(exc)) from exc


def main() -> None:
    _ensure_geniusai_server_available()
    try:
        mcp.run(transport="http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
