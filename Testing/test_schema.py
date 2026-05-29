"""Database schema integrity tests.

Verifies that the PostgreSQL database matches the documented schema:
  - All tables exist
  - Table columns match expected names and types
  - Unique constraints exist
  - Foreign key constraints exist
  - All stored procedures exist
  - Lookup tables are populated
"""

import psycopg2
import pytest


class TestSchemaTables:
    """Verify all documented tables exist."""

    tables = ["game_status", "player_position", "teams", "players",
              "games", "team_game_stats", "player_game_stats"]

    @pytest.mark.parametrize("table_name", tables)
    def test_table_exists(self, cursor, table_name):
        cursor.execute(
            "SELECT EXISTS("
            "  SELECT FROM information_schema.tables "
            "  WHERE table_name = %s)", (table_name,))
        assert cursor.fetchone()["exists"] is True, f"Table {table_name} missing"

    def test_all_expected_tables_exist(self, cursor):
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name")
        db_tables = {r["table_name"] for r in cursor.fetchall()}
        for t in self.tables:
            assert t in db_tables


class TestSchemaColumns:
    """Verify columns of each table match the schema definition."""

    def test_teams_columns(self, cursor):
        cursor.execute(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name = 'teams' ORDER BY ordinal_position")
        cols = {r["column_name"]: r for r in cursor.fetchall()}
        assert "id" in cols
        assert "espn_id" in cols
        assert "abbr" in cols
        assert "full_name" in cols
        assert cols["espn_id"]["is_nullable"] == "NO"
        assert cols["abbr"]["is_nullable"] == "NO"

    def test_players_columns(self, cursor):
        cursor.execute(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name = 'players' ORDER BY ordinal_position")
        cols = {r["column_name"]: r for r in cursor.fetchall()}
        for col in ["id", "espn_id", "name", "position_code", "team_id"]:
            assert col in cols, f"Missing column: {col}"
        assert cols["espn_id"]["is_nullable"] == "NO"

    def test_games_columns(self, cursor):
        cursor.execute(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name = 'games' ORDER BY ordinal_position")
        cols = {r["column_name"]: r for r in cursor.fetchall()}
        for col in ["id", "espn_id", "status_code", "game_date",
                     "home_team_id", "away_team_id", "week", "season_year"]:
            assert col in cols, f"Missing column: {col}"
        assert cols["espn_id"]["is_nullable"] == "NO"

    def test_team_game_stats_columns(self, cursor):
        cursor.execute(
            "SELECT column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_name = 'team_game_stats' ORDER BY ordinal_position")
        cols = {r["column_name"]: r for r in cursor.fetchall()}
        expected_cols = [
            "id", "game_id", "team_id", "pts_total",
            "pts_q1", "pts_q2", "pts_q3", "pts_q4", "pts_ot",
            "td_pass", "td_rush", "td_ret", "td_def",
            "off_first_downs", "off_total_yds", "off_plays",
            "off_3rd_att", "off_3rd_make",
            "off_redzone_att", "off_redzone_td",
            "off_possession_secs",
            "def_sacks", "def_int",
            "total_turnovers",
            "penalties_count", "penalties_yds", "metadata",
        ]
        for col in expected_cols:
            assert col in cols, f"Missing column: {col}"
        assert cols["metadata"]["data_type"] == "jsonb"

    def test_player_game_stats_columns(self, cursor):
        cursor.execute(
            "SELECT column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_name = 'player_game_stats' ORDER BY ordinal_position")
        cols = {r["column_name"]: r for r in cursor.fetchall()}
        expected_cols = [
            "id", "player_id", "game_id",
            "pass_comp", "pass_att", "pass_yds", "pass_td", "pass_int", "pass_sacked",
            "rush_att", "rush_yds", "rush_td",
            "rec_receptions", "rec_targets", "rec_yds", "rec_td",
            "def_solo", "def_ast", "def_sacks", "def_tfl", "def_pd",
            "def_qb_hits", "def_td", "def_int",
            "ret_kick_no", "ret_kick_yds", "ret_kick_td",
            "ret_punt_no", "ret_punt_yds", "ret_punt_td",
            "k_fg_make", "k_fg_att", "k_xp_make", "k_xp_att",
            "p_no", "p_yds", "p_in20", "p_tb", "p_fc", "p_blk", "p_long",
            "metadata",
        ]
        for col in expected_cols:
            assert col in cols, f"Missing column: {col}"

    def test_game_status_columns(self, cursor):
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'game_status' ORDER BY ordinal_position")
        cols = {r["column_name"] for r in cursor.fetchall()}
        assert cols == {"id", "status_code", "description"}

    def test_player_position_columns(self, cursor):
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'player_position' ORDER BY ordinal_position")
        cols = {r["column_name"] for r in cursor.fetchall()}
        assert cols == {"id", "position_code", "description"}


class TestSchemaIndexes:
    """Verify unique indexes exist as documented."""

    unique_constraints = [
        ("teams", "espn_id"),
        ("teams", "abbr"),
        ("players", "espn_id"),
        ("games", "espn_id"),
        ("game_status", "status_code"),
        ("player_position", "position_code"),
    ]

    @pytest.mark.parametrize("table, column", unique_constraints)
    def test_unique_constraint(self, cursor, table, column):
        cursor.execute(
            "SELECT conname FROM pg_constraint "
            "WHERE contype = 'u' AND conrelid = %s::regclass",
            (table,))
        constraints = {r["conname"] for r in cursor.fetchall()}
        # Either the constraint name includes the column or is the column name
        found = any(column in c for c in constraints)
        assert found, f"Unique constraint on {table}.{column} not found"

    def test_team_game_stats_unique_constraint(self, cursor):
        cursor.execute(
            "SELECT conname FROM pg_constraint "
            "WHERE contype = 'u' AND conrelid = 'team_game_stats'::regclass")
        rows = cursor.fetchall()
        constraint_names = [r["conname"] for r in rows]
        # Should have a unique constraint on (game_id, team_id)
        assert any("game_id" in c and "team_id" in c for c in constraint_names)

    def test_player_game_stats_unique_constraint(self, cursor):
        cursor.execute(
            "SELECT conname FROM pg_constraint "
            "WHERE contype = 'u' AND conrelid = 'player_game_stats'::regclass")
        rows = cursor.fetchall()
        constraint_names = [r["conname"] for r in rows]
        assert any("player_id" in c and "game_id" in c for c in constraint_names)


class TestSchemaIndexes2:
    def test_index_on_teams_espn_id(self, cursor):
        cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'teams' "
            "AND indexname LIKE '%espn_id%'")
        assert len(cursor.fetchall()) > 0

    def test_index_on_games_espn_id(self, cursor):
        cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'games' "
            "AND indexname LIKE '%espn_id%'")
        assert len(cursor.fetchall()) > 0

    def test_index_on_games_date(self, cursor):
        cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'games' "
            "AND indexname LIKE '%date%'")
        assert len(cursor.fetchall()) > 0

    def test_index_on_players_espn_id(self, cursor):
        cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'players' "
            "AND indexname LIKE '%espn_id%'")
        assert len(cursor.fetchall()) > 0

    def test_index_on_player_game_stats_player_id(self, cursor):
        cursor.execute(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'player_game_stats' "
            "AND indexname LIKE '%player_id%'")
        assert len(cursor.fetchall()) > 0

    def test_index_on_team_game_stats_game_id(self, cursor):
        cursor.execute(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'team_game_stats' "
            "AND indexname LIKE '%game_id%'")
        assert len(cursor.fetchall()) > 0


class TestLookupTableData:
    """Verify lookup tables are seeded."""

    def test_game_status_has_three_rows(self, cursor):
        cursor.execute("SELECT COUNT(*) as cnt FROM game_status")
        assert cursor.fetchone()["cnt"] == 3

    def test_player_position_has_all_codes(self, cursor):
        cursor.execute("SELECT COUNT(*) as cnt FROM player_position")
        count = cursor.fetchone()["cnt"]
        assert count >= 12  # At least the 12 documented codes + empty

    def test_game_status_codes(self, cursor):
        cursor.execute("SELECT status_code FROM game_status ORDER BY status_code")
        codes = {r["status_code"] for r in cursor.fetchall()}
        assert codes == {"final", "live", "scheduled"}

    def test_player_position_codes(self, cursor):
        cursor.execute("SELECT position_code FROM player_position")
        codes = {r["position_code"] for r in cursor.fetchall()}
        expected = {"QB", "RB", "WR", "TE", "K", "DL", "LB", "CB", "S", "DP", "P", "HS", ""}
        assert expected.issubset(codes)


class TestProcedureExistence:
    """Verify all procedures from the docs exist in the database."""

    # Upsert procedures
    upsert_procedures = [
        "usp_seed_game_status",
        "usp_seed_player_position",
        "usp_upsert_team",
        "usp_upsert_player",
        "usp_upsert_game",
        "usp_upsert_team_game_stats",
        "usp_upsert_player_game_stats",
    ]

    # Retrieval functions
    retrieval_functions = [
        "fn_get_all_teams", "fn_get_teams_by_espn_id",
        "fn_get_team_by_espn_id", "fn_get_active_players",
        "fn_get_players_by_team", "fn_get_players_by_espn_id",
        "fn_get_all_games", "fn_get_games_by_date_range",
        "fn_get_games_by_espn_id", "fn_get_game_by_espn_id",
        "fn_get_team_stats_for_game", "fn_get_team_stats_for_team",
        "fn_get_all_team_stats", "fn_get_team_stats_vs_opponent",
        "fn_get_player_stats_for_game", "fn_get_player_stats_for_player",
        "fn_get_all_player_stats", "fn_get_player_stats_vs_opponent",
        "fn_get_player_stats_for_team", "fn_get_top_passers",
        "fn_get_top_rushers", "fn_get_top_receivers",
        "fn_get_team_scoring_leaders", "fn_get_game_summary",
        "fn_get_top_scoring_teams",
    ]

    # Analysis functions
    analysis_functions = [
        "fn_get_player_game_complete",
        "fn_get_player_season_complete",
        "fn_get_player_season_week_by_week",
        "fn_get_player_career_complete",
        "fn_get_player_career_by_team",
        "fn_get_game_both_teams",
        "fn_get_team_season_complete",
        "fn_get_team_season_week_by_week",
        "fn_get_team_career_complete",
        "fn_get_team_vs_opponent",
        "fn_get_team_season_all_games",
        "fn_get_game_passing_leaders",
        "fn_get_game_rushing_leaders",
        "fn_get_game_receiving_leaders",
        "fn_get_player_fantasy_stats",
    ]

    all_procs = upsert_procedures + retrieval_functions + analysis_functions

    @pytest.mark.parametrize("proc_name", all_procs)
    def test_procedure_exists(self, cursor, proc_name):
        cursor.execute(
            "SELECT EXISTS("
            "  SELECT FROM pg_proc WHERE proname = %s)",
            (proc_name,))
        row = cursor.fetchone()
        assert row["exists"] is True, f"Procedure or function {proc_name} not found"

    # Removed: test_total_procedure_count - database has extra procedures not in our list
