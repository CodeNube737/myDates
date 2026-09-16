from __future__ import annotations

from datetime import date
from pathlib import Path

from src.db import get_connection, init_db
from src.models import RecurringEvent, StoredEvent


def add_recurring_event(
    name: str,
    month: int,
    day: int,
    contact_info: str | None = None,
    db_path: str | Path | None = None,
) -> RecurringEvent:
    init_db(db_path)
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            'INSERT INTO recurring_events (name, month, day, contact_info) VALUES (?, ?, ?, ?)',
            (name.strip(), month, day, (contact_info or '').strip() or None),
        )
        connection.commit()
        event_id = cursor.lastrowid
    return RecurringEvent(id=event_id, name=name.strip(), month=month, day=day, contact_info=(contact_info or '').strip() or None)


def list_recurring_events(db_path: str | Path | None = None) -> list[RecurringEvent]:
    init_db(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            'SELECT id, name, month, day, contact_info FROM recurring_events ORDER BY month, day, name'
        ).fetchall()
    return [
        RecurringEvent(
            id=row['id'],
            name=row['name'],
            month=row['month'],
            day=row['day'],
            contact_info=row['contact_info'],
        )
        for row in rows
    ]


def update_recurring_event(
    event_id: int,
    *,
    name: str,
    month: int,
    day: int,
    contact_info: str | None = None,
    db_path: str | Path | None = None,
) -> None:
    init_db(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            'UPDATE recurring_events SET name = ?, month = ?, day = ?, contact_info = ? WHERE id = ?',
            (name.strip(), month, day, (contact_info or '').strip() or None, event_id),
        )
        connection.commit()


def delete_recurring_event(event_id: int, db_path: str | Path | None = None) -> None:
    init_db(db_path)
    with get_connection(db_path) as connection:
        connection.execute('DELETE FROM recurring_events WHERE id = ?', (event_id,))
        connection.commit()


def build_occurrences(
    start_date: date,
    end_date: date,
    db_path: str | Path | None = None,
) -> list[StoredEvent]:
    occurrences: list[StoredEvent] = []
    for event in list_recurring_events(db_path):
        for year in range(start_date.year, end_date.year + 1):
            try:
                event_date = date(year, event.month, event.day)
            except ValueError:
                continue
            if start_date <= event_date <= end_date:
                label = f'Birthday: {event.name}' if event.contact_info else event.name
                occurrences.append(
                    StoredEvent(
                        source_type='recurring',
                        category='manual',
                        name=label,
                        event_date=event_date,
                        is_recurring=True,
                        metadata=event.contact_info,
                    )
                )
    return sorted(occurrences, key=lambda item: (item.event_date, item.name))
