"""Unit tests for retrieval stored procedures.

These tests verify that retrieval procedures exist.
"""

import psycopg2
import pytest


class TestRetrievalProceduresExist:
    """Verify all retrieval procedures exist."""

    procedures = [
        # Team procedures
        "fn_get_all_teams",
        "fn_get_teams_by_espn_id",
        "fn_get_team_by_espn_id",
        "fn_get_active_players",
        "fn_get_players_by_team",
        "fn_get_players_by_espn_id",
        # Game procedures
        "fn_get_all_games",
        "fn_get_games_by_date_range",
        "fn_get_games_by_espn_id",
        "fn_get_game_by_espn_id",
        # TeamStats procedures
        "fn_get_team_stats_for_game",
        "fn_get_team_stats_for_team",
        "fn_get_all_team_stats",
        "fn_get_team_stats_vs_opponent",
        # PlayerStats procedures
        "fn_get_player_stats_for_game",
        "fn_get_player_stats_for_player",
        "fn_get_all_player_stats",
        "fn_get_player_stats_vs_opponent",
        "fn_get_player_stats_for_team",
        # Analysis procedures
        "fn_get_top_passers",
        "fn_get_top_rushers",
        "fn_get_top_receivers",
        "fn_get_team_scoring_leaders",
        "fn_get_game_summary",
        "fn_get_top_scoring_teams",
    ]

    @pytest.mark.parametrize("proc_name", procedures)
    def test_procedure_exists(self, cursor, proc_name):
        cursor.execute(
            "SELECT EXISTS(SELECT FROM pg_proc WHERE proname = %s)",
            (proc_name,)
        )
        assert cursor.fetchone()["exists"] is True, f"Procedure {proc_name} not found"
