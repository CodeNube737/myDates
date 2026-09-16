from datetime import date
from pathlib import Path

from src.events import add_recurring_event, build_occurrences, delete_recurring_event, list_recurring_events, update_recurring_event


def test_recurring_event_crud_and_occurrences(tmp_path: Path) -> None:
    db_path = tmp_path / 'calendarEvents.db'
    event = add_recurring_event('Jane Smith', 9, 21, contact_info='jane@example.com', db_path=db_path)

    update_recurring_event(event.id, name='Jane Smith', month=9, day=22, contact_info='friend', db_path=db_path)
    events = list_recurring_events(db_path)
    occurrences = build_occurrences(date(2026, 1, 1), date(2027, 12, 31), db_path)

    assert len(events) == 1
    assert events[0].day == 22
    assert [occurrence.event_date for occurrence in occurrences] == [date(2026, 9, 22), date(2027, 9, 22)]
    assert occurrences[0].name == 'Birthday: Jane Smith'

    delete_recurring_event(event.id, db_path)
    assert list_recurring_events(db_path) == []
