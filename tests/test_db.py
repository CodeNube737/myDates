from pathlib import Path

from src.db import get_connection, init_db


def test_init_db_creates_runtime_schema(tmp_path: Path) -> None:
    db_path = tmp_path / 'data' / 'calendarEvents.db'

    created = init_db(db_path)

    assert created == db_path
    assert db_path.exists()
    with get_connection(db_path) as connection:
        tables = {
            row['name']
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {'user_profile', 'profile_religions', 'profile_countries', 'profile_astronomy_interests', 'recurring_events', 'scraped_events'} <= tables
