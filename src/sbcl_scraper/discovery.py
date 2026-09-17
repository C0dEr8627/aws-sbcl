from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup


PROFILE_PREFIX = "/community/@"


@dataclass(frozen=True, slots=True)
class Candidate:
    alias: str
    profile_url: str


def extract_candidates(html: str, base_url: str = "https://builder.aws.com") -> list[Candidate]:
    """Extract unique Builder Center public-profile links from search HTML.

    This parser deliberately accepts only the documented public profile route.
    It does not infer aliases from arbitrary text.
    """
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[Candidate] = []
    seen: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = str(link["href"])
        parsed = urlparse(href)
        path = parsed.path.rstrip("/")
        if not path.startswith(PROFILE_PREFIX):
            continue

        alias = path[len(PROFILE_PREFIX):].strip()
        if not alias or "/" in alias:
            continue

        key = alias.casefold()
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            Candidate(alias=alias, profile_url=f"{base_url.rstrip('/')}{path}")
        )

    return candidates
