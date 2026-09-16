from datetime import date
from pathlib import Path

from src.models import UserProfile
from src.scraper import list_scraped_events, refresh_events_for_profile, scrape_religious_events


def test_scrape_religious_events_includes_christian_holidays() -> None:
    events = scrape_religious_events(['Christianity'], 2026, 2026)
    names = {event.name for event in events}

    assert 'Holiday: Christmas Day' in names
    assert 'Holiday: Easter Sunday' in names
    assert any(event.event_date == date(2026, 12, 25) for event in events)


def test_refresh_events_replaces_existing_category_data(tmp_path: Path) -> None:
    db_path = tmp_path / 'calendarEvents.db'
    profile = UserProfile(name='Alex', religions=['Christianity'], countries=[], astronomy_interests=[])

    first = refresh_events_for_profile(profile, start_year=2026, end_year=2026, db_path=db_path)
    second = refresh_events_for_profile(profile, start_year=2027, end_year=2027, db_path=db_path)
    stored = list_scraped_events(db_path)

    assert first
    assert second
    assert stored
    assert all(event.event_date.year == 2027 for event in stored)


def test_scrape_religious_events_includes_jewish_holidays_when_supported() -> None:
    events = scrape_religious_events(['Judaism'], 2026, 2026)

    assert any(event.name == 'Holiday: Rosh Hashanah' for event in events)
