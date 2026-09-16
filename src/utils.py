from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
EXPORT_DIR = DATA_DIR / 'exports'
DB_PATH = DATA_DIR / 'calendarEvents.db'


def ensure_runtime_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)


def unique_clean(values: list[str] | tuple[str, ...]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return cleaned


def parse_multi_value_input(raw: str) -> list[str]:
    return unique_clean(raw.split(',')) if raw else []


def parse_month_day(raw: str) -> tuple[int, int]:
    month_text, day_text = [piece.strip() for piece in raw.split('/', 1)]
    return int(month_text), int(day_text)


def format_month_day(month: int, day: int) -> str:
    return f'{month:02d}/{day:02d}'


def format_full_date(value: date) -> str:
    return f"{value.strftime('%A, %B')} {value.day}, {value.year}"


def parse_iso_date(raw: str) -> date:
    return datetime.strptime(raw, '%Y-%m-%d').date()
