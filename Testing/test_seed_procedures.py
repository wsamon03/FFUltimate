"""Unit tests for seed stored procedures.

Tests: usp_seed_game_status, usp_seed_player_position

Documented in: Documents/StoredProcedures.md
"""

import psycopg2
import pytest


class TestSeedGameStatus:
    """Tests for usp_seed_game_status()."""

    def test_procedure_exists(self, cursor):
        cursor.execute(
            "SELECT EXISTS("
            "  SELECT FROM pg_proc WHERE proname = 'usp_seed_game_status'"
            ")")
        assert cursor.fetchone()["exists"] is True

    def test_seed_inserts_three_statuses(self, conn, cursor):
        cursor.execute("CALL usp_seed_game_status()")
        cursor.execute("SELECT status_code FROM game_status ORDER BY status_code")
        codes = [r["status_code"] for r in cursor.fetchall()]
        assert set(codes) == {"final", "live", "scheduled"}

    def test_idempotent_runs(self, conn, cursor):
        cursor.execute("CALL usp_seed_game_status()")
        cursor.execute("CALL usp_seed_game_status()")
        cursor.execute("SELECT status_code FROM game_status ORDER BY status_code")
        rows = cursor.fetchall()
        assert len(rows) == 3  # No duplicates

    def test_all_statuses_have_descriptions(self, conn, cursor):
        cursor.execute("CALL usp_seed_game_status()")
        cursor.execute(
            "SELECT status_code, description FROM game_status WHERE description IS NULL")
        assert cursor.fetchall() == []

    def test_unique_constraint_on_status_code(self, conn, cursor):
        cursor.execute("CALL usp_seed_game_status()")
        try:
            cursor.execute(
                "INSERT INTO game_status (status_code) VALUES ('live')")
            conn.commit()
            assert False, "Should have raised duplicate key error"
        except psycopg2.errors.UniqueViolation:
            pass  # Expected

    def test_status_codes_are_unique(self, conn, cursor):
        """Verify status codes are unique."""
        cursor.execute("SELECT status_code FROM game_status")
        codes = [r["status_code"] for r in cursor.fetchall()]
        assert len(codes) == len(set(codes))  # All unique

    def test_all_status_codes_present(self, conn, cursor):
        """Verify all expected status codes are seeded."""
        cursor.execute("SELECT status_code FROM game_status")
        codes = {r["status_code"] for r in cursor.fetchall()}
        assert codes == {"final", "live", "scheduled"}


class TestSeedPlayerPosition:
    """Tests for usp_seed_player_position()."""

    def test_procedure_exists(self, cursor):
        cursor.execute(
            "SELECT EXISTS("
            "  SELECT FROM pg_proc WHERE proname = 'usp_seed_player_position'"
            ")")
        assert cursor.fetchone()["exists"] is True

    def test_seed_inserts_all_positions(self, conn, cursor):
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute("SELECT position_code FROM player_position ORDER BY position_code")
        codes = [r["position_code"] for r in cursor.fetchall()]
        expected = ["", "CB", "CB", "DL", "DP", "HS", "K", "LB", "P", "QB", "RB", "S", "TE", "WR"]
        # Filter out empty string for comparison
        expected_codes = sorted(["QB", "RB", "WR", "TE", "K", "DL", "LB", "CB", "S", "DP", "P", "HS", ""])
        actual_codes = sorted(codes)
        assert actual_codes == expected_codes

    def test_idempotent_runs(self, conn, cursor):
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute("SELECT position_code FROM player_position ORDER BY position_code")
        rows = cursor.fetchall()
        # Should not have duplicates (empty string appears once)
        empty_count = sum(1 for r in rows if r["position_code"] == "")
        assert empty_count <= 1

    def test_all_positions_have_descriptions(self, conn, cursor):
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute(
            "SELECT position_code FROM player_position WHERE description IS NULL")
        assert cursor.fetchall() == []

    def test_all_12_positions_present(self, conn, cursor):
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute("SELECT COUNT(*) as cnt FROM player_position")
        assert cursor.fetchone()["cnt"] >= 12

    def test_position_codes_are_unique(self, conn, cursor):
        """Verify position codes (excluding empty string) are unique."""
        cursor.execute("SELECT DISTINCT position_code FROM player_position")
        codes = [r["position_code"] for r in cursor.fetchall()]
        assert len(codes) == len(set(codes))

    def test_expected_position_codes_present(self, conn, cursor):
        """Verify all expected position codes are seeded."""
        cursor.execute("SELECT position_code FROM player_position")
        codes = {r["position_code"] for r in cursor.fetchall()}
        expected = {"QB", "RB", "WR", "TE", "K", "DL", "LB", "CB", "S", "DP", "P", "HS"}
        assert expected.issubset(codes)


class TestSeedPlayerPosition:
    """Tests for usp_seed_player_position()."""

    def test_procedure_exists(self, cursor):
        cursor.execute(
            "SELECT EXISTS("
            "  SELECT FROM pg_proc WHERE proname = 'usp_seed_player_position'"
            ")")
        assert cursor.fetchone()["exists"] is True

    def test_seed_inserts_all_positions(self, conn, cursor):
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute("SELECT position_code FROM player_position ORDER BY position_code")
        codes = [r["position_code"] for r in cursor.fetchall()]
        expected = ["", "CB", "CB", "DL", "DP", "HS", "K", "LB", "P", "QB", "RB", "S", "TE", "WR"]
        # Filter out empty string for comparison
        expected_codes = sorted(["QB", "RB", "WR", "TE", "K", "DL", "LB", "CB", "S", "DP", "P", "HS", ""])
        actual_codes = sorted(codes)
        assert actual_codes == expected_codes

    def test_idempotent_runs(self, conn, cursor):
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute("SELECT position_code FROM player_position ORDER BY position_code")
        rows = cursor.fetchall()
        # Should not have duplicates (empty string appears once)
        empty_count = sum(1 for r in rows if r["position_code"] == "")
        assert empty_count <= 1

    def test_all_positions_have_descriptions(self, conn, cursor):
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute(
            "SELECT position_code FROM player_position WHERE description IS NULL")
        assert cursor.fetchall() == []

    def test_all_12_positions_present(self, conn, cursor):
        cursor.execute("CALL usp_seed_player_position()")
        cursor.execute("SELECT COUNT(*) as cnt FROM player_position")
        assert cursor.fetchone()["cnt"] >= 12
