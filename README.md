# myDates

myDates is a local-first calendar events tracker that stores a personal profile, recurring dates, scraped holidays, and astronomy events in SQLite and exports them to a CSV format suitable for external planning tools.

## Features
- CLI entrypoint in `calendarEvents.py` that routes to `src.app.main()`
- SQLite database automatically created at `data/calendarEvents.db`
- Profile management for religions, countries, and astronomy interests
- Recurring annual event CRUD for birthdays, anniversaries, and custom dates
- On-demand scraping for religious, national, and astronomical events
- CSV export from today through the end of next year at `data/exports/calendar_YYYY-MM-DD.csv`

## Setup
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python calendarEvents.py
```

## Test
```bash
pytest tests
```

## Project structure
```
calendarEvents/
├── calendarEvents.py
├── requirements.txt
├── README.md
├── .gitignore
├── src/
│   ├── app.py
│   ├── db.py
│   ├── events.py
│   ├── exporter.py
│   ├── models.py
│   ├── profile.py
│   ├── scraper.py
│   └── utils.py
├── tests/
└── docs/
```
