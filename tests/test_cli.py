from typer.testing import CliRunner

from sbcl_scraper.cli import app
from sbcl_scraper.models import Builder
from sbcl_scraper.store import BuilderStore


runner = CliRunner()


def make_builder(alias: str, location: str = "Maharashtra, India", followers: int = 0, following: int = 0) -> Builder:
    return Builder(
        alias=alias,
        display_name=alias.title(),
        location=location,
        followers=followers,
        following=following,
        profile_url=f"https://builder.aws.com/community/@{alias}",
        email=None,
        scraped_at="2026-09-18T00:00:00+00:00",
    )


def test_help_lists_commands():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "profile" in result.stdout
    assert "scrape" in result.stdout
    assert "export" in result.stdout
    assert "list-targets" in result.stdout


def test_list_targets_uses_target_criteria(tmp_path):
    db = tmp_path / "builders.sqlite3"
    with BuilderStore(db) as store:
        store.upsert(make_builder("india-target"))
        store.upsert(make_builder("has-followers", followers=1))
        store.upsert(make_builder("non-india", location="London, UK"))

    result = runner.invoke(app, ["list-targets", "--db", str(db)])

    assert result.exit_code == 0
    assert "@india-target" in result.stdout
    assert "@has-followers" not in result.stdout
    assert "@non-india" not in result.stdout
    assert "1 target profile(s)." in result.stdout


def test_export_defaults_to_targets(tmp_path):
    db = tmp_path / "builders.sqlite3"
    output = tmp_path / "targets.csv"
    with BuilderStore(db) as store:
        store.upsert(make_builder("target"))
        store.upsert(make_builder("not-target", following=2))

    result = runner.invoke(
        app,
        ["export", "--db", str(db), "--format", "csv", "--output", str(output)],
    )

    assert result.exit_code == 0
    assert "Exported 1 profile(s)" in result.stdout
    assert "target" in output.read_text(encoding="utf-8-sig")
    assert "not-target" not in output.read_text(encoding="utf-8-sig")


def test_export_all_profiles(tmp_path):
    db = tmp_path / "builders.sqlite3"
    output = tmp_path / "all.xlsx"
    with BuilderStore(db) as store:
        store.upsert(make_builder("target"))
        store.upsert(make_builder("not-target", following=2))

    result = runner.invoke(
        app,
        ["export", "--db", str(db), "--format", "xlsx", "--output", str(output), "--all"],
    )

    assert result.exit_code == 0
    assert "Exported 2 profile(s)" in result.stdout
    assert output.exists()
