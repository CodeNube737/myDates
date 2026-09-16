from __future__ import annotations

from datetime import date

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:  # pragma: no cover
    Console = None
    Table = None

from src.db import init_db
from src.events import add_recurring_event, delete_recurring_event, list_recurring_events, update_recurring_event
from src.exporter import export_events, gather_export_events
from src.models import UserProfile
from src.profile import get_profile, save_profile
from src.scraper import refresh_events_for_profile
from src.utils import format_month_day, parse_month_day, parse_multi_value_input

console = Console() if Console else None


def _print(message: str) -> None:
    if console:
        console.print(message)
    else:  # pragma: no cover
        print(message)


def _input(prompt: str) -> str:
    return input(prompt).strip()


def _input_int(prompt: str) -> int | None:
    raw = _input(prompt)
    try:
        return int(raw)
    except ValueError:
        _print('Please enter a number.')
        return None


def configure_profile() -> None:
    existing = get_profile()
    _print('\nProfile setup')
    name = _input(f'Name [{existing.name if existing else ""}]: ') or (existing.name if existing else '')
    religions = _input(
        'Religions (comma separated; Christianity, Islam, Hinduism, Buddhism, Judaism) '
        f'[{", ".join(existing.religions) if existing else ""}]: '
    )
    countries = _input(f'Countries [{", ".join(existing.countries) if existing else ""}]: ')
    interests = _input(f'Astronomy interests [{", ".join(existing.astronomy_interests) if existing else ""}]: ')
    profile = UserProfile(
        name=name,
        religions=parse_multi_value_input(religions) if religions else (existing.religions if existing else []),
        countries=parse_multi_value_input(countries) if countries else (existing.countries if existing else []),
        astronomy_interests=parse_multi_value_input(interests) if interests else (existing.astronomy_interests if existing else []),
    )
    save_profile(profile)
    _print('[green]Profile saved.[/green]' if console else 'Profile saved.')


def manage_recurring_events() -> None:
    while True:
        _print('\nRecurring events: [1] list [2] add [3] edit [4] delete [0] back')
        choice = _input('Choose: ')
        if choice == '1':
            events = list_recurring_events()
            if not events:
                _print('No recurring events saved.')
                continue
            if Table and console:
                table = Table(title='Recurring Events')
                table.add_column('ID')
                table.add_column('Date')
                table.add_column('Name')
                table.add_column('Contact')
                for event in events:
                    table.add_row(str(event.id), format_month_day(event.month, event.day), event.name, event.contact_info or '')
                console.print(table)
            else:  # pragma: no cover
                for event in events:
                    print(event)
        elif choice == '2':
            name = _input('Event name: ')
            event_type = _input('Event type (birthday/anniversary/custom): ') or 'custom'
            try:
                month, day = parse_month_day(_input('Month/Day (MM/DD): '))
            except ValueError:
                _print('Please enter the date as MM/DD.')
                continue
            contact = _input('Contact info (optional): ')
            add_recurring_event(name, event_type, month, day, contact_info=contact or None)
            _print('Recurring event added.')
        elif choice == '3':
            event_id = _input_int('Event ID to edit: ')
            if event_id is None:
                continue
            name = _input('Updated event name: ')
            event_type = _input('Updated event type (birthday/anniversary/custom): ') or 'custom'
            try:
                month, day = parse_month_day(_input('Updated Month/Day (MM/DD): '))
            except ValueError:
                _print('Please enter the date as MM/DD.')
                continue
            contact = _input('Updated contact info (optional): ')
            update_recurring_event(
                event_id,
                name=name,
                event_type=event_type,
                month=month,
                day=day,
                contact_info=contact or None,
            )
            _print('Recurring event updated.')
        elif choice == '4':
            event_id = _input_int('Event ID to delete: ')
            if event_id is None:
                continue
            delete_recurring_event(event_id)
            _print('Recurring event deleted.')
        elif choice == '0':
            return
        else:
            _print('Invalid choice.')


def refresh_scraped_events() -> None:
    profile = get_profile()
    if profile is None:
        _print('Create a profile first.')
        return
    events = refresh_events_for_profile(profile)
    _print(f'Refreshed {len(events)} scraped events.')


def preview_upcoming_events() -> None:
    rows = gather_export_events(today=date.today())[:10]
    if not rows:
        _print('No events available to preview.')
        return
    if Table and console:
        table = Table(title='Upcoming Export Rows')
        table.add_column('Select')
        table.add_column('Year')
        table.add_column('Week#')
        table.add_column('Date')
        table.add_column('Event Name')
        for row in rows:
            table.add_row(row[1], row[2], row[3], row[5], row[7])
        console.print(table)
    else:  # pragma: no cover
        for row in rows:
            print(row)


def run_export() -> None:
    output_path = export_events(today=date.today())
    _print(f'CSV exported to {output_path}')


def main() -> int:
    init_db()
    running = True
    while running:
        _print('\nCalendar Events Tracker')
        _print('[1] Profile  [2] Recurring events  [3] Refresh scraped events  [4] Export CSV  [5] Preview export  [0] Exit')
        choice = _input('Choose: ')
        if choice == '1':
            configure_profile()
        elif choice == '2':
            manage_recurring_events()
        elif choice == '3':
            refresh_scraped_events()
        elif choice == '4':
            run_export()
        elif choice == '5':
            preview_upcoming_events()
        elif choice == '0':
            running = False
        else:
            _print('Invalid choice.')
    return 0
