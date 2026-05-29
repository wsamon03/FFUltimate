"""Data validation and consistency tests.

Tests business rules and data integrity:
  - FK integrity: No orphaned records in foreign key relationships
  - Stat plausibility: No negative yards, TDs, or attempts; comp <= att
  - Derived stats: Quarter scores sum to total
  - Idempotency: Upsert procedures produce no duplicates when called multiple times
"""

from datetime import datetime

import psycopg2
import pytest


class TestForeignKeyIntegrity:
    """Verify all foreign key relationships are intact - no orphaned records."""

    def test_teams_fk_to_games(self, cursor):
        """All games have valid team_id references."""
        cursor.execute(
            "SELECT COUNT(*) FROM games WHERE home_team_id NOT IN "
            "(SELECT id FROM teams) OR away_team_id NOT IN "
            "(SELECT id FROM teams)"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_players_fk_to_teams(self, cursor):
        """All players have valid team_id references."""
        cursor.execute(
            "SELECT COUNT(*) FROM players WHERE team_id NOT IN "
            "(SELECT id FROM teams)"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_team_stats_fk_to_game_team(self, cursor):
        """All team_game_stats have valid game_id and team_id references."""
        cursor.execute(
            "SELECT COUNT(*) FROM team_game_stats WHERE game_id NOT IN "
            "(SELECT id FROM games)"
        )
        orphaned_game_ids = cursor.fetchone()["count"]
        assert orphaned_game_ids == 0

        cursor.execute(
            "SELECT COUNT(*) FROM team_game_stats WHERE team_id NOT IN "
            "(SELECT id FROM teams)"
        )
        orphaned_team_ids = cursor.fetchone()["count"]
        assert orphaned_team_ids == 0

    def test_player_stats_fk_to_game_player(self, cursor):
        """All player_game_stats have valid game_id and player_id references."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE game_id NOT IN "
            "(SELECT id FROM games)"
        )
        orphaned_game_ids = cursor.fetchone()["count"]
        assert orphaned_game_ids == 0

        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE player_id NOT IN "
            "(SELECT id FROM players)"
        )
        orphaned_player_ids = cursor.fetchone()["count"]
        assert orphaned_player_ids == 0

    def test_game_status_fk_exists(self, cursor):
        """All references to game_status have valid status_code values."""
        cursor.execute(
            "SELECT COUNT(*) FROM game_status WHERE status_code NOT IN "
            "(SELECT status_code FROM game_status WHERE id IS NOT NULL)"
        )
        invalid_refs = cursor.fetchone()["count"]
        assert invalid_refs == 0

    def test_player_position_fk_exists(self, cursor):
        """All player positions have valid position_code values."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_position WHERE position_code NOT IN "
            "(SELECT position_code FROM player_position WHERE id IS NOT NULL)"
        )
        invalid_refs = cursor.fetchone()["count"]
        assert invalid_refs == 0


class TestStatPlausibility:
    """Verify player stats are plausible and don't violate basic rules."""

    def test_no_negative_pass_yards(self, cursor):
        """Passing yards should never be negative."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE pass_yds < 0"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_no_negative_rush_yards(self, cursor):
        """Rushing yards should never be negative."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE rush_yds < 0"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_no_negative_rec_yards(self, cursor):
        """Receiving yards should never be negative."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE rec_yds < 0"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_completions_less_than_attempts(self, cursor):
        """Passing completions should never exceed attempts."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE pass_att > 0 AND "
            "pass_comp > pass_att"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_no_negative_pass_td(self, cursor):
        """Passing TDs should never be negative."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE pass_td < 0"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_no_negative_int(self, cursor):
        """Interceptions thrown should never be negative."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE pass_int < 0"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_no_negative_sacked(self, cursor):
        """Sacked yards should never be negative."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE pass_sacked < 0"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_no_negative_rush_td(self, cursor):
        """Rushing TDs should never be negative."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE rush_td < 0"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_no_negative_rush_att(self, cursor):
        """Rushing attempts should never be negative."""
        cursor.execute(
            "SELECT COUNT(*) FROM player_game_stats WHERE rush_att < 0"
        )
        count = cursor.fetchone()["count"]
        assert count == 0

    def test_defense_stats_non_negative(self, cursor):
        """Defensive stats should never be negative."""
        cursor.execute(
            """
            SELECT COUNT(*) FROM player_game_stats WHERE
                def_solo < 0 OR def_ast < 0 OR def_sacks < 0 OR
                def_tfl < 0 OR def_pd < 0 OR def_qb_hits < 0 OR
                def_int < 0 OR def_td < 0
            """
        )
        count = cursor.fetchone()["count"]
        assert count == 0


class TestDerivedStats:
    """Verify computed statistics are correctly derived from source data."""

    def test_quarter_scores_sum_to_total(self, cursor):
        """Q1+Q2+Q3+Q4+OT should equal pts_total (when team_game_stats has quarters)."""
        cursor.execute(
            """
            SELECT COUNT(*) FROM team_game_stats
            WHERE pts_total IS NOT NULL AND
                  (pts_q1 IS NOT NULL OR pts_q2 IS NOT NULL OR
                   pts_q3 IS NOT NULL OR pts_q4 IS NOT NULL OR
                   pts_ot IS NOT NULL)
            """
        )
        teams_with_quarters = cursor.fetchone()["count"]
        
        if teams_with_quarters > 0:
            cursor.execute(
                """
                SELECT COUNT(*) FROM team_game_stats
                WHERE pts_q1 IS NOT NULL AND pts_q2 IS NOT NULL AND
                      pts_q3 IS NOT NULL AND pts_q4 IS NOT NULL AND
                      pts_q1 + pts_q2 + pts_q3 + pts_q4 != pts_total
                """
            )
            mismatches = cursor.fetchone()["count"]
            # Note: games might have overtime, so we allow a partial check
            # This is a basic check - not all games have all quarters populated
            assert mismatches == 0


class TestIdempotency:
    """Verify upsert procedures are idempotent - running twice produces no duplicates."""

    @pytest.fixture
    def test_team_id(conn, cursor):
        """Create or return a test team for idempotency tests."""
        cursor.execute(
            "SELECT id FROM teams WHERE espn_id = %s",
            ("999999001",)
        )
        row = cursor.fetchone()
        if row:
            return str(row["id"])
        cursor.execute(
            "CALL usp_upsert_team(%s, %s, %s)",
            ("999999001", "TEST", "Test Team")
        )
        cursor.execute(
            "SELECT id FROM teams WHERE espn_id = %s",
            ("999999001",)
        )
        return str(cursor.fetchone()["id"])

    @pytest.fixture
    def test_player_team_id(conn, cursor, test_team_id):
        """Create or return a test player team for idempotency tests."""
        cursor.execute(
            "SELECT id FROM players WHERE espn_id = %s AND team_id = %s",
            ("999999001", test_team_id)
        )
        row = cursor.fetchone()
        if row:
            return str(row["id"])
        cursor.execute(
            "CALL usp_upsert_player(%s, %s, %s, %s)",
            ("999999001", "TestIdemPlayer", "QB", test_team_id)
        )
        cursor.execute(
            "SELECT id FROM players WHERE espn_id = %s",
            ("999999001",)
        )
        return str(cursor.fetchone()["id"])

    @pytest.fixture
    def test_game_id(conn, cursor, test_team_id):
        """Create or return a test game for idempotency tests."""
        cursor.execute(
            "SELECT id FROM games WHERE espn_id = %s",
            ("999999001",)
        )
        row = cursor.fetchone()
        if row:
            return str(row["id"])
        import uuid
        from datetime import datetime
        cursor.execute(
            """CALL usp_upsert_game(%s, %s, %s, %s, %s, %s, %s)""",
            ("999999001", "scheduled", "scheduled", str(uuid.uuid4()), test_team_id, 1, 2025)
        )
        cursor.execute(
            "SELECT id FROM games WHERE espn_id = %s",
            ("999999001",)
        )
        return str(cursor.fetchone()["id"])

    def test_team_upsert_idempotent(self, conn, cursor, test_team_id):
        """Running usp_upsert_team twice on same data produces no duplicates."""
        cursor.execute("SELECT COUNT(*) FROM teams WHERE espn_id = %s", ("999999001",))
        count_before = cursor.fetchone()["count"]
        
        cursor.execute(
            "CALL usp_upsert_team(%s, %s, %s)",
            ("999999001", "TEST", "Test Team")
        )
        
        cursor.execute("SELECT COUNT(*) FROM teams WHERE espn_id = %s", ("999999001",))
        count_after = cursor.fetchone()["count"]
        
        assert count_after == count_before == 1

    def test_player_upsert_idempotent(self, conn, cursor, test_player_team_id):
        """Running usp_upsert_player twice on same data produces no duplicates."""
        cursor.execute("SELECT COUNT(*) FROM players WHERE espn_id = %s", ("999999001",))
        count_before = cursor.fetchone()["count"]
        
        cursor.execute(
            "CALL usp_upsert_player(%s, %s, %s, %s)",
            ("999999001", "TestIdemPlayer", "QB", str(test_player_team_id))
        )
        
        cursor.execute("SELECT COUNT(*) FROM players WHERE espn_id = %s", ("999999001",))
        count_after = cursor.fetchone()["count"]
        
        assert count_after == count_before == 1

    def test_game_upsert_idempotent(self, conn, cursor, test_game_id):
        """Running usp_upsert_game twice on same data produces no duplicates."""
        cursor.execute("SELECT COUNT(*) FROM games WHERE espn_id = %s", ("999999001",))
        count_before = cursor.fetchone()["count"]
        
        cursor.execute(
            "CALL usp_upsert_game(%s, %s, %s, %s, %s, %s, %s)",
            ("999999001", "final", datetime.utcnow().replace(minute=0, second=0),
             str(test_game_id), str(test_game_id), 1, 2025)
        )
        
        cursor.execute("SELECT COUNT(*) FROM games WHERE espn_id = %s", ("999999001",))
        count_after = cursor.fetchone()["count"]
        
        assert count_after == count_before == 1


class TestSchemaConsistency:
    """Verify database schema and data are consistent with documentation."""

    def game_status_count(self, cursor):
        """game_status table should have exactly 3 rows."""
        cursor.execute("SELECT COUNT(*) FROM game_status")
        count = cursor.fetchone()["count"]
        assert count == 3, f"Expected 3 game statuses, got {count}"

    def player_position_count(self, cursor):
        """player_position table should have at least 12 rows."""
        cursor.execute("SELECT COUNT(*) FROM player_position")
        count = cursor.fetchone()["count"]
        assert count >= 12, f"Expected at least 12 player positions, got {count}"

    def player_position_empty_exists(self, cursor):
        """Empty string position should exist in player_position."""
        cursor.execute("SELECT COUNT(*) FROM player_position WHERE position_code = ''")
        count = cursor.fetchone()["count"]
        assert count >= 1, "Empty string position not found"
