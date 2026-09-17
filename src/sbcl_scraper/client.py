from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx


BASE_URL = "https://builder.aws.com"


@dataclass(slots=True)
class BuilderCenterClient:
    """Small HTTP client for publicly accessible Builder Center pages.

    Discovery/search transport is intentionally not hard-coded until the site's
    actual public search request has been verified. Profile pages are stable
    enough to support direct retrieval by alias.
    """

    base_url: str = BASE_URL
    timeout: float = 15.0
    user_agent: str = "aws-sbcl-scraper/0.1"

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": self.user_agent},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BuilderCenterClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_profile_html(self, alias: str) -> str:
        alias = alias.strip().lstrip("@")
        if not alias:
            raise ValueError("alias must not be empty")
        response = self._client.get(f"/community/@{quote(alias, safe='')}")
        response.raise_for_status()
        return response.text
