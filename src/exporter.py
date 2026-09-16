from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from src.events import build_occurrences
from src.scraper import list_scraped_events
from src.utils import EXPORT_DIR, format_full_date


def gather_export_events(
    *,
    today: date | None = None,
    db_path: str | Path | None = None,
) -> list[list[str]]:
    today = today or date.today()
    # The product requirement is an export window from today through December 31
    # of the next calendar year, even when that spans almost two full years.
    end_date = date(today.year + 1, 12, 31)
    all_events = [
        *build_occurrences(today, end_date, db_path),
        *list_scraped_events(db_path, start_date=today, end_date=end_date),
    ]
    all_events.sort(key=lambda item: (item.event_date, item.name))
    rows: list[list[str]] = []
    for event in all_events:
        _, iso_week, _ = event.event_date.isocalendar()
        rows.append([
            '',
            'TRUE' if event.is_recurring else 'FALSE',
            str(event.event_date.year),
            str(iso_week),
            'D',
            format_full_date(event.event_date),
            '',
            event.name,
            "DIDN'T START",
            '',
        ])
    return rows


def export_events(
    *,
    today: date | None = None,
    db_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> Path:
    today = today or date.today()
    if output_dir:
        export_dir = Path(output_dir)
    else:
        export_dir = EXPORT_DIR
    export_dir.mkdir(parents=True, exist_ok=True)
    output_path = export_dir / f'calendar_{today.isoformat()}.csv'
    rows = gather_export_events(today=today, db_path=db_path)
    with output_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
    return output_path
