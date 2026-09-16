from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import holidays as holidays_lib
except ImportError:  # pragma: no cover
    holidays_lib = None

try:
    from convertdate import hebrew
except ImportError:  # pragma: no cover
    hebrew = None

try:
    import ephem
except ImportError:  # pragma: no cover
    ephem = None

try:
    from hijri_converter import Gregorian, Hijri
except ImportError:  # pragma: no cover
    Gregorian = None
    Hijri = None

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

from src.db import get_connection, init_db
from src.models import StoredEvent, UserProfile
from src.profile import get_profile

HINDU_KEYWORDS = ('diwali', 'deepavali', 'holi', 'dussehra', 'janmashtami', 'shivaratri')
BUDDHIST_KEYWORDS = ('vesak', 'visakha', 'makha', 'asalha', 'buddha purnima')
JEWISH_DATES = {
    'Holiday: Passover': (1, 15),
    'Holiday: Rosh Hashanah': (7, 1),
    'Holiday: Yom Kippur': (7, 10),
    'Holiday: Hanukkah': (9, 25),
}
ISLAMIC_DATES = {
    'Holiday: Islamic New Year': (1, 1),
    'Holiday: Mawlid': (3, 12),
    'Holiday: Ramadan Begins': (9, 1),
    'Holiday: Eid al-Fitr': (10, 1),
    'Holiday: Eid al-Adha': (12, 10),
}


def _gregorian_easter(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day_value = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day_value)


def _event(source_type: str, category: str, name: str, event_date: date, is_recurring: bool, metadata: str | None = None) -> StoredEvent:
    return StoredEvent(
        source_type=source_type,
        category=category,
        name=name,
        event_date=event_date,
        is_recurring=is_recurring,
        metadata=metadata,
    )


def scrape_religious_events(religions: list[str], start_year: int, end_year: int) -> list[StoredEvent]:
    events: list[StoredEvent] = []
    selected = {religion.casefold(): religion for religion in religions}
    for year in range(start_year, end_year + 1):
        if 'christianity' in selected:
            easter = _gregorian_easter(year)
            events.extend([
                _event('religious', 'Christianity', 'Holiday: Good Friday', easter - timedelta(days=2), True),
                _event('religious', 'Christianity', 'Holiday: Easter Sunday', easter, True),
                _event('religious', 'Christianity', 'Holiday: Christmas Day', date(year, 12, 25), True),
            ])
        if 'islam' in selected:
            for hijri_year in _candidate_hijri_years(year):
                for name, (month, day_value) in ISLAMIC_DATES.items():
                    converted = _hijri_to_gregorian(hijri_year, month, day_value)
                    if converted and converted.year == year:
                        events.append(_event('religious', 'Islam', name, converted, True))
        if 'judaism' in selected:
            for hebrew_year in _candidate_hebrew_years(year):
                for name, (month, day_value) in JEWISH_DATES.items():
                    converted = _hebrew_to_gregorian(hebrew_year, month, day_value)
                    if converted and converted.year == year:
                        events.append(_event('religious', 'Judaism', name, converted, True))
        if 'hinduism' in selected:
            events.extend(_holiday_keyword_matches('IN', year, HINDU_KEYWORDS, 'Hinduism'))
        if 'buddhism' in selected:
            events.extend(_holiday_keyword_matches('TH', year, BUDDHIST_KEYWORDS, 'Buddhism'))
    return _dedupe_events(events)


def scrape_national_holidays(countries: list[str], start_year: int, end_year: int) -> list[StoredEvent]:
    events: list[StoredEvent] = []
    for country in countries:
        for year in range(start_year, end_year + 1):
            for event_date, name in _country_holidays(country, year):
                events.append(_event('national', country, f'National Holiday: {name}', event_date, True))
    return _dedupe_events(events)


def scrape_astronomical_events(interests: list[str], start_year: int, end_year: int) -> list[StoredEvent]:
    events: list[StoredEvent] = []
    interest_text = ' '.join(interests).casefold()
    for year in range(start_year, end_year + 1):
        if any(keyword in interest_text for keyword in ('moon', 'lunar', 'full moon', 'new moon')):
            events.extend(_moon_phase_events(year))
        if any(keyword in interest_text for keyword in ('equinox', 'solstice', 'season')):
            events.extend(_seasonal_events(year))
        if 'meteor' in interest_text:
            events.extend([
                _event('astronomy', 'meteor showers', 'Astronomy: Quadrantids Peak', date(year, 1, 3), False),
                _event('astronomy', 'meteor showers', 'Astronomy: Perseids Peak', date(year, 8, 12), False),
                _event('astronomy', 'meteor showers', 'Astronomy: Geminids Peak', date(year, 12, 14), False),
            ])
    return _dedupe_events(events)


def refresh_events_for_profile(
    profile: UserProfile | None = None,
    *,
    start_year: int | None = None,
    end_year: int | None = None,
    db_path: str | Path | None = None,
) -> list[StoredEvent]:
    init_db(db_path)
    profile = profile or get_profile(db_path)
    if profile is None:
        return []
    today = date.today()
    start_year = start_year or today.year
    end_year = end_year or (today.year + 1)
    events = [
        *scrape_religious_events(profile.religions, start_year, end_year),
        *scrape_national_holidays(profile.countries, start_year, end_year),
        *scrape_astronomical_events(profile.astronomy_interests, start_year, end_year),
    ]
    _replace_scraped_events(events, db_path)
    return sorted(events, key=lambda item: (item.event_date, item.name))


def list_scraped_events(
    db_path: str | Path | None = None,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[StoredEvent]:
    init_db(db_path)
    query = (
        'SELECT id, source_type, category, name, event_date, is_recurring, metadata '
        'FROM scraped_events WHERE 1=1'
    )
    params: list[str] = []
    if start_date:
        query += ' AND event_date >= ?'
        params.append(start_date.isoformat())
    if end_date:
        query += ' AND event_date <= ?'
        params.append(end_date.isoformat())
    query += ' ORDER BY event_date, name'
    with get_connection(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
    return [
        StoredEvent(
            id=row['id'],
            source_type=row['source_type'],
            category=row['category'],
            name=row['name'],
            event_date=datetime.strptime(row['event_date'], '%Y-%m-%d').date(),
            is_recurring=bool(row['is_recurring']),
            metadata=row['metadata'],
        )
        for row in rows
    ]


def _replace_scraped_events(events: list[StoredEvent], db_path: str | Path | None = None) -> None:
    grouped_keys = sorted({(event.source_type, event.category) for event in events})
    with get_connection(db_path) as connection:
        for source_type, category in grouped_keys:
            connection.execute(
                'DELETE FROM scraped_events WHERE source_type = ? AND category = ?',
                (source_type, category),
            )
        connection.executemany(
            'INSERT OR REPLACE INTO scraped_events '
            '(source_type, category, name, event_date, is_recurring, metadata) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            [
                (
                    event.source_type,
                    event.category,
                    event.name,
                    event.event_date.isoformat(),
                    int(event.is_recurring),
                    event.metadata,
                )
                for event in events
            ],
        )
        connection.commit()


def _holiday_keyword_matches(country: str, year: int, keywords: tuple[str, ...], category: str) -> list[StoredEvent]:
    matches: list[StoredEvent] = []
    for event_date, name in _country_holidays(country, year):
        if any(keyword in name.casefold() for keyword in keywords):
            matches.append(_event('religious', category, f'Holiday: {name}', event_date, True))
    return matches


def _country_holidays(country: str, year: int) -> list[tuple[date, str]]:
    code = country.strip()
    if holidays_lib is not None:
        try:
            holiday_map = holidays_lib.country_holidays(code, years=[year])
            return sorted((event_date, name) for event_date, name in holiday_map.items())
        except Exception:
            pass
    if requests is not None:
        try:
            response = requests.get(
                f'https://date.nager.at/api/v3/PublicHolidays/{year}/{code}',
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            return [
                (datetime.strptime(item['date'], '%Y-%m-%d').date(), item.get('localName') or item['name'])
                for item in payload
            ]
        except Exception:
            return []
    return []


def _hijri_to_gregorian(year: int, month: int, day_value: int) -> date | None:
    if Hijri is None:
        return None
    try:
        converted = Hijri(year, month, day_value).to_gregorian()
        return date(converted.year, converted.month, converted.day)
    except Exception:
        return None


def _candidate_hijri_years(year: int) -> list[int]:
    if Gregorian is not None:
        start_year = Gregorian(year, 1, 1).to_hijri().year
        end_year = Gregorian(year, 12, 31).to_hijri().year
        return sorted({start_year, end_year})
    return [year - 579, year - 578]


def _hebrew_to_gregorian(year: int, month: int, day_value: int) -> date | None:
    if hebrew is None:
        return None


def _candidate_hebrew_years(year: int) -> list[int]:
    if hebrew is not None:
        start_year = hebrew.from_gregorian(year, 1, 1)[0]
        end_year = hebrew.from_gregorian(year, 12, 31)[0]
        return sorted({start_year, end_year})
    return [year + 3760, year + 3761]
    try:
        g_year, g_month, g_day = hebrew.to_gregorian(year, month, day_value)
        return date(g_year, g_month, g_day)
    except Exception:
        return None


def _moon_phase_events(year: int) -> list[StoredEvent]:
    if ephem is None:
        return [
            _event('astronomy', 'lunar phases', 'Astronomy: Full Moon', date(year, 1, 13), False),
            _event('astronomy', 'lunar phases', 'Astronomy: New Moon', date(year, 1, 29), False),
        ]
    events: list[StoredEvent] = []
    start = ephem.Date(f'{year}/1/1')
    end = ephem.Date(f'{year + 1}/1/1')
    current = start
    while True:
        next_full = ephem.next_full_moon(current)
        if next_full >= end:
            break
        events.append(_event('astronomy', 'lunar phases', 'Astronomy: Full Moon', next_full.datetime().date(), False))
        current = ephem.Date(next_full + 1)
    current = start
    while True:
        next_new = ephem.next_new_moon(current)
        if next_new >= end:
            break
        events.append(_event('astronomy', 'lunar phases', 'Astronomy: New Moon', next_new.datetime().date(), False))
        current = ephem.Date(next_new + 1)
    return events


def _seasonal_events(year: int) -> list[StoredEvent]:
    if ephem is None:
        return [
            _event('astronomy', 'seasons', 'Astronomy: March Equinox', date(year, 3, 20), False),
            _event('astronomy', 'seasons', 'Astronomy: June Solstice', date(year, 6, 21), False),
            _event('astronomy', 'seasons', 'Astronomy: September Equinox', date(year, 9, 22), False),
            _event('astronomy', 'seasons', 'Astronomy: December Solstice', date(year, 12, 21), False),
        ]
    values = [
        ('Astronomy: March Equinox', ephem.next_equinox(f'{year}/1/1').datetime().date()),
        ('Astronomy: June Solstice', ephem.next_solstice(f'{year}/3/21').datetime().date()),
        ('Astronomy: September Equinox', ephem.next_equinox(f'{year}/6/22').datetime().date()),
        ('Astronomy: December Solstice', ephem.next_solstice(f'{year}/9/23').datetime().date()),
    ]
    return [_event('astronomy', 'seasons', name, event_date, False) for name, event_date in values]


def _dedupe_events(events: list[StoredEvent]) -> list[StoredEvent]:
    unique: dict[tuple[str, str, str, date], StoredEvent] = {}
    for event in events:
        unique[(event.source_type, event.category, event.name, event.event_date)] = event
    return sorted(unique.values(), key=lambda item: (item.event_date, item.name))
