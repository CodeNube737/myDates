# TDD Guide

The test suite follows the application module boundaries:

- `test_db.py` validates schema creation.
- `test_profile.py` validates profile persistence.
- `test_events.py` validates recurring event CRUD and expansion.
- `test_scraper.py` validates representative scraping behavior and replacement semantics.
- `test_exporter.py` validates the CSV output format.
