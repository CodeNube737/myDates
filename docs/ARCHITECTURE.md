# Architecture

The application mirrors the requested modular CLI structure:

- `calendarEvents.py` provides the single CLI entrypoint.
- `src/app.py` contains the rich-based menu dispatcher and short-lived in-memory session state.
- `src/db.py` initializes SQLite schema in `data/calendarEvents.db`.
- `src/profile.py`, `src/events.py`, and `src/scraper.py` isolate domain logic.
- `src/exporter.py` is responsible for the CSV format and export window.
