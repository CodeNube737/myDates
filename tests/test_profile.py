from pathlib import Path

from src.models import UserProfile
from src.profile import get_profile, save_profile


def test_save_and_get_profile_round_trip(tmp_path: Path) -> None:
    db_path = tmp_path / 'calendarEvents.db'
    saved = save_profile(
        UserProfile(
            name='Alex',
            religions=['Christianity', 'Islam', 'Islam'],
            countries=['US', 'CA'],
            astronomy_interests=['full moon', 'meteor showers'],
        ),
        db_path,
    )

    loaded = get_profile(db_path)

    assert saved.name == 'Alex'
    assert loaded is not None
    assert loaded.name == 'Alex'
    assert loaded.religions == ['Christianity', 'Islam']
    assert loaded.countries == ['CA', 'US']
    assert loaded.astronomy_interests == ['full moon', 'meteor showers']
