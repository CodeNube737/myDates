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
        for delete_sql, insert_sql, values in (
            (
                'DELETE FROM profile_religions WHERE profile_id = 1',
                'INSERT INTO profile_religions (profile_id, religion) VALUES (1, ?)',
                profile.religions,
            ),
            (
                'DELETE FROM profile_countries WHERE profile_id = 1',
                'INSERT INTO profile_countries (profile_id, country) VALUES (1, ?)',
                profile.countries,
            ),
            (
                'DELETE FROM profile_astronomy_interests WHERE profile_id = 1',
                'INSERT INTO profile_astronomy_interests (profile_id, interest) VALUES (1, ?)',
                profile.astronomy_interests,
            ),
        ):
            connection.execute(delete_sql)
            connection.executemany(
                insert_sql,
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
