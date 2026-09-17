from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path

from openpyxl import Workbook

from .models import Builder


FIELDS = [
    "alias",
    "display_name",
    "location",
    "followers",
    "following",
    "profile_url",
    "email",
    "scraped_at",
]


def _rows(builders: list[Builder]) -> list[dict[str, object]]:
    return [asdict(builder) for builder in builders]


def export_csv(builders: list[Builder], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(_rows(builders))

    return path


def export_xlsx(builders: list[Builder], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Builders"
    worksheet.append(FIELDS)

    for row in _rows(builders):
        worksheet.append([row[field] for field in FIELDS])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    for column_cells in worksheet.columns:
        width = max(len(str(cell.value or "")) for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(width + 2, 60)

    workbook.save(path)
    return path
