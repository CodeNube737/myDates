from __future__ import annotations

from pathlib import Path

from src.db import get_connection, init_db
from src.models import UserProfile
from src.utils import unique_clean


def save_profile(profile: UserProfile, db_path: str | Path | None = None) -> UserProfile:
    init_db(db_path)
    profile = UserProfile(
        name=profile.name.strip(),
        religions=unique_clean(profile.religions),
        countries=unique_clean(profile.countries),
        astronomy_interests=unique_clean(profile.astronomy_interests),
    )
    with get_connection(db_path) as connection:
        connection.execute(
            'INSERT INTO user_profile (id, name) VALUES (1, ?) '
            'ON CONFLICT(id) DO UPDATE SET name = excluded.name',
            (profile.name,),
        )
        for table, values, column in (
            ('profile_religions', profile.religions, 'religion'),
            ('profile_countries', profile.countries, 'country'),
            ('profile_astronomy_interests', profile.astronomy_interests, 'interest'),
        ):
            connection.execute(f'DELETE FROM {table} WHERE profile_id = 1')
            connection.executemany(
                f'INSERT INTO {table} (profile_id, {column}) VALUES (1, ?)',
                [(value,) for value in values],
            )
        connection.commit()
    return profile


def get_profile(db_path: str | Path | None = None) -> UserProfile | None:
    init_db(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute('SELECT name FROM user_profile WHERE id = 1').fetchone()
        if row is None:
            return None
        religions = [r['religion'] for r in connection.execute(
            'SELECT religion FROM profile_religions WHERE profile_id = 1 ORDER BY religion'
        )]
        countries = [r['country'] for r in connection.execute(
            'SELECT country FROM profile_countries WHERE profile_id = 1 ORDER BY country'
        )]
        interests = [r['interest'] for r in connection.execute(
            'SELECT interest FROM profile_astronomy_interests WHERE profile_id = 1 ORDER BY interest'
        )]
    return UserProfile(
        name=row['name'],
        religions=religions,
        countries=countries,
        astronomy_interests=interests,
    )
