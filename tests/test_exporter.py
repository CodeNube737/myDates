import csv
from datetime import date
from pathlib import Path

from src.events import add_recurring_event
from src.exporter import export_events
from src.models import UserProfile
from src.profile import save_profile
from src.scraper import refresh_events_for_profile


def test_export_events_writes_required_csv_format(tmp_path: Path) -> None:
    db_path = tmp_path / 'calendarEvents.db'
    export_dir = tmp_path / 'exports'
    add_recurring_event('Jane Smith', 'birthday', 9, 21, contact_info='friend', db_path=db_path)
    profile = UserProfile(name='Alex', religions=['Christianity'], countries=[], astronomy_interests=[])
    save_profile(profile, db_path)
    refresh_events_for_profile(profile, start_year=2026, end_year=2026, db_path=db_path)

    output = export_events(today=date(2026, 9, 15), db_path=db_path, output_dir=export_dir)

    assert output == export_dir / 'calendar_2026-09-15.csv'
    with output.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.reader(handle))

    assert rows
    birthday_row = next(row for row in rows if row[7] == 'Birthday: Jane Smith')
    christmas_row = next(row for row in rows if row[7] == 'Holiday: Christmas Day')
    assert birthday_row == ['', 'TRUE', '2026', str(date(2026, 9, 21).isocalendar().week), 'D', 'Monday, September 21, 2026', '', 'Birthday: Jane Smith', "DIDN'T START", '']
    assert christmas_row[0] == ''
    assert christmas_row[1] == 'TRUE'
    assert christmas_row[2] == '2026'
    assert christmas_row[4] == 'D'
    assert christmas_row[8] == "DIDN'T START"


def test_export_uses_non_zero_padded_day_format(tmp_path: Path) -> None:
    db_path = tmp_path / 'calendarEvents.db'
    export_dir = tmp_path / 'exports'
    add_recurring_event('Project Launch', 'custom', 9, 7, db_path=db_path)

    output = export_events(today=date(2026, 1, 1), db_path=db_path, output_dir=export_dir)

    with output.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.reader(handle))

    row = next(row for row in rows if row[7] == 'Project Launch')
    assert row[5] == 'Monday, September 7, 2026'
