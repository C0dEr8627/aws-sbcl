from __future__ import annotations

import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from .models import Builder

BASE_URL = "https://builder.aws.com"
_PROFILE_PATH = "/community/@{alias}"
_ALIAS_RE = re.compile(r"^@?([A-Za-z0-9._-]+)$")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_COUNT_RE = re.compile(r"^(\d[\d,]*)\s+(followers|following)$", re.IGNORECASE)


def profile_url(alias: str) -> str:
    match = _ALIAS_RE.fullmatch(alias.strip())
    if not match:
        raise ValueError(f"Invalid Builder Center alias: {alias!r}")
    return f"{BASE_URL}{_PROFILE_PATH.format(alias=quote(match.group(1), safe='._-'))}"


def _clean_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    lines: list[str] = []
    for text in soup.stripped_strings:
        value = " ".join(text.split())
        if value and value not in lines:
            lines.append(value)
    return lines


def _parse_count(lines: list[str], label: str) -> int:
    pattern = re.compile(rf"^(\d[\d,]*)\s+{label}$", re.IGNORECASE)
    for line in lines:
        match = pattern.fullmatch(line)
        if match:
            return int(match.group(1).replace(",", ""))
    raise ValueError(f"Could not find {label} count in Builder Center profile")


def _parse_location(lines: list[str], followers_index: int) -> str:
    # On the public profile, location appears in the profile header before
    # the follower/following counts. Prefer lines that explicitly end in India.
    for line in reversed(lines[:followers_index]):
        if line.casefold().endswith("india"):
            return line

    # Fallback: use the last plausible header line before the counts.
    excluded = {"follow", "unfollow", "community builder", "student builder group leader"}
    for line in reversed(lines[max(0, followers_index - 8):followers_index]):
        lower = line.casefold()
        if line.startswith("@") or lower in excluded or " since " in lower:
            continue
        if len(line) <= 100:
            return line
    raise ValueError("Could not find location in Builder Center profile")


def parse_profile_html(html: str, requested_alias: str) -> Builder:
    lines = _clean_lines(html)
    alias_match = _ALIAS_RE.fullmatch(requested_alias.strip())
    if not alias_match:
        raise ValueError(f"Invalid Builder Center alias: {requested_alias!r}")
    alias = alias_match.group(1)

    at_alias = f"@{alias}"
    if at_alias.casefold() not in {line.casefold() for line in lines}:
        raise ValueError(f"Profile alias @{alias} was not found in page")

    try:
        alias_index = next(i for i, line in enumerate(lines) if line.casefold() == at_alias.casefold())
    except StopIteration as exc:
        raise ValueError(f"Profile alias @{alias} was not found in page") from exc

    display_name = next(
        (line for line in lines[:alias_index] if line and not line.startswith("Image")),
        alias,
    )
    followers = _parse_count(lines, "followers")
    following = _parse_count(lines, "following")
    followers_index = next(
        i for i, line in enumerate(lines) if _COUNT_RE.fullmatch(line) and line.casefold().endswith("followers")
    )
    location = _parse_location(lines, followers_index)
    email_match = _EMAIL_RE.search("\n".join(lines))

    return Builder(
        alias=alias,
        display_name=display_name,
        location=location,
        followers=followers,
        following=following,
        profile_url=profile_url(alias),
        email=email_match.group(0) if email_match else None,
    )


class BuilderCenterClient:
    """Small public-profile client; authentication is intentionally unsupported."""

    def __init__(self, timeout: float = 20.0) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "aws-sbcl-scraper/0.1"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BuilderCenterClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def fetch_profile(self, alias: str) -> Builder:
        response = self._client.get(profile_url(alias))
        response.raise_for_status()
        return parse_profile_html(response.text, alias)
