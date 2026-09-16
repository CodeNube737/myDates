# API Overview

## Core modules
- `src.profile.save_profile(profile)` stores the single local profile.
- `src.events.add_recurring_event(...)` manages annual manual events.
- `src.scraper.refresh_events_for_profile(...)` refreshes scraped records for the configured profile.
- `src.exporter.export_events(...)` writes the required CSV file.
