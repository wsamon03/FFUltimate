"""Shared fixtures for all test modules."""

import os
import uuid
from datetime import datetime

import psycopg2
import pytest
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()


def _get_db_params():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "nfl_fantasy"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "owenethanTKD"),
        "port": int(os.getenv("DB_PORT", "5432")),
    }


@pytest.fixture(scope="session")
def db_params():
    return _get_db_params()


@pytest.fixture(scope="session")
def conn(db_params):
    conn = psycopg2.connect(**db_params)
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture()
def cursor(conn):
    """Provides a RealDictCursor that closes after the test."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        yield cur


# dict_cursor fixture is no longer needed - cursor now provides dict results


@pytest.fixture(scope="session")
def test_team_id(conn, cursor):
    """Create or return a test team for use across all tests."""
    cursor.execute(
        "SELECT id FROM teams WHERE espn_id = %s",
        ("999999001",),
    )
    row = cursor.fetchone()
    if row:
        return str(row["id"])
    cursor.execute("CALL usp_upsert_team(%s, %s, %s)", ("999999001", "TEST", "Test Team"))
    cursor.execute(
        "SELECT id FROM teams WHERE espn_id = %s",
        ("999999001",),
    )
    return str(cursor.fetchone()["id"])


@pytest.fixture(scope="session")
def test_player_id(conn, cursor, test_team_id):
    """Create or return a test player for use across all tests."""
    test_pid = "999999001"
    cursor.execute(
        "SELECT id FROM players WHERE espn_id = %s",
        (test_pid,),
    )
    row = cursor.fetchone()
    if row:
        return str(row["id"])
    cursor.execute(
        "CALL usp_upsert_player(%s, %s, %s, %s)",
        (test_pid, "Test Player QB", "QB", str(uuid.UUID(test_team_id))),
    )
    cursor.execute(
        "SELECT id FROM players WHERE espn_id = %s",
        (test_pid,),
    )
    return str(cursor.fetchone()["id"])


@pytest.fixture(scope="session")
def test_game_id(conn, cursor, test_team_id):
    """Create or return a test game for use across all tests."""
    espn_id = "999999001"
    cursor.execute(
        "SELECT id FROM games WHERE espn_id = %s",
        (espn_id,),
    )
    row = cursor.fetchone()
    if row:
        return str(row["id"])
    cursor.execute(
        "CALL usp_upsert_game(%s, %s, %s, %s, %s, %s, %s)",
        (espn_id, "final", datetime(2025, 9, 4, 20, 20, 0), test_team_id, test_team_id, 1, 2025),
    )
    cursor.execute(
        "SELECT id FROM games WHERE espn_id = %s",
        (espn_id,),
    )
    return str(cursor.fetchone()["id"])
