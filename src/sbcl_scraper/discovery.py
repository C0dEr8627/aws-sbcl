from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup


BASE_URL = "https://builder.aws.com"
PROFILE_PREFIX = "/community/@"
_PROFILE_ROUTE_RE = re.compile(
    r"(?:https?://builder\.aws\.com)?/community/(?:%40|@)([A-Za-z0-9._-]+)",
    re.IGNORECASE,
)
_ALIAS_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True, slots=True)
class Candidate:
    alias: str
    profile_url: str


def _candidate_from_alias(alias: str, base_url: str) -> Candidate | None:
    alias = unquote(alias).strip().lstrip("@")
    if not alias or not _ALIAS_RE.fullmatch(alias):
        return None
    return Candidate(
        alias=alias,
        profile_url=f"{base_url.rstrip('/')}/community/@{alias}",
    )


def extract_candidates(html: str, base_url: str = BASE_URL) -> list[Candidate]:
    """Extract public Builder Center profile links from a source page.

    Builder Center directory pages can render profile cards from embedded page
    data rather than ordinary ``<a href>`` elements. We therefore inspect both
    anchor attributes and the raw/HTML-decoded page text. Only the public
    ``/community/@alias`` route is accepted; aliases are never inferred from
    display names or other arbitrary text.
    """
    candidates: list[Candidate] = []
    seen: set[str] = set()

    def add(alias: str) -> None:
        candidate = _candidate_from_alias(alias, base_url)
        if candidate is None:
            return
        key = candidate.alias.casefold()
        if key in seen:
            return
        seen.add(key)
        candidates.append(candidate)

    soup = BeautifulSoup(html, "html.parser")

    # First collect normal links. This remains the cheapest and most precise
    # discovery path when a page renders profile anchors directly.
    for link in soup.find_all("a", href=True):
        href = html_lib.unescape(str(link["href"]))
        parsed = urlparse(href)
        path = unquote(parsed.path).rstrip("/")
        if path.casefold().startswith(PROFILE_PREFIX):
            add(path[len(PROFILE_PREFIX):])

    # Next inspect the complete response. React/Next-style pages frequently
    # keep profile URLs in serialized state or escaped strings rather than in
    # visible anchor elements. Decode common JSON/HTML escaping before matching.
    raw_variants = (
        html,
        html_lib.unescape(html),
        html.replace("\\/", "/"),
        html_lib.unescape(html).replace("\\/", "/"),
    )
    for variant in raw_variants:
        for match in _PROFILE_ROUTE_RE.finditer(variant):
            add(match.group(1))

    return candidates
