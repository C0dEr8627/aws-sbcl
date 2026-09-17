from __future__ import annotations

from pathlib import Path

import typer

from .export import export_csv, export_xlsx
from .filtering import is_target
from .models import Builder
from .profile import BuilderCenterClient
from .store import BuilderStore

app = typer.Typer(help="Local AWS Builder Center scraper for SBCL workflows.")


def _print_builder(builder: Builder) -> None:
    typer.echo(f"Alias:       @{builder.alias}")
    typer.echo(f"Name:        {builder.display_name}")
    typer.echo(f"Location:    {builder.location}")
    typer.echo(f"Followers:   {builder.followers}")
    typer.echo(f"Following:   {builder.following}")
    typer.echo(f"Profile URL: {builder.profile_url}")
    typer.echo(f"Email:       {builder.email or '-'}")
    typer.echo(f"Target:      {'yes' if is_target(builder) else 'no'}")


@app.command()
def profile(
    alias: str = typer.Argument(..., help="Builder Center alias, with or without @."),
) -> None:
    """Fetch and display one public Builder Center profile."""
    try:
        with BuilderCenterClient() as client:
            builder = client.fetch_profile(alias)
    except Exception as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    _print_builder(builder)


@app.command()
def scrape(
    aliases: list[str] = typer.Argument(..., help="One or more Builder Center aliases."),
    db: Path = typer.Option(Path("data/builders.sqlite3"), "--db", help="SQLite database path."),
) -> None:
    """Fetch public profiles and save normalized records to local SQLite."""
    saved = 0
    failed = 0

    with BuilderCenterClient() as client, BuilderStore(db) as store:
        for alias in aliases:
            try:
                builder = client.fetch_profile(alias)
                store.upsert(builder)
                saved += 1
                typer.echo(f"Saved @{builder.alias} ({builder.location})")
            except Exception as exc:
                failed += 1
                typer.echo(f"Failed {alias}: {exc}", err=True)

    typer.echo(f"Scrape complete: {saved} saved, {failed} failed.")
    if failed:
        raise typer.Exit(code=1)


@app.command("list-targets")
def list_targets(
    db: Path = typer.Option(Path("data/builders.sqlite3"), "--db", help="SQLite database path."),
) -> None:
    """List stored profiles matching the SBCL target criteria."""
    with BuilderStore(db) as store:
        builders = store.list_targets()

    if not builders:
        typer.echo("No target profiles found.")
        return

    for builder in builders:
        typer.echo(f"@{builder.alias}\t{builder.display_name}\t{builder.location}")

    typer.echo(f"{len(builders)} target profile(s).")


@app.command()
def export(
    format: str = typer.Option("csv", "--format", "-f", help="Export format: csv or xlsx."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path."),
    db: Path = typer.Option(Path("data/builders.sqlite3"), "--db", help="SQLite database path."),
    all_profiles: bool = typer.Option(False, "--all", help="Export all stored profiles instead of targets only."),
) -> None:
    """Export stored target profiles to CSV or XLSX."""
    normalized_format = format.casefold()
    if normalized_format not in {"csv", "xlsx"}:
        typer.echo("Error: --format must be csv or xlsx.", err=True)
        raise typer.Exit(code=2)

    if output is None:
        output = Path("exports") / f"builders.{normalized_format}"

    with BuilderStore(db) as store:
        if all_profiles:
            # Keep the export surface intentionally small: targets are the normal
            # workflow, while --all is useful for auditing the local scrape.
            rows = _all_builders(store)
        else:
            rows = store.list_targets()

    path = export_csv(rows, output) if normalized_format == "csv" else export_xlsx(rows, output)
    typer.echo(f"Exported {len(rows)} profile(s) to {path}")


def _all_builders(store: BuilderStore) -> list[Builder]:
    # The store intentionally exposes target selection as its public query API.
    # For --all, query through the existing SQLite connection without expanding
    # the store's public surface just for the CLI.
    rows = store._connection.execute("SELECT * FROM builders ORDER BY lower(alias)").fetchall()
    return [Builder(**dict(row)) for row in rows]


if __name__ == "__main__":
    app()
