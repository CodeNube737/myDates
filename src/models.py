from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class UserProfile:
    name: str
    religions: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    astronomy_interests: list[str] = field(default_factory=list)


@dataclass
class RecurringEvent:
    name: str
    month: int
    day: int
    contact_info: Optional[str] = None
    id: Optional[int] = None


@dataclass
class StoredEvent:
    source_type: str
    category: str
    name: str
    event_date: date
    is_recurring: bool
    metadata: Optional[str] = None
    id: Optional[int] = None
