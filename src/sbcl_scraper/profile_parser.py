from __future__ import annotations

import re
from html import unescape

from bs4 import BeautifulSoup


PROFILE_PATH_RE = re.compile(r"/community/@([A-Za-z0-9_.-]+)")
COUNT_RE = re.compile(r"([0-9][0-9,]*)")


def _clean(value: str) -> str:
    return " ".join(unescape(value).split())


def _find_count(text: str, label: str) -> int | None:
    pattern = re.compile(rf"{re.escape(label)}\s*([0-9][0-9,]*)", re.I)
    match = pattern.search(text)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def parse_profile_html(html: str, profile_url: str) -> dict[str, object | None]:
    """Extract public profile fields when they are present in rendered HTML."""
    soup = BeautifulSoup(html, "html.parser")
    text = _clean(soup.get_text(" ", strip=True))

    alias = None
    match = PROFILE_PATH_RE.search(profile_url)
    if match:
        alias = match.group(1)

    display_name = None
    if soup.title:
        title = _clean(soup.title.get_text(" ", strip=True))
        if title:
            display_name = title.split(" | ", 1)[0].strip()

    location = None
    for node in soup.find_all(string=re.compile(r"\bIndia\b", re.I)):
        candidate = _clean(str(node.parent.get_text(" ", strip=True))) if node.parent else _clean(str(node))
        if "," in candidate and len(candidate) < 160:
            location = candidate
            break

    followers = _find_count(text, "followers")
    following = _find_count(text, "following")

    email = None
    for link in soup.select('a[href^="mailto:"]'):
        href = link.get("href", "")
        email = href[7:].split("?", 1)[0].strip() or None
        if email:
            break

    return {
        "alias": alias,
        "display_name": display_name,
        "location": location,
        "followers": followers,
        "following": following,
        "profile_url": profile_url,
        "email": email,
    }
