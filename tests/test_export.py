import csv

from openpyxl import load_workbook

from sbcl_scraper.export import export_csv, export_xlsx
from sbcl_scraper.models import Builder


def make_builder(alias: str = "umar") -> Builder:
    return Builder(
        alias=alias,
        display_name="Umar Ansari",
        location="Maharashtra, India",
        followers=0,
        following=0,
        profile_url=f"https://builder.aws.com/community/@{alias}",
        email=None,
        scraped_at="2026-09-18T00:00:00+00:00",
    )


def test_export_csv(tmp_path):
    output = export_csv([make_builder()], tmp_path / "builders.csv")

    with output.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {
            "alias": "umar",
            "display_name": "Umar Ansari",
            "location": "Maharashtra, India",
            "followers": "0",
            "following": "0",
            "profile_url": "https://builder.aws.com/community/@umar",
            "email": "",
            "scraped_at": "2026-09-18T00:00:00+00:00",
        }
    ]


def test_export_xlsx(tmp_path):
    output = export_xlsx([make_builder()], tmp_path / "builders.xlsx")
    workbook = load_workbook(output)
    worksheet = workbook["Builders"]

    assert list(worksheet.values) == [
        (
            "alias",
            "display_name",
            "location",
            "followers",
            "following",
            "profile_url",
            "email",
            "scraped_at",
        ),
        (
            "umar",
            "Umar Ansari",
            "Maharashtra, India",
            0,
            0,
            "https://builder.aws.com/community/@umar",
            None,
            "2026-09-18T00:00:00+00:00",
        ),
    ]
    assert worksheet.freeze_panes == "A2"
    workbook.close()
