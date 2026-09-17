from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import quote

import httpx


BASE_URL = "https://builder.aws.com"


@dataclass(slots=True)
class BuilderCenterClient:
    """Small HTTP client for publicly accessible Builder Center pages."""

    base_url: str = BASE_URL
    timeout: float = 15.0
    user_agent: str = "aws-sbcl-scraper/0.1"
    _client: httpx.Client = field(init=False, repr=False)

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

    def get_html(self, url: str) -> str:
        """Fetch a public Builder Center page by absolute URL."""
        response = self._client.get(url)
        response.raise_for_status()
        return response.text

    def get_profile_html(self, alias: str) -> str:
        alias = alias.strip().lstrip("@")
        if not alias:
            raise ValueError("alias must not be empty")
        response = self._client.get(f"/community/@{quote(alias, safe='')}")
        response.raise_for_status()
        return response.text

    def fetch_profile(self, alias: str):
        """Fetch and normalize one public Builder Center profile."""
        from .models import Builder
        from .profile_parser import parse_profile_html

        normalized_alias = alias.strip().lstrip("@")
        if not normalized_alias:
            raise ValueError("alias must not be empty")

        profile_url = f"{self.base_url.rstrip('/')}/community/@{quote(normalized_alias, safe='._-')}"
        html = self.get_profile_html(normalized_alias)
        data = parse_profile_html(html, profile_url)

        required = ("alias", "display_name", "location", "followers", "following", "profile_url")
        missing = [field for field in required if data.get(field) in (None, "")]
        if missing:
            raise ValueError(f"missing profile fields: {', '.join(missing)}")

        return Builder(
            alias=str(data["alias"]),
            display_name=str(data["display_name"]),
            location=str(data["location"]),
            followers=int(data["followers"]),
            following=int(data["following"]),
            profile_url=str(data["profile_url"]),
            email=str(data["email"]) if data.get("email") else None,
            scraped_at=datetime.now(timezone.utc).isoformat(),
        )
