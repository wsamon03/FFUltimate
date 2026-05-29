"""Unit tests for analysis multi-table stored procedures.

Tests verify that analysis procedures exist.

Player-focused: sp_get_player_game_complete, sp_get_player_season_complete,
                sp_get_player_season_week_by_week, sp_get_player_career_complete,
                sp_get_player_career_by_team
Team-focused:   sp_get_game_both_teams, sp_get_team_season_complete,
                sp_get_team_season_week_by_week, sp_get_team_career_complete,
                sp_get_team_vs_opponent, sp_get_team_season_all_games
Leaderboard:    sp_get_game_passing_leaders, sp_get_game_rushing_leaders,
                sp_get_game_receiving_leaders
Fantasy:        sp_get_player_fantasy_stats
"""

import psycopg2
import pytest


class TestAnalysisProceduresExist:
    """Verify all analysis procedures exist."""

    procedures = [
        # Player-focused procedures
        "fn_get_player_game_complete",
        "fn_get_player_season_complete",
        "fn_get_player_season_week_by_week",
        "fn_get_player_career_complete",
        "fn_get_player_career_by_team",
        # Team-focused procedures
        "fn_get_game_both_teams",
        "fn_get_team_season_complete",
        "fn_get_team_season_week_by_week",
        "fn_get_team_career_complete",
        "fn_get_team_vs_opponent",
        "fn_get_team_season_all_games",
        # Leaderboard procedures
        "fn_get_game_passing_leaders",
        "fn_get_game_rushing_leaders",
        "fn_get_game_receiving_leaders",
        # Fantasy procedures
        "fn_get_player_fantasy_stats",
    ]

    @pytest.mark.parametrize("proc_name", procedures)
    def test_procedure_exists(self, cursor, proc_name):
        cursor.execute(
            "SELECT EXISTS(SELECT FROM pg_proc WHERE proname = %s)",
            (proc_name,)
        )
        assert cursor.fetchone()["exists"] is True, f"Procedure {proc_name} not found"
