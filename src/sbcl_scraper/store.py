from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Builder


SCHEMA = """
CREATE TABLE IF NOT EXISTS builders (
    alias TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    location TEXT NOT NULL,
    followers INTEGER NOT NULL,
    following INTEGER NOT NULL,
    profile_url TEXT NOT NULL,
    email TEXT,
    scraped_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_builders_location ON builders(location);
CREATE INDEX IF NOT EXISTS idx_builders_target ON builders(followers, following);
"""


class BuilderStore:
    """Small local SQLite store for normalized public Builder profiles."""

    def __init__(self, path: str | Path = "data/builders.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(SCHEMA)
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "BuilderStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def upsert(self, builder: Builder) -> None:
        self._connection.execute(
            """
            INSERT INTO builders
                (alias, display_name, location, followers, following,
                 profile_url, email, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alias) DO UPDATE SET
                display_name=excluded.display_name,
                location=excluded.location,
                followers=excluded.followers,
                following=excluded.following,
                profile_url=excluded.profile_url,
                email=excluded.email,
                scraped_at=excluded.scraped_at
            """,
            (
                builder.alias,
                builder.display_name,
                builder.location,
                builder.followers,
                builder.following,
                builder.profile_url,
                builder.email,
                builder.scraped_at,
            ),
        )
        self._connection.commit()

    def get(self, alias: str) -> Builder | None:
        row = self._connection.execute(
            "SELECT * FROM builders WHERE alias = ?", (alias,)
        ).fetchone()
        if row is None:
            return None
        return Builder(**dict(row))

    def list_all(self) -> list[Builder]:
        rows = self._connection.execute(
            "SELECT * FROM builders ORDER BY lower(alias)"
        ).fetchall()
        return [Builder(**dict(row)) for row in rows]

    def list_targets(self) -> list[Builder]:
        return [builder for builder in self.list_all() if builder.is_target]
