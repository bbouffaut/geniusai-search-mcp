import os

GENIUSAI_SERVER_URL = os.environ.get("GENIUSAI_SERVER_URL", "http://127.0.0.1:19819").rstrip("/")
GENIUSAI_SEARCH_TIMEOUT_SECONDS = float(os.environ.get("GENIUSAI_SEARCH_TIMEOUT_SECONDS", "30"))
