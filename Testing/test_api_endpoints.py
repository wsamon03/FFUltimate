"""Integration tests for FastAPI endpoints.

Covers all endpoints documented in Documents/API_Documentation.md:

Ingestion (POST): /api/ingest/game, /api/ingest/week, /api/ingest/season
Retrieval (GET):  /api/teams, /api/games, /api/stats/game/{id},
                  /api/stats/player/{id}, /api/stats/team/{id},
                  /api/stats/leaderboard/{id}, /api/stats/fantasy/{id}

Error responses:  400, 404, 422

Uses pytest's test client (no live server needed).
"""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingest.service.app import app


# ===== Fixtures =====


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_conn():
    """Mock database connection that returns dict-like rows."""
    conn_mock = MagicMock()
    cur_mock = MagicMock()
    cur_mock.__enter__ = MagicMock(return_value=cur_mock)
    cur_mock.__exit__ = MagicMock(return_value=False)
    conn_mock.__enter__ = MagicMock(return_value=conn_mock)
    conn_mock.__exit__ = MagicMock(return_value=False)
    conn_mock.cursor.return_value = cur_mock
    conn_mock.autocommit = True
    return conn_mock, cur_mock


# ===== Utility for mocking DB results =====


def _setup_mock_teams(cur_mock):
    rows = [
        {"id": "00000000-0000-0000-0000-000000000001", "espn_id": "1", "abbr": "KC", "full_name": "Kansas City Chiefs"},
        {"id": "00000000-0000-0000-0000-000000000002", "espn_id": "2", "abbr": "SF", "full_name": "San Francisco 49ers"},
    ]
    cur_mock.execute.return_value = None
    cur_mock.fetchall.return_value = rows
    cur_mock.fetchone.return_value = rows[0]


def _setup_mock_games(cur_mock):
    rows = [
        {
            "id": "00000000-0000-0000-0000-000000000010", "espn_id": "401671769",
            "game_date": "2025-09-04T20:20:00", "status_code": "final",
            "week": 1, "season_year": 2025,
            "home_abbr": "KC", "home_name": "Kansas City Chiefs",
            "away_abbr": "SF", "away_name": "San Francisco 49ers",
        }
    ]
    cur_mock.execute.return_value = None
    cur_mock.fetchall.return_value = rows
    cur_mock.fetchone.return_value = rows[0]


# ===== Ingestion endpoints =====


class TestIngestionEndpoints:
    """Test POST /api/ingest/* endpoints."""

    @patch("ingest.service.ingestion_router.ESPNClient")
    @patch("ingest.service.ingestion_router.PgDBWriter")
    @patch("ingest.service.ingestion_router.IngestionEngine")
    def test_ingest_game_success(self, MockEngine, mock_writer, mock_espn, client):
        mock_engine_instance = MagicMock()
        mock_engine_instance.process_game = AsyncMock(return_value="550e8400-e29b-41d4-a716-446655440000")
        MockEngine.return_value = mock_engine_instance
        resp = client.post("/api/ingest/game", params={"event_id": "401671769"})
        assert resp.status_code == 200
        data = resp.json()
        assert "game_id" in data

    @patch("ingest.service.ingestion_router.ESPNClient")
    @patch("ingest.service.ingestion_router.PgDBWriter")
    @patch("ingest.service.ingestion_router.IngestionEngine")
    def test_ingest_game_not_found(self, MockEngine, mock_writer, mock_espn, client):
        mock_engine_instance = MagicMock()
        mock_engine_instance.process_game = AsyncMock(return_value=None)
        MockEngine.return_value = mock_engine_instance
        resp = client.post("/api/ingest/game", params={"event_id": "000000000"})
        assert resp.status_code == 404

    @patch("ingest.service.ingestion_router.ESPNClient")
    @patch("ingest.service.ingestion_router.PgDBWriter")
    @patch("ingest.service.ingestion_router.IngestionEngine")
    def test_ingest_week_success(self, MockEngine, mock_writer, mock_espn, client):
        mock_engine_instance = MagicMock()
        mock_engine_instance.process_week = AsyncMock(return_value=(16, 0))
        MockEngine.return_value = mock_engine_instance
        resp = client.post("/api/ingest/week", params={"year": 2025, "week": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "games_ingested" in data
        assert "games_failed" in data

    @patch("ingest.service.ingestion_router.ESPNClient")
    @patch("ingest.service.ingestion_router.PgDBWriter")
    @patch("ingest.service.ingestion_router.IngestionEngine")
    def test_ingest_season_success(self, MockEngine, mock_writer, mock_espn, client):
        mock_engine_instance = MagicMock()
        mock_engine_instance.process_season = AsyncMock(return_value=(285, 0))
        MockEngine.return_value = mock_engine_instance
        resp = client.post("/api/ingest/season", params={"year": 2025})
        assert resp.status_code == 200
        data = resp.json()
        assert "games_ingested" in data

    def test_ingest_week_invalid_week_number(self, client):
        resp = client.post("/api/ingest/week", params={"year": 2025, "week": 25})
        assert resp.status_code == 422

    def test_ingest_game_missing_event_id(self, client):
        resp = client.post("/api/ingest/game")
        assert resp.status_code == 422


# ===== Retrieval endpoints =====


class TestTeamsEndpoint:
    def test_get_teams(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        _setup_mock_teams(cur_mock)

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/teams")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["abbr"] == "KC"

    def test_teams_have_required_fields(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        _setup_mock_teams(cur_mock)

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/teams")

        data = resp.json()
        for team in data:
            assert "id" in team
            assert "espn_id" in team
            assert "abbr" in team
            assert "full_name" in team


class TestGamesEndpoint:
    def test_get_games(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        _setup_mock_games(cur_mock)

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/games")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_games_filtered_by_season(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn

        def capture_sql(*args, **kwargs):
            pass
        cur_mock.execute.side_effect = capture_sql
        cur_mock.fetchall.return_value = []

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/games", params={"season": 2025})

        assert resp.status_code == 200


class TestStatsGameEndpoint:
    def test_get_game_stats_success(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        row = {
            "game_espn_id": "401671769", "game_date": "2025-09-04T20:20:00",
            "home_team_name": "Kansas City Chiefs", "away_team_name": "San Francisco 49ers",
            "home_team_pts": 30, "away_team_pts": 24, "status_code": "final",
            "week": 1, "season_year": 2025,
        }
        cur_mock.fetchone.return_value = MagicMock(**row)
        cur_mock.fetchall.return_value = []
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/game/00000000-0000-0000-0000-000000000010")

        assert resp.status_code == 200

    def test_get_game_stats_not_found(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        cur_mock.fetchone.return_value = None
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/game/00000000-0000-0000-0000-000000009999")

        assert resp.status_code == 404


class TestStatsPlayerEndpoint:
    def test_get_player_stats(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        row = {
            "player_name": "Patrick Mahomes", "pass_yds": 354, "pass_td": 3,
            "team_name": "Kansas City Chiefs", "game_date": "2025-09-04T20:20:00",
        }
        cur_mock.fetchall.return_value = [MagicMock(**row)]
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/player/00000000-0000-0000-0000-000000000042")

        assert resp.status_code == 200


class TestStatsTeamEndpoint:
    def test_get_team_stats(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        row = {
            "team_name": "Kansas City Chiefs", "pts_total": 30,
            "off_total_yds": 412, "game_date": "2025-09-04T20:20:00",
        }
        cur_mock.fetchall.return_value = [MagicMock(**row)]
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/team/00000000-0000-0000-0000-000000000001")

        assert resp.status_code == 200


class TestLeaderboardEndpoint:
    def test_leaderboard_passing_default(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        row = {
            "player_name": "Patrick Mahomes", "pass_yds": 354,
            "team_name": "Kansas City Chiefs", "pass_comp": 28, "pass_att": 40,
        }
        cur_mock.fetchall.return_value = [MagicMock(**row)]
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/leaderboard/00000000-0000-0000-0000-000000000010")

        assert resp.status_code == 200

    def test_leaderboard_rushing(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        row = {
            "player_name": "Isiah Pacheco", "rush_yds": 120,
            "team_name": "Kansas City Chiefs", "rush_att": 20,
        }
        cur_mock.fetchall.return_value = [MagicMock(**row)]
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/leaderboard/00000000-0000-0000-0000-000000000010?category=rushing")

        assert resp.status_code == 200

    def test_leaderboard_receiving(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        row = {
            "player_name": "Travis Kelce", "rec_yds": 95,
            "team_name": "Kansas City Chiefs", "rec_receptions": 7,
        }
        cur_mock.fetchall.return_value = [MagicMock(**row)]
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/leaderboard/00000000-0000-0000-0000-000000000010?category=receiving")

        assert resp.status_code == 200

    def test_leaderboard_invalid_category(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/leaderboard/00000000-0000-0000-0000-000000000010?category=invalid")

        assert resp.status_code == 400


class TestFantasyStatsEndpoint:
    def test_get_fantasy_stats(self, client, mock_conn):
        conn_mock, cur_mock = mock_conn
        row = {
            "player_name": "Patrick Mahomes", "pass_yds": 354, "pass_td": 3,
            "rush_yds": 72, "rush_td": 1, "rec_yds": 65, "rec_td": 1,
            "rec_receptions": 5, "game_date": "2025-09-04T20:20:00",
        }
        cur_mock.fetchall.return_value = [MagicMock(**row)]
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/fantasy/00000000-0000-0000-0000-000000000042")

        assert resp.status_code == 200
        data = resp.json()
        # Verify fantasy points are calculated
        assert "total_yards" in data[0]
        assert "fantasy_points" in data[0]

    def test_fantasy_points_formula(self, client, mock_conn):
        """Verify fantasy points = yards/10 + TD*4 + rec*0.5."""
        conn_mock, cur_mock = mock_conn
        row = {
            "player_name": "Test", "pass_yds": 354, "rush_yds": 0, "rec_yds": 0,
            "pass_td": 3, "rush_td": 0, "rec_td": 0, "rec_receptions": 5,
            "game_date": "2025-09-04T20:20:00",
        }
        cur_mock.fetchall.return_value = [MagicMock(**row)]
        cur_mock.execute.return_value = None

        with patch("ingest.service.retrieval_router.PgDBWriter") as MockWriter:
            instance = MagicMock()
            instance.__enter__ = MagicMock(return_value=conn_mock)
            instance.__exit__ = MagicMock(return_value=False)
            MockWriter.return_value = instance
            resp = client.get("/api/stats/fantasy/00000000-0000-0000-0000-000000000042")

        data = resp.json()
        expected_fp = 354 / 10 + 3 * 4 + 5 * 0.5  # 35.4 + 12 + 2.5 = 49.9
        assert abs(data[0]["fantasy_points"] - expected_fp) < 0.01


# ===== Swagger / docs endpoint =====


class TestSwaggerDocs:
    def test_swagger_docs_available(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_spec(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        assert "paths" in spec
        paths = list(spec["paths"].keys())
        assert "/api/teams" in paths
        assert "/api/games" in paths
        assert "/api/ingest/game" in paths
        assert "/api/ingest/week" in paths
        assert "/api/ingest/season" in paths
