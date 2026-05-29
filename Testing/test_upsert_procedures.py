"""Unit tests for upsert stored procedures.

Tests: usp_upsert_team, usp_upsert_player, usp_upsert_game,
usp_upsert_team_game_stats, usp_upsert_player_game_stats
"""

import psycopg2
import pytest


class TestUpsertProceduresExist:
    """Verify all upsert procedures exist."""

    procedures = [
        "usp_upsert_team",
        "usp_upsert_player",
        "usp_upsert_game",
        "usp_upsert_team_game_stats",
        "usp_upsert_player_game_stats",
    ]

    @pytest.mark.parametrize("proc_name", procedures)
    def test_procedure_exists(self, cursor, proc_name):
        cursor.execute(
            "SELECT EXISTS(SELECT FROM pg_proc WHERE proname = %s)",
            (proc_name,)
        )
        assert cursor.fetchone()["exists"] is True, f"Procedure {proc_name} not found"
