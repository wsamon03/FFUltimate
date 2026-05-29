"""
Main ingestion orchestration for NFL game data.
Handles upserting dimensions and inserting facts.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from database import get_or_create_by_unique
from espn_api import fetch_game_summary, get_boxscore, get_game_info
from transformers import (
    parse_possession_time, parse_fraction, parse_int,
    map_stat_by_label, parse_sacks, safe_jsonb
)

logger = logging.getLogger(__name__)

# ESPN stat label mappings
TEAM_STAT_LABELS = {
    "points": ["PTS", "POINTS"],
    "q1": ["Q1"], "q2": ["Q2"], "q3": ["Q3"], "q4": ["Q4"], "ot": ["OT"],
    "first_downs": ["FIRST DOWNS", "1ST Downs"],
    "total_yards": ["TOTAL YARDS", "TOT YDS"],
    "third_downs": ["3RD DOWN", "3RD Downs"],
    "red_zone": ["RED ZONE", "Red Zone"],
    "possession": ["POSSESSION", "TIME OF POSS.", "TOP"],
    "turnovers": ["TURNOVERS", "TO"],
    "penalties": ["PENALTIES", "PEN"],
    "penalty_yards": ["PENALTY YARDS", "PEN YDS"],
}


def upsert_team(abbr: str, full_name: str) -> int:
    """
    Upsert a team into the database.

    Args:
        abbr: Team abbreviation (e.g., "KC", "SF")
        full_name: Full team name

    Returns:
        Team ID
    """
    select_query = """
        SELECT id FROM teams WHERE abbr = %s
    """
    insert_query = """
        INSERT INTO teams (abbr, full_name) VALUES (%s, %s)
        RETURNING id
    """

    return get_or_create_by_unique(
        select_query, insert_query,
        (abbr,),
        (abbr, full_name)
    )


def upsert_player(external_id: str, name: str, position: str, team_id: Optional[int]) -> int:
    """
    Upsert a player into the database.

    Args:
        external_id: ESPN athlete ID
        name: Player name
        position: Position abbreviation
        team_id: Associated team ID (can be None)

    Returns:
        Player ID
    """
    select_query = """
        SELECT id FROM players WHERE external_id = %s
    """
    insert_query = """
        INSERT INTO players (external_id, name, position, team_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """

    return get_or_create_by_unique(
        select_query, insert_query,
        (external_id,),
        (external_id, name, position, team_id)
    )


def upsert_game(espn_id: str, status: str, game_date: datetime,
               home_espn_id: str, away_espn_id: str,
               week: Optional[int] = None, season_year: Optional[int] = None) -> int:
    """
    Upsert a game into the database.

    Args:
        espn_id: ESPN event ID
        status: Game status (scheduled, live, final)
        game_date: Game date/time
        home_espn_id: Home team's ESPN ID for this game
        away_espn_id: Away team's ESPN ID for this game
        week: Week number (optional)
        season_year: Season year (optional)

    Returns:
        Game ID
    """
    select_query = """
        SELECT id FROM games WHERE espn_id = %s
    """
    insert_query = """
        INSERT INTO games (espn_id, status, game_date, home_espn_id, away_espn_id, week, season_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """

    return get_or_create_by_unique(
        select_query, insert_query,
        (espn_id,),
        (espn_id, status, game_date, home_team_id, away_team_id, week, season_year)
    )


def insert_team_stats(conn, game_id: int, team_id: int, stats: Dict[str, Any]):
    """
    Insert or update team game statistics.

    Args:
        conn: Database connection
        game_id: Game ID
        team_id: Team ID
        stats: Dictionary of stat values
    """
    query = """
        INSERT INTO team_game_stats (
            game_id, team_id,
            pts_total, pts_q1, pts_q2, pts_q3, pts_q4, pts_ot,
            td_pass, td_rush, td_ret, td_def,
            off_first_downs, off_total_yds, off_plays,
            off_3rd_att, off_3rd_make,
            off_redzone_att, off_redzone_td,
            off_possession_secs, def_sacks, def_int,
            total_turnovers, penalties_count, penalties_yds,
            metadata, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (game_id, team_id) DO UPDATE SET
            pts_total = EXCLUDED.pts_total,
            pts_q1 = EXCLUDED.pts_q1, pts_q2 = EXCLUDED.pts_q2,
            pts_q3 = EXCLUDED.pts_q3, pts_q4 = EXCLUDED.pts_q4, pts_ot = EXCLUDED.pts_ot,
            td_pass = EXCLUDED.td_pass, td_rush = EXCLUDED.td_rush,
            td_ret = EXCLUDED.td_ret, td_def = EXCLUDED.td_def,
            off_first_downs = EXCLUDED.off_first_downs,
            off_total_yds = EXCLUDED.off_total_yds, off_plays = EXCLUDED.off_plays,
            off_3rd_att = EXCLUDED.off_3rd_att, off_3rd_make = EXCLUDED.off_3rd_make,
            off_redzone_att = EXCLUDED.off_redzone_att, off_redzone_td = EXCLUDED.off_redzone_td,
            off_possession_secs = EXCLUDED.off_possession_secs,
            def_sacks = EXCLUDED.def_sacks, def_int = EXCLUDED.def_int,
            total_turnovers = EXCLUDED.total_turnovers,
            penalties_count = EXCLUDED.penalties_count, penalties_yds = EXCLUDED.penalties_yds,
            metadata = EXCLUDED.metadata
    """

    with conn.cursor() as cur:
        cur.execute(query, (
            game_id, team_id,
            stats.get("pts_total"), stats.get("pts_q1"), stats.get("pts_q2"),
            stats.get("pts_q3"), stats.get("pts_q4"), stats.get("pts_ot"),
            stats.get("td_pass"), stats.get("td_rush"), stats.get("td_ret"), stats.get("td_def"),
            stats.get("off_first_downs"), stats.get("off_total_yds"), stats.get("off_plays"),
            stats.get("off_3rd_make"), stats.get("off_3rd_att"),
            stats.get("off_redzone_td"), stats.get("off_redzone_att"),
            stats.get("off_possession_secs"), stats.get("def_sacks"), stats.get("def_int"),
            stats.get("total_turnovers"), stats.get("penalties_count"), stats.get("penalties_yds"),
            safe_jsonb(stats.get("metadata", {}))
        ))
        logger.debug(f"Inserted team stats for team_id={team_id}, game_id={game_id}")


def insert_player_stats(conn, player_id: int, game_id: int, stats: Dict[str, Any]):
    """
    Insert or update player game statistics.

    Args:
        conn: Database connection
        player_id: Player ID
        game_id: Game ID
        stats: Dictionary of stat values
    """
    query = """
        INSERT INTO player_game_stats (
            player_id, game_id,
            pass_comp, pass_att, pass_yds, pass_td, pass_int, pass_sacked,
            rush_att, rush_yds, rush_td,
            rec_receptions, rec_targets, rec_yds, rec_td,
            def_solo, def_ast, def_sacks, def_tfl, def_pd, def_qb_hits, def_td, def_int,
            ret_kick_no, ret_kick_yds, ret_kick_td,
            ret_punt_no, ret_punt_yds, ret_punt_td,
            k_fg_make, k_fg_att, k_xp_make, k_xp_att,
            p_no, p_yds, p_in20, p_tb, p_fc, p_blk, p_long,
            metadata, last_updated
        ) VALUES (
            %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (player_id, game_id) DO UPDATE SET
            pass_comp = EXCLUDED.pass_comp, pass_att = EXCLUDED.pass_att,
            pass_yds = EXCLUDED.pass_yds, pass_td = EXCLUDED.pass_td,
            pass_int = EXCLUDED.pass_int, pass_sacked = EXCLUDED.pass_sacked,
            rush_att = EXCLUDED.rush_att, rush_yds = EXCLUDED.rush_yds,
            rush_td = EXCLUDED.rush_td,
            rec_receptions = EXCLUDED.rec_receptions, rec_targets = EXCLUDED.rec_targets,
            rec_yds = EXCLUDED.rec_yds, rec_td = EXCLUDED.rec_td,
            def_solo = EXCLUDED.def_solo, def_ast = EXCLUDED.def_ast,
            def_sacks = EXCLUDED.def_sacks, def_tfl = EXCLUDED.def_tfl,
            def_pd = EXCLUDED.def_pd, def_qb_hits = EXCLUDED.def_qb_hits,
            def_td = EXCLUDED.def_td, def_int = EXCLUDED.def_int,
            ret_kick_no = EXCLUDED.ret_kick_no, ret_kick_yds = EXCLUDED.ret_kick_yds,
            ret_kick_td = EXCLUDED.ret_kick_td,
            ret_punt_no = EXCLUDED.ret_punt_no, ret_punt_yds = EXCLUDED.ret_punt_yds,
            ret_punt_td = EXCLUDED.ret_punt_td,
            k_fg_make = EXCLUDED.k_fg_make, k_fg_att = EXCLUDED.k_fg_att,
            k_xp_make = EXCLUDED.k_xp_make, k_xp_att = EXCLUDED.k_xp_att,
            p_no = EXCLUDED.p_no, p_yds = EXCLUDED.p_yds, p_in20 = EXCLUDED.p_in20,
            p_tb = EXCLUDED.p_tb, p_fc = EXCLUDED.p_fc, p_blk = EXCLUDED.p_blk,
            p_long = EXCLUDED.p_long,
            metadata = EXCLUDED.metadata
    """

    with conn.cursor() as cur:
        cur.execute(query, (
            player_id, game_id,
            stats.get("pass_comp"), stats.get("pass_att"), stats.get("pass_yds"),
            stats.get("pass_td"), stats.get("pass_int"), stats.get("pass_sacked"),
            stats.get("rush_att"), stats.get("rush_yds"), stats.get("rush_td"),
            stats.get("rec_receptions"), stats.get("rec_targets"), stats.get("rec_yds"),
            stats.get("rec_td"),
            stats.get("def_solo"), stats.get("def_ast"), stats.get("def_sacks"),
            stats.get("def_tfl"), stats.get("def_pd"), stats.get("def_qb_hits"),
            stats.get("def_td"), stats.get("def_int"),
            stats.get("ret_kick_no"), stats.get("ret_kick_yds"), stats.get("ret_kick_td"),
            stats.get("ret_punt_no"), stats.get("ret_punt_yds"), stats.get("ret_punt_td"),
            stats.get("k_fg_make"), stats.get("k_fg_att"), stats.get("k_xp_make"),
            stats.get("k_xp_att"),
            stats.get("p_no"), stats.get("p_yds"), stats.get("p_in20"),
            stats.get("p_tb"), stats.get("p_fc"), stats.get("p_blk"), stats.get("p_long"),
            safe_jsonb(stats.get("metadata", {}))
        ))
        logger.debug(f"Inserted player stats for player_id={player_id}, game_id={game_id}")


def parse_team_stats(boxscore: dict, team_data: dict) -> Dict[str, Any]:
    """
    Parse team statistics from ESPN boxscore.

    Args:
        boxscore: Full boxscore data
        team_data: Individual team data from boxscore.teams[]

    Returns:
        Dictionary of parsed stat values
    """
    stats = {}
    statistics = team_data.get("statistics", [])

    # Extract scoring
    scoring = team_data.get("score", "0")
    stats["pts_total"] = parse_int(scoring)

    # Parse possession time
    for stat in statistics:
        if isinstance(stat, dict) and stat.get("name") == "Possession":
            labels = stat.get("labels", [])
            values = stat.get("values", [])
            top_value = map_stat_by_label(labels, values, "TOP")
            if top_value:
                stats["off_possession_secs"] = parse_possession_time(top_value)

    # Parse third downs (format: "3/12")
    for stat in statistics:
        if isinstance(stat, dict) and "3rd" in stat.get("name", ""):
            labels = stat.get("labels", [])
            values = stat.get("values", [])
            td_value = map_stat_by_label(labels, values, "3RD DOWN")
            if td_value:
                make, att = parse_fraction(td_value)
                stats["off_3rd_make"] = make
                stats["off_3rd_att"] = att

    # Parse red zone
    for stat in statistics:
        if isinstance(stat, dict) and "Red" in stat.get("name", ""):
            labels = stat.get("labels", [])
            values = stat.get("values", [])
            rz_value = map_stat_by_label(labels, values, "RED ZONE")
            if rz_value:
                make, att = parse_fraction(rz_value)
                stats["off_redzone_td"] = make
                stats["off_redzone_att"] = att

    # Parse first downs
    for stat in statistics:
        if isinstance(stat, dict) and "1st" in stat.get("name", ""):
            labels = stat.get("labels", [])
            values = stat.get("values", [])
            fd_value = map_stat_by_label(labels, values, "FIRST DOWNS")
            if not fd_value:
                fd_value = map_stat_by_label(labels, values, "1ST Downs")
            if fd_value:
                stats["off_first_downs"] = parse_int(fd_value)

    # Parse total yards
    for stat in statistics:
        if isinstance(stat, dict) and "Total" in stat.get("name", ""):
            labels = stat.get("labels", [])
            values = stat.get("values", [])
            ty_value = map_stat_by_label(labels, values, "TOTAL YARDS")
            if not ty_value:
                ty_value = map_stat_by_label(labels, values, "TOT YDS")
            if ty_value:
                stats["off_total_yds"] = parse_int(ty_value)

    # Store remaining stats in metadata
    stats["metadata"] = {
        "raw_statistics": [str(s) for s in statistics]
    }

    return stats


def parse_player_stats(player_data: dict) -> Dict[str, Any]:
    """
    Parse player statistics from ESPN boxscore.

    Args:
        player_data: Player data from boxscore.players[]

    Returns:
        Dictionary of parsed stat values
    """
    stats = {}
    metadata = {}

    # ESPN stores player stats in categories
    stats_dict = player_data.get("stats", {})

    for category_name, category_data in stats_dict.items():
        if not isinstance(category_data, dict):
            continue

        category_lower = category_name.lower()
        labels = category_data.get("labels", [])
        values = category_data.get("values", [])

        if "pass" in category_lower:
            stats["pass_comp"] = parse_int(map_stat_by_label(labels, values, "CP"))
            stats["pass_att"] = parse_int(map_stat_by_label(labels, values, "ATT"))
            combined = map_stat_by_label(labels, values, "CP/ATT")
            if combined:
                comp, att = parse_fraction(combined)
                if comp:
                    stats["pass_comp"] = comp
                if att:
                    stats["pass_att"] = att
            stats["pass_yds"] = parse_int(map_stat_by_label(labels, values, "YDS"))
            stats["pass_td"] = parse_int(map_stat_by_label(labels, values, "TD"))
            stats["pass_int"] = parse_int(map_stat_by_label(labels, values, "INT"))
            stats["pass_sacked"] = parse_int(map_stat_by_label(labels, values, "SACK"))

        elif "rush" in category_lower:
            stats["rush_att"] = parse_int(map_stat_by_label(labels, values, "ATT"))
            stats["rush_yds"] = parse_int(map_stat_by_label(labels, values, "YDS"))
            stats["rush_td"] = parse_int(map_stat_by_label(labels, values, "TD"))

        elif "recv" in category_lower or "receiving" in category_lower:
            stats["rec_receptions"] = parse_int(map_stat_by_label(labels, values, "REC"))
            stats["rec_targets"] = parse_int(map_stat_by_label(labels, values, "TARGETS"))
            stats["rec_yds"] = parse_int(map_stat_by_label(labels, values, "YDS"))
            stats["rec_td"] = parse_int(map_stat_by_label(labels, values, "TD"))

        elif "def" in category_lower:
            stats["def_solo"] = parse_int(map_stat_by_label(labels, values, "SOLO"))
            stats["def_ast"] = parse_int(map_stat_by_label(labels, values, "AST"))
            stats["def_sacks"] = parse_sacks(map_stat_by_label(labels, values, "SACK"))
            stats["def_tfl"] = parse_int(map_stat_by_label(labels, values, "TFL"))
            stats["def_pd"] = parse_int(map_stat_by_label(labels, values, "PD"))
            stats["def_qb_hits"] = parse_int(map_stat_by_label(labels, values, "QB HTS"))
            stats["def_int"] = parse_int(map_stat_by_label(labels, values, "INT"))
            stats["def_td"] = parse_int(map_stat_by_label(labels, values, "TD"))

        elif "kick return" in category_lower:
            stats["ret_kick_no"] = parse_int(map_stat_by_label(labels, values, "NO"))
            stats["ret_kick_yds"] = parse_int(map_stat_by_label(labels, values, "YDS"))
            stats["ret_kick_td"] = parse_int(map_stat_by_label(labels, values, "TD"))

        elif "punt return" in category_lower:
            stats["ret_punt_no"] = parse_int(map_stat_by_label(labels, values, "NO"))
            stats["ret_punt_yds"] = parse_int(map_stat_by_label(labels, values, "YDS"))
            stats["ret_punt_td"] = parse_int(map_stat_by_label(labels, values, "TD"))

        elif "field goal" in category_lower or "kicking" in category_lower:
            stats["k_fg_make"] = parse_int(map_stat_by_label(labels, values, "FG"))
            fg_combined = map_stat_by_label(labels, values, "FG%")
            if fg_combined:
                fg_combined = map_stat_by_label(labels, values, "FIELD GOALS")
            stats["k_fg_att"] = parse_int(map_stat_by_label(labels, values, "FG ATT"))
            stats["k_xp_make"] = parse_int(map_stat_by_label(labels, values, "XP"))
            stats["k_xp_att"] = parse_int(map_stat_by_label(labels, values, "XP ATT"))

        elif "punt" in category_lower:
            stats["p_no"] = parse_int(map_stat_by_label(labels, values, "NO"))
            stats["p_yds"] = parse_int(map_stat_by_label(labels, values, "YDS"))
            stats["p_in20"] = parse_int(map_stat_by_label(labels, values, "IN 20"))
            stats["p_tb"] = parse_int(map_stat_by_label(labels, values, "TB"))
            stats["p_fc"] = parse_int(map_stat_by_label(labels, values, "FC"))
            stats["p_blk"] = parse_int(map_stat_by_label(labels, values, "BLK"))
            stats["p_long"] = parse_int(map_stat_by_label(labels, values, "LONG"))

        # Store raw category data in metadata
        metadata[f"raw_{category_lower}"] = {
            "labels": labels,
            "values": values
        }

    stats["metadata"] = metadata
    return stats


def process_game(conn, game_id: str):
    """
    Process a single game from ESPN API.

    Args:
        conn: Database connection
        game_id: ESPN event ID

    Returns:
        Database game ID or None if processing failed
    """
    logger.info(f"Processing game: {game_id}")

    # Fetch game data
    try:
        game_data = fetch_game_summary(game_id)
    except Exception as e:
        logger.error(f"Failed to fetch game {game_id}: {e}")
        return None

    boxscore = get_boxscore(game_data)
    header = get_game_info(game_data)

    if not boxscore or not header:
        logger.warning(f"No boxscore or header data for game {game_id}")
        return None

    # Extract team info
    teams_data = boxscore.get("teams", [])
    if len(teams_data) < 2:
        logger.warning(f"Invalid teams data for game {game_id}")
        return None

    # Get home and away teams
    home_team = teams_data[0]
    away_team = teams_data[1]

    # Upsert teams
    home_abbr = home_team.get("abbreviation", "")
    home_name = home_team.get("displayName", "")
    home_team_id = upsert_team(home_abbr, home_name)

    away_abbr = away_team.get("abbreviation", "")
    away_name = away_team.get("displayName", "")
    away_team_id = upsert_team(away_abbr, away_name)

    # Extract game metadata
    game_status = header.get("status", {}).get("type", {}).get("state", "unknown")
    game_datetime_str = header.get("date", "")

    try:
        game_datetime = datetime.fromisoformat(game_datetime_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        game_datetime = datetime.now()

    # Parse week and season
    season = header.get("season", {})
    season_year = season.get("year") if season else None
    week_num = season.get("type", {}).get("week") if season else None

    # Upsert game (procedure resolves home/away team UUIDs internally from ESPN IDs)
    db_game_id = upsert_game(
        espn_id=game_id,
        status=game_status,
        game_date=game_datetime,
        home_espn_id=home_team_id,
        away_espn_id=away_team_id,
        week=week_num,
        season_year=season_year
    )

    # Process team stats
    team_stats = [
        {"team_id": home_team_id, "team_data": home_team},
        {"team_id": away_team_id, "team_data": away_team},
    ]

    for ts in team_stats:
        parsed_stats = parse_team_stats(boxscore, ts["team_data"])
        insert_team_stats(conn, db_game_id, ts["team_id"], parsed_stats)

    # Process player stats
    players = boxscore.get("participants", [])
    for participant in players:
        athlete_data = participant.get("athlete", {})
        player_id = athlete_data.get("id")
        player_name = athlete_data.get("displayName", "")
        player_position = athlete_data.get("jersey", "UNK")

        # Get team for player
        team_id = None
        if participant.get("homeAway") == "home":
            team_id = home_team_id
        else:
            team_id = away_team_id

        if not player_id or not player_name:
            continue

        db_player_id = upsert_player(str(player_id), player_name, player_position, team_id)
        player_stats = parse_player_stats(athlete_data)

        # Only insert if player has any stats
        non_null_stats = {k: v for k, v in player_stats.items()
                         if v is not None and k != "metadata"}
        if non_null_stats:
            insert_player_stats(conn, db_player_id, db_game_id, player_stats)

    logger.info(f"Completed processing game {game_id}, inserted DB game_id={db_game_id}")
    return db_game_id


def run_ingestion(conn, game_ids: list):
    """
    Main ingestion entry point.

    Args:
        conn: Database connection
        game_ids: List of ESPN game IDs to process
    """
    processed = 0
    failed = 0

    for game_id in game_ids:
        try:
            db_id = process_game(conn, game_id)
            if db_id:
                processed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}")
            failed += 1

    logger.info(f"Ingestion complete: {processed} succeeded, {failed} failed")
    return processed, failed
