import logging
import os
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def _build_headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logger.warning(
            "GITHUB_TOKEN is not set. Requests are unauthenticated (60 req/hour limit)."
        )
    return headers


def create_github_client() -> httpx.AsyncClient:
    """Create a configured httpx.AsyncClient for the GitHub API.

    Reads GITHUB_TOKEN from the environment at call time.
    """
    return httpx.AsyncClient(headers=_build_headers(), timeout=10.0)


async def fetch_github_profile(username: str, client: httpx.AsyncClient) -> dict[str, Any]:
    """Fetch a GitHub user profile via the REST API.

    Raises:
        httpx.HTTPStatusError: When the API returns a non-2xx response.
    """
    url = f"{GITHUB_API_BASE}/users/{quote(username, safe='')}"
    response = await client.get(url)
    response.raise_for_status()
    return response.json()
