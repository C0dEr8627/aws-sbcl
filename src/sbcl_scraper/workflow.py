from __future__ import annotations

from datetime import datetime, timezone

from .client import BuilderCenterClient
from .discovery import Candidate
from .models import Builder
from .profile_parser import parse_profile_html
from .store import BuilderStore


class ScrapeError(RuntimeError):
    """Raised when a public profile cannot be normalized into a Builder."""


def normalize_profile(data: dict[str, object | None]) -> Builder:
    """Convert parsed public profile data into a validated Builder record."""
    required = ("alias", "display_name", "location", "followers", "following", "profile_url")
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        raise ScrapeError(f"missing profile fields: {', '.join(missing)}")

    try:
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
    except (TypeError, ValueError) as exc:
        raise ScrapeError("invalid profile field type") from exc


def scrape_candidates(
    candidates: list[Candidate],
    client: BuilderCenterClient,
    store: BuilderStore,
) -> tuple[list[Builder], list[tuple[Candidate, str]]]:
    """Fetch, normalize, and persist public profiles.

    A single malformed/unavailable profile does not stop the remaining scrape.
    Errors are returned for operator visibility rather than silently discarded.
    """
    saved: list[Builder] = []
    errors: list[tuple[Candidate, str]] = []

    for candidate in candidates:
        try:
            html = client.get_profile_html(candidate.alias)
            data = parse_profile_html(html, candidate.profile_url)
            builder = normalize_profile(data)
            store.upsert(builder)
            saved.append(builder)
        except Exception as exc:
            errors.append((candidate, str(exc)))

    return saved, errors
