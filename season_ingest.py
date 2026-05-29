#!/usr/bin/env python3
"""
NFL Season Ingestion Script - Consolidated Single Script
Downloads full NFL season stats from ESPN APIs to PostgreSQL.

NOTE: This script uses ESPN's historical scoreboard endpoint with explicit
year, week, and type parameters to retrieve game IDs for completed seasons.
The public ESPN API may have limitations on historical data access - game IDs
are typically available only for the current/previous season within ESPN's
data retention window.

Usage:
    python season_ingest.py --season 2026      # Download 2026 season (when active)
    python season_ingest.py --counts            # Show table counts

Historical Data Note:
- The public ESPN API returns game data for active/current seasons only
- Past seasons (2024, 2025) may not be accessible via the public API
- When the 2026 season is active (Sept 2026-Jan 2027), use --season 2026

Requirements:
- ESPN API rate limit: 0.5s sleep between requests
- Historical endpoint: /scoreboard?dates={year}&week={week}&type={type}
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# API constants (ESPN uses http, not https for these endpoints)
SCOREBOARD_URL = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
SUMMARY_URL = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"

# Request headers (mimic browser)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

# Rate limit: sleep between requests (0.5 seconds as per requirements)
API_DELAY = 0.5


# ========================
# HISTORICAL SEASON DISCOVERY
# Use the FIXED-YEAR discovery strategy: dates=year&week=N&type=2|3
# ========================

def fetch_historical_scoreboard(year, week, type_id):
    """
    Fetch historical NFL scoreboard using ESPN's historical endpoint.

    Target URL: /scoreboard?dates={year}&week={week}&type={type}

    Args:
        year: Year string (e.g., "2024" or "2025")
        week: Week number (1-18 for regular season)
        type_id: Season type (2=Regular Season)

    Returns:
        JSON response from ESPN API
    """
    params = {
        "dates": year,
        "week": str(week),
        "type": str(type_id)
    }

    try:
        resp = requests.get(SCOREBOARD_URL, headers=HEADERS, params=params, timeout=30)

        # Handle 404/403 errors for weeks outside the API's historical window
        if resp.status_code in (403, 404):
            logger.debug(f"  Week {week}: API returned {resp.status_code} - skipping")
            return None

        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        # Handle specific HTTP errors for historical data windows
        if e.response is not None and e.response.status_code in (403, 404):
            logger.debug(f"  Week {week}: HTTP {e.response.status_code} - skipping")
        else:
            error_msg = str(e) if e else "Unknown error"
            logger.debug(f"  Week {week}: HTTP error - {error_msg}")
        return None
    except requests.RequestException as e:
        error_msg = str(e) if e else "Unknown error"
        logger.debug(f"  Week {week}: Request error - {error_msg}")
        return None
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        logger.debug(f"  Week {week}: Error - {error_msg}")
        return None


def fetch_game_summary(game_id):
    """Fetch detailed game summary from ESPN API.

    Args:
        game_id: ESPN event ID

    Returns:
        JSON response with game details, or None on error
    """
    url = f"{SUMMARY_URL}?event={game_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)

        # Handle non-JSON responses (API returns status codes for invalid game IDs)
        if resp.status_code == 200:
            data = resp.json()
            # Check if response is actually an error (status code as int)
            if isinstance(data, int):
                logger.debug(f"  Game {game_id}: API returned status code instead of data")
                return None
            return data
        else:
            logger.debug(f"  Game {game_id}: HTTP {resp.status_code} - skipping")
            return None
    except requests.exceptions.HTTPError as e:
        # Handle 404/403 for historical game IDs
        if e.response is not None and e.response.status_code in (403, 404):
            logger.debug(f"  Game {game_id}: HTTP {e.response.status_code} - skipping")
        else:
            error_msg = str(e) if e else "Unknown error"
            logger.debug(f"  Game {game_id}: HTTP error - {error_msg}")
        return None
    except (ValueError, requests.RequestException) as e:
        error_msg = str(e) if e else "Unknown error"
        logger.debug(f"  Game {game_id}: Request error - {error_msg}")
        return None
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        logger.debug(f"  Game {game_id}: Error - {error_msg}")
        return None


def extract_game_ids(scoreboard):
    """Extract game IDs from scoreboard events.

    Args:
        scoreboard: JSON response from fetch_scoreboard()

    Returns:
        List of game (event) IDs as strings
    """
    game_ids = []

    # ESPN API returns events at top level OR nested under leagues[0]
    # Try top-level events first
    if scoreboard.get("events"):
        for event in scoreboard["events"]:
            event_id = event.get("id")
            if event_id:
                game_ids.append(str(event_id))
        return game_ids

    # Fall back to nested events (if top-level is empty)
    for league in scoreboard.get("leagues", []):
        for event in league.get("events", []):
            event_id = event.get("id")
            if event_id:
                game_ids.append(str(event_id))

    return game_ids


# ========================
# TRANSFORMATION FUNCTIONS
# ========================

def parse_possession_time(mm_ss_str):
    """Convert possession time from MM:SS to total seconds."""
    if not mm_ss_str or not isinstance(mm_ss_str, str):
        return None
    try:
        parts = mm_ss_str.split(":")
        if len(parts) == 2:
            return (int(parts[0]) * 60) + int(parts[1])
    except (ValueError, AttributeError):
        pass
    return None


def parse_fraction(frac_str):
    """Parse fraction string like "5/12" or "4-12" into (make, attempt)."""
    if not frac_str or not isinstance(frac_str, str):
        return (None, None)
    try:
        # ESPN uses both / and - as fraction separators
        if "/" in frac_str:
            parts = frac_str.split("/")
        elif "-" in frac_str:
            parts = frac_str.split("-")
        else:
            return (None, None)
        if len(parts) == 2:
            return (int(parts[0]), int(parts[1]))
    except (ValueError, AttributeError):
        pass
    return (None, None)


def map_stat_by_label(labels, stats, target_label):
    """Find stat value by matching label index in ESPN's stat arrays."""
    if not labels or not stats or not target_label:
        return None
    try:
        target_upper = target_label.upper()
        for i, label in enumerate(labels):
            if label and isinstance(label, str) and label.upper() == target_upper:
                return stats[i]
    except (AttributeError, TypeError):
        pass
    return None


def parse_sacks(sack_str):
    """Parse sack value handling half-sacks."""
    if not sack_str or not isinstance(sack_str, str):
        return None
    try:
        return float(sack_str)
    except ValueError:
        return None


def parse_int_safe(s):
    """Safely parse integer from string."""
    if not s or not isinstance(s, str):
        return None
    try:
        return int(s)
    except ValueError:
        return None


# ========================
# DATABASE FUNCTIONS
# ========================

def get_connection():
    """Create and return PostgreSQL connection."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "nfl_fantasy"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "owenethanTKD"),
            port=int(os.getenv("DB_PORT", "5432"))
        )
        logger.debug(f"Connected to {os.getenv('DB_NAME', 'nfl_fantasy')}")
        return conn
    except psycopg2.Error as e:
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Database connection error: {error_msg}")
        raise


def get_or_create_by_unique(select_query, insert_query, select_params, insert_params):
    """Generic upsert for tables with unique constraints."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(select_query, select_params)
            result = cur.fetchone()

            if result:
                logger.debug(f"Found existing record with id: {result['id']}")
                return result['id']

            cur.execute(insert_query, insert_params)
            conn.commit()
            new_id = cur.fetchone()['id']
            logger.debug(f"Created new record with id: {new_id}")
            return new_id
    except psycopg2.Error as e:
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Upsert error: {error_msg}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


# ========================
# DIMENSION UPSERTS
# ========================

def upsert_team(abbr, full_name):
    """Upsert a team into the database."""
    select = "SELECT id FROM teams WHERE abbr = %s"
    insert = "INSERT INTO teams (abbr, full_name) VALUES (%s, %s) RETURNING id"
    return get_or_create_by_unique(select, insert, (abbr,), (abbr, full_name))


def upsert_player(external_id, name, position, team_id):
    """Upsert a player into the database."""
    select = "SELECT id FROM players WHERE external_id = %s"
    insert = "INSERT INTO players (external_id, name, position, team_id) VALUES (%s, %s, %s, %s) RETURNING id"
    return get_or_create_by_unique(select, insert, (external_id,),
                                   (external_id, name, position, team_id))


def upsert_game(espn_id, status, game_date, home_espn_id, away_espn_id, week=None, season_year=None):
    """Upsert a game into the database."""
    select = "SELECT id FROM games WHERE espn_id = %s"
    insert = "INSERT INTO games (espn_id, status, game_date, home_espn_id, away_espn_id, week, season_year) " \
             "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id"
    return get_or_create_by_unique(select, insert, (espn_id,),
                                   (espn_id, status, game_date, home_team_id, away_team_id, week, season_year))


# ========================
# FACT TABLE INSERTS
# ========================

def insert_team_stats(conn, game_id, team_id, stats):
    """Insert team game statistics."""
    query = """
        INSERT INTO team_game_stats (
            game_id, team_id, pts_total, pts_q1, pts_q2, pts_q3, pts_q4, pts_ot,
            td_pass, td_rush, td_ret, td_def, off_first_downs, off_total_yds, off_plays,
            off_3rd_att, off_3rd_make, off_redzone_att, off_redzone_td, off_possession_secs,
            def_sacks, def_int, total_turnovers, penalties_count, penalties_yds, metadata
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s,
            %s
        )
        ON CONFLICT (game_id, team_id) DO UPDATE SET
            pts_total = EXCLUDED.pts_total, pts_q1 = EXCLUDED.pts_q1, pts_q2 = EXCLUDED.pts_q2,
            pts_q3 = EXCLUDED.pts_q3, pts_q4 = EXCLUDED.pts_q4, pts_ot = EXCLUDED.pts_ot,
            td_pass = EXCLUDED.td_pass, td_rush = EXCLUDED.td_rush, td_ret = EXCLUDED.td_ret, td_def = EXCLUDED.td_def,
            off_first_downs = EXCLUDED.off_first_downs, off_total_yds = EXCLUDED.off_total_yds, off_plays = EXCLUDED.off_plays,
            off_3rd_att = EXCLUDED.off_3rd_att, off_3rd_make = EXCLUDED.off_3rd_make,
            off_redzone_att = EXCLUDED.off_redzone_att, off_redzone_td = EXCLUDED.off_redzone_td,
            off_possession_secs = EXCLUDED.off_possession_secs, def_sacks = EXCLUDED.def_sacks,
            def_int = EXCLUDED.def_int, total_turnovers = EXCLUDED.total_turnovers,
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
        logger.debug(f"Inserted team stats: team_id={team_id}, game_id={game_id}")


def insert_player_stats(conn, player_id, game_id, stats):
    """Insert player game statistics."""
    query = """
        INSERT INTO player_game_stats (
            player_id, game_id,
            pass_comp, pass_att, pass_yds, pass_td, pass_int, pass_sacked,
            rush_att, rush_yds, rush_td,
            rec_receptions, rec_targets, rec_yds, rec_td,
            def_solo, def_ast, def_sacks, def_tfl, def_pd, def_qb_hits, def_td, def_int,
            ret_kick_no, ret_kick_yds, ret_kick_td, ret_punt_no, ret_punt_yds, ret_punt_td,
            k_fg_make, k_fg_att, k_xp_make, k_xp_att,
            p_no, p_yds, p_in20, p_tb, p_fc, p_blk, p_long, metadata
        ) VALUES (
            %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s
        )
        ON CONFLICT (player_id, game_id) DO UPDATE SET
            pass_comp = EXCLUDED.pass_comp, pass_att = EXCLUDED.pass_att,
            pass_yds = EXCLUDED.pass_yds, pass_td = EXCLUDED.pass_td, pass_int = EXCLUDED.pass_int,
            pass_sacked = EXCLUDED.pass_sacked, rush_att = EXCLUDED.rush_att, rush_yds = EXCLUDED.rush_yds,
            rush_td = EXCLUDED.rush_td, rec_receptions = EXCLUDED.rec_receptions, rec_targets = EXCLUDED.rec_targets,
            rec_yds = EXCLUDED.rec_yds, rec_td = EXCLUDED.rec_td,
            def_solo = EXCLUDED.def_solo, def_ast = EXCLUDED.def_ast, def_sacks = EXCLUDED.def_sacks,
            def_tfl = EXCLUDED.def_tfl, def_pd = EXCLUDED.def_pd, def_qb_hits = EXCLUDED.def_qb_hits,
            def_td = EXCLUDED.def_td, def_int = EXCLUDED.def_int,
            ret_kick_no = EXCLUDED.ret_kick_no, ret_kick_yds = EXCLUDED.ret_kick_yds, ret_kick_td = EXCLUDED.ret_kick_td,
            ret_punt_no = EXCLUDED.ret_punt_no, ret_punt_yds = EXCLUDED.ret_punt_yds, ret_punt_td = EXCLUDED.ret_punt_td,
            k_fg_make = EXCLUDED.k_fg_make, k_fg_att = EXCLUDED.k_fg_att, k_xp_make = EXCLUDED.k_xp_make, k_xp_att = EXCLUDED.k_xp_att,
            p_no = EXCLUDED.p_no, p_yds = EXCLUDED.p_yds, p_in20 = EXCLUDED.p_in20,
            p_tb = EXCLUDED.p_tb, p_fc = EXCLUDED.p_fc, p_blk = EXCLUDED.p_blk, p_long = EXCLUDED.p_long,
            metadata = EXCLUDED.metadata
    """
    with conn.cursor() as cur:
        cur.execute(query, (
            player_id, game_id,
            stats.get("pass_comp"), stats.get("pass_att"), stats.get("pass_yds"),
            stats.get("pass_td"), stats.get("pass_int"), stats.get("pass_sacked"),
            stats.get("rush_att"), stats.get("rush_yds"), stats.get("rush_td"),
            stats.get("rec_receptions"), stats.get("rec_targets"), stats.get("rec_yds"), stats.get("rec_td"),
            stats.get("def_solo"), stats.get("def_ast"), stats.get("def_sacks"), stats.get("def_tfl"),
            stats.get("def_pd"), stats.get("def_qb_hits"), stats.get("def_td"), stats.get("def_int"),
            stats.get("ret_kick_no"), stats.get("ret_kick_yds"), stats.get("ret_kick_td"),
            stats.get("ret_punt_no"), stats.get("ret_punt_yds"), stats.get("ret_punt_td"),
            stats.get("k_fg_make"), stats.get("k_fg_att"), stats.get("k_xp_make"), stats.get("k_xp_att"),
            stats.get("p_no"), stats.get("p_yds"), stats.get("p_in20"),
            stats.get("p_tb"), stats.get("p_fc"), stats.get("p_blk"),
            stats.get("p_long"),
            safe_jsonb(stats.get("metadata", {}))
        ))
        logger.debug(f"Inserted player stats: player_id={player_id}, game_id={game_id}")


# ========================
# HELPER FUNCTIONS
# ========================

def safe_jsonb(data):
    """Clean dictionary for JSONB storage. Returns JSON string."""
    if not data:
        return '{}'
    result = {}
    for key, value in data.items():
        if value is not None and isinstance(value, (str, int, float, bool, list, dict)):
            result[key] = value
        else:
            result[key] = str(value)
    return json.dumps(result)


# ========================
# STAT PARSING
# ========================

def parse_team_stats(team_data):
    """Parse team statistics from ESPN boxscore.

    The summary API returns team stats as objects with name/displayValue/value fields,
    NOT as labels/values arrays.
    """
    stats = {}
    statistics = team_data.get("statistics", [])

    # Scoring
    stats["pts_total"] = parse_int_safe(team_data.get("score", "0"))

    for stat in statistics:
        if not isinstance(stat, dict):
            continue
        name = stat.get("name", "")
        display_value = stat.get("displayValue", "")
        value = stat.get("value")

        if name == "possessionTime":
            # displayValue is like "23:52", value is already seconds (1432)
            if display_value:
                stats["off_possession_secs"] = parse_possession_time(display_value)
            elif isinstance(value, (int, float)) and value != "-":
                stats["off_possession_secs"] = int(value)

        elif "third" in name.lower():
            # displayValue like "4-12"
            if display_value:
                make, att = parse_fraction(display_value)
                stats["off_3rd_make"] = make
                stats["off_3rd_att"] = att

        elif name == "redZoneAttempts":
            # displayValue like "2-3"
            if display_value:
                make, att = parse_fraction(display_value)
                stats["off_redzone_td"] = make
                stats["off_redzone_att"] = att

        elif name == "firstDowns":
            if value is not None and value != "-":
                stats["off_first_downs"] = parse_int_safe(str(int(value)))

        elif name == "totalYards":
            # value may be "-" string, fall back to displayValue
            yds_val = display_value if display_value and display_value != "-" else None
            stats["off_total_yds"] = parse_int_safe(yds_val)

        elif name == "totalOffensivePlays":
            if value is not None and value != "-":
                stats["off_plays"] = parse_int_safe(str(int(value)))

        elif name == "totalPenaltiesYards":
            # displayValue like "6-46" means "6 penalties for 46 yards"
            if display_value and "-" in display_value:
                parts = display_value.split("-")
                if len(parts) == 2:
                    stats["penalties_count"] = parse_int_safe(parts[0])
                    stats["penalties_yds"] = parse_int_safe(parts[1])

    # Store raw statistics in metadata
    stats["metadata"] = {"raw_statistics": [str(s) for s in statistics]}

    return stats


def parse_player_stats(stat_categories):
    """Parse player statistics from ESPN boxscore.

    stat_categories is the list of stat category objects from a team's boxscore.players entry.
    Each category has: name, labels (array), athletes (array of {athlete, stats}).

    We iterate per-stat-category, and for each athlete within that category,
    we build stats using the labels and their athlete's stats array.
    Returns: list of (athlete_info, stats_dict) tuples.
    """
    results = []

    if not isinstance(stat_categories, list):
        return results

    for category in stat_categories:
        if not isinstance(category, dict):
            continue

        category_name = category.get("name", "")
        category_lower = category_name.lower()
        labels = category.get("labels", [])
        athletes = category.get("athletes", [])

        if not athletes:
            # No individual athlete data for this category (e.g., fumbles team totals only)
            continue

        for ath_entry in athletes:
            if not isinstance(ath_entry, dict):
                continue
            athlete = ath_entry.get("athlete", {})
            ath_stats = ath_entry.get("stats", [])

            ath_id = athlete.get("id")
            ath_name = athlete.get("displayName", "")
            ath_display = athlete.get("displayName", "")
            ath_jersey = athlete.get("jersey", "UNK")
            ath_position = athlete.get("position", {}).get("displayName", "UNK") if isinstance(athlete.get("position"), dict) else athlete.get("position", "UNK")

            stats = {}
            player_metadata = {}

            # Mapping from category name to stat fields
            if ath_stats and isinstance(ath_stats, list) and labels and isinstance(labels, list):
                # Build a dict of label -> stat_value for this athlete
                stat_map = {}
                for j, label in enumerate(labels):
                    if j < len(ath_stats):
                        stat_map[label] = ath_stats[j]

                if "pass" in category_lower:
                    # Labels: ['C/ATT', 'YDS', 'AVG', 'TD', 'INT', 'SACKS', 'QBR', 'RTG']
                    ca = stat_map.get("C/ATT", "")
                    if ca:
                        comp, att = parse_fraction(ca)
                        stats["pass_comp"] = comp
                        stats["pass_att"] = att
                    stats["pass_yds"] = parse_int_safe(stat_map.get("YDS"))
                    stats["pass_td"] = parse_int_safe(stat_map.get("TD"))
                    stats["pass_int"] = parse_int_safe(stat_map.get("INT"))
                    sacks_str = stat_map.get("SACKS", "")
                    if sacks_str and sacks_str != "-":
                        if isinstance(sacks_str, str) and "-" in sacks_str:
                            # "3-16" -> use first part for sack count
                            stats["pass_sacked"] = parse_int_safe(sacks_str.split("-")[0])
                        else:
                            stats["pass_sacked"] = parse_int_safe(sacks_str)

                elif "rush" in category_lower:
                    # Labels: ['CAR', 'YDS', 'AVG', 'TD', 'LONG']
                    stats["rush_att"] = parse_int_safe(stat_map.get("CAR"))
                    stats["rush_yds"] = parse_int_safe(stat_map.get("YDS"))
                    stats["rush_td"] = parse_int_safe(stat_map.get("TD"))

                elif "recv" in category_lower or "receiving" in category_lower:
                    # Labels: ['REC', 'YDS', 'AVG', 'TD', 'LONG', 'TGTS']
                    stats["rec_receptions"] = parse_int_safe(stat_map.get("REC"))
                    stats["rec_targets"] = parse_int_safe(stat_map.get("TGTS"))
                    stats["rec_yds"] = parse_int_safe(stat_map.get("YDS"))
                    stats["rec_td"] = parse_int_safe(stat_map.get("TD"))

                elif "def" in category_lower:
                    # Labels: ['TOT', 'SOLO', 'SACKS', 'TFL', 'PD', 'QB HTS', 'TD']
                    solo = parse_int_safe(stat_map.get("SOLO"))
                    tot = parse_int_safe(stat_map.get("TOT"))
                    # def_ast = TOT - SOLO (assists = total - solo)
                    stats["def_solo"] = solo
                    stats["def_ast"] = (tot - solo) if (tot is not None and solo is not None) else None
                    stats["def_sacks"] = parse_sacks(stat_map.get("SACKS"))
                    stats["def_tfl"] = parse_int_safe(stat_map.get("TFL"))
                    stats["def_pd"] = parse_int_safe(stat_map.get("PD"))
                    stats["def_qb_hits"] = parse_int_safe(stat_map.get("QB HTS"))
                    stats["def_int"] = parse_int_safe(stat_map.get("INT")) if "INT" in stat_map else None
                    stats["def_td"] = parse_int_safe(stat_map.get("TD"))

                elif "kick return" in category_lower:
                    # Labels: ['NO', 'YDS', 'AVG', 'LONG', 'TD']
                    stats["ret_kick_no"] = parse_int_safe(stat_map.get("NO"))
                    stats["ret_kick_yds"] = parse_int_safe(stat_map.get("YDS"))
                    stats["ret_kick_td"] = parse_int_safe(stat_map.get("TD"))

                elif "punt return" in category_lower:
                    # Labels: ['NO', 'YDS', 'AVG', 'LONG', 'TD']
                    stats["ret_punt_no"] = parse_int_safe(stat_map.get("NO"))
                    stats["ret_punt_yds"] = parse_int_safe(stat_map.get("YDS"))
                    stats["ret_punt_td"] = parse_int_safe(stat_map.get("TD"))

                elif "kick" in category_lower or "field goal" in category_lower:
                    # Labels: ['FG', 'PCT', 'LONG', 'XP', 'PTS']
                    fg = stat_map.get("FG", "")
                    if fg and "-" in fg:
                        fg_make, fg_att = parse_fraction(fg)
                        stats["k_fg_make"] = fg_make
                        stats["k_fg_att"] = fg_att
                    else:
                        stats["k_fg_make"] = parse_int_safe(fg)
                        stats["k_fg_att"] = None
                    xp = stat_map.get("XP", "")
                    if xp and "-" in xp:
                        xp_make, xp_att = parse_fraction(xp)
                        stats["k_xp_make"] = xp_make
                        stats["k_xp_att"] = xp_att
                    else:
                        stats["k_xp_make"] = parse_int_safe(xp)
                        stats["k_xp_att"] = None

                elif "punt" in category_lower:
                    # Labels: ['NO', 'YDS', 'AVG', 'TB', 'In 20', 'LONG']
                    stats["p_no"] = parse_int_safe(stat_map.get("NO"))
                    stats["p_yds"] = parse_int_safe(stat_map.get("YDS"))
                    stats["p_in20"] = parse_int_safe(stat_map.get("In 20"))
                    stats["p_tb"] = parse_int_safe(stat_map.get("TB"))

                # Store raw data for this category
                player_metadata[f"raw_{category_lower}"] = {
                    "labels": labels,
                    "stats": ath_stats
                }

            if ath_id and ath_name:
                results.append({
                    "player_id": str(ath_id),
                    "player_name": ath_display,
                    "player_position": ath_position,
                    "stats": stats,
                    "metadata": player_metadata,
                })

    return results


# ========================
# GAME PROCESSING
# ========================

def process_game(conn, game_id):
    """Process a single game from ESPN API.

    Args:
        conn: Database connection
        game_id: ESPN event ID

    Returns:
        Database game ID or None if processing failed
    """
    logger.info(f"Processing game: {game_id}")

    try:
        # Fetch game data
        game_data = fetch_game_summary(game_id)

        if game_data is None:
            logger.debug(f"Game {game_id}: Summary API returned no data - skipping")
            return None

        boxscore = game_data.get("boxscore")
        header = game_data.get("header")

        if not boxscore or not header:
            logger.warning(f"No boxscore/header data for game {game_id}")
            return None

        # Extract competition info from header
        competitions = header.get("competitions", [])
        if not competitions:
            logger.warning(f"No competitions data for game {game_id}")
            return None

        competition = competitions[0]
        competitors = competition.get("competitors", [])
        if len(competitors) < 2:
            logger.warning(f"Invalid competitors data for game {game_id}")
            return None

        # Identify home/away teams from competitors
        home_competitor = None
        away_competitor = None
        for c in competitors:
            if c.get("homeAway") == "home":
                home_competitor = c
            else:
                away_competitor = c

        if not home_competitor or not away_competitor:
            home_competitor = competitors[0]
            away_competitor = competitors[1]

        home_team_data = home_competitor.get("team", {})
        away_team_data = away_competitor.get("team", {})

        # Upsert teams
        home_team_id = upsert_team(
            home_team_data.get("abbreviation", ""),
            home_team_data.get("displayName", "")
        )
        away_team_id = upsert_team(
            away_team_data.get("abbreviation", ""),
            away_team_data.get("displayName", "")
        )

        # Extract game metadata from header
        game_status = competition.get("status", {}).get("type", {}).get("state", "unknown")
        game_datetime_str = competition.get("date", "")

        try:
            game_datetime = datetime.fromisoformat(game_datetime_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            game_datetime = datetime.now()

        # Parse week and season from header
        season_info = header.get("season", {})
        season_year = season_info.get("year") if season_info else None
        week_num = header.get("week") or (season_info.get("type", {}).get("week") if season_info else None)

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

        # Process team stats from boxscore.teams
        teams_data = boxscore.get("teams", [])
        if len(teams_data) >= 2:
            for team in teams_data:
                home_away = team.get("homeAway", "")
                team_id = home_team_id if home_away == "home" else away_team_id
                # Find matching competitor for score
                if home_away == "home":
                    team_score = home_competitor.get("score", "0")
                else:
                    team_score = away_competitor.get("score", "0")
                team_data_with_score = {**team, "score": team_score}
                parsed_stats = parse_team_stats(team_data_with_score)
                insert_team_stats(conn, db_game_id, team_id, parsed_stats)

        # Process player stats from boxscore.players
        # boxscore.players is a list of per-team entries, each with statistics categories
        # Each stat category contains athletes with individual stats
        players_data = boxscore.get("players", [])
        home_athlete_count = 0
        away_athlete_count = 0

        for team_entry in players_data:
            team_info = team_entry.get("team", {})
            statistics = team_entry.get("statistics", [])

            # Determine team for this entry's players
            team_name = team_info.get("displayName", "")
            player_team_id = None
            if team_name == home_competitor.get("team", {}).get("displayName", ""):
                player_team_id = home_team_id
            else:
                player_team_id = away_team_id

            # Parse all stat categories to get individual player stats
            player_results = parse_player_stats(statistics)

            for pr in player_results:
                p_id = pr["player_id"]
                p_name = pr["player_name"]
                p_pos = pr["player_position"]
                p_stats = pr["stats"]
                p_metadata = pr["metadata"]

                if not p_id or not p_name:
                    continue

                db_player_id = upsert_player(p_id, p_name, p_pos, player_team_id)

                # Only insert if player has stats
                non_null_stats = {k: v for k, v in p_stats.items() if v is not None and k != "metadata"}
                if non_null_stats:
                    insert_player_stats(conn, db_player_id, db_game_id, p_stats)

                if player_team_id == home_team_id:
                    home_athlete_count += 1
                else:
                    away_athlete_count += 1

        conn.commit()
        logger.info(f"Completed processing game {game_id}, DB game_id={db_game_id} (home_athletes={home_athlete_count}, away_athletes={away_athlete_count})")
        return db_game_id

    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Error processing game {game_id}: {error_msg}")
        import traceback
        traceback.print_exc()
        return None


# ========================
# HISTORICAL SEASON GAME COLLECTION
# ========================


# ========================
# HISTORICAL SEASON GAME COLLECTION
# Uses the historical endpoint with explicit parameters:
# /scoreboard?dates={year}&week={week}&type={type}
# ========================

def get_season_games(year):
    """
    Fetch all game IDs for a given NFL season using the historical endpoint.

    Uses ESPN's historical endpoint with explicit year, week, and type parameters:
    /scoreboard?dates={year}&week={week}&type={type}

    Args:
        year: Year string (e.g., "2024" or "2025")
        season_types: List of (type_id, season_type_name) tuples
                     Default: [(2, "Regular"), (3, "Playoffs")]

    Returns:
        Sorted list of game IDs
    """
    year = str(year)
    logger.info(f"Fetching games for year={year} (Regular Season)")

    game_ids = set()
    week = 1
    max_weeks = 18  # Regular season weeks (Week 1-18)

    # Fetch Regular Season only (type=2)
    while week <= max_weeks:
        try:
            # Use the historical endpoint with explicit parameters
            scoreboard = fetch_historical_scoreboard(year, week, type_id=2)
            found_ids = extract_game_ids(scoreboard)
            if found_ids:
                logger.debug(f"  Week {week}: found {len(found_ids)} game(s)")
                game_ids.update(found_ids)
            else:
                logger.debug(f"  Week {week}: no games found")
        except requests.exceptions.HTTPError as e:
            # Handle 404/403 errors for weeks outside the current season window
            logger.debug(f"  Week {week}: HTTP {e.response.status_code} - skipped")
        except Exception as e:
            # Skip weeks with API errors (often happens for weeks before season starts)
            logger.debug(f"  Week {week}: skipped - {type(e).__name__}")

        week += 1

    return sorted(game_ids)



# ========================
# MAIN ENTRY POINT
# ========================

def process_game_batch(conn, game_ids):
    """Process a batch of games with delay between requests."""
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
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"Error processing game {game_id}: {error_msg}")
            failed += 1

        # Respect API rate limits
        time.sleep(API_DELAY)

    logger.info(f"Ingestion complete: {processed} succeeded, {failed} failed")
    return processed, failed


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="NFL Historical Season Ingestion Script - Downloads completed NFL seasons from ESPN APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download entire 2025 season (Regular Season only)
  python season_ingest.py --season 2025

  # Download both Regular Season and Playoffs
  python season_ingest.py --season 2025 --include-playoffs

  # Download a specific year
  python season_ingest.py --year 2024

  # Show database counts
  python season_ingest.py --counts

  # Show help
  python season_ingest.py --help

Historical Discovery Notes:
  - Uses: /scoreboard?dates={year}&week={week}&type={type}
  - Regular Season: type=2
  - Playoffs: type=3
  - Weeks: 1-18 (Regular), varies for Playoffs
        """
    )

    parser.add_argument("--season", "-s", type=str, help="Download entire season (year, e.g., 2025)")
    parser.add_argument("--year", "-y", type=str, help="Custom year to download")
    parser.add_argument("--game-id", "-g", type=str, help="Single ESPN game/event ID to process")
    parser.add_argument("--date", "-d", type=str, help="Date in YYYY-MM-DD format")
    parser.add_argument("--include-playoffs", action="store_true", help="Include playoffs in download")
    parser.add_argument("--counts", "-c", action="store_true", help="Show database table counts")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress INFO logging")
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging")

    args = parser.parse_args()

    # Adjust logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle --counts only
    if args.counts:
        logger.info("Fetching database counts...")
        try:
            conn = get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
                rows = cur.fetchall()
                tables = [row['table_name'] for row in rows]
                logger.info("Database tables: " + ", ".join(tables))
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cur.fetchone()
                    if result:
                        logger.info(f"  {table}: {result['count']}")
            conn.close()
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"Failed to connect to database: {error_msg}")
            sys.exit(1)
        return

    # Collect game IDs to process
    game_ids = []

    if args.season:
        game_ids = get_season_games(args.season)
    elif args.year:
        game_ids = get_season_games(args.year)
    elif args.game_id:
        game_ids = [args.game_id]
    elif args.date:
        try:
            scoreboard = fetch_scoreboard(args.date)
            game_ids = extract_game_ids(scoreboard)
            if not game_ids:
                logger.warning(f"No games found for date {args.date}")
                return
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"Failed to fetch scoreboard for date {args.date}: {error_msg}")
            sys.exit(1)
    else:
        parser.print_help()
        logger.info("\nPlease specify --season, --year, --game-id, or --date")
        return

    if not game_ids:
        logger.warning("No games found")
        return

    logger.info(f"Processing {len(game_ids)} game(s)...")

    # Run ingestion
    try:
        conn = get_connection()

        processed, failed = process_game_batch(conn, game_ids)

        # Show final counts
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
            rows = cur.fetchall()
            tables = [row['table_name'] for row in rows]
            for table in tables:
                cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cur.fetchone()
                if result:
                    logger.info(f"  {table}: {result['count']}")

        conn.close()

        if failed > 0:
            logger.warning(f"Some games failed: {failed}")

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Ingestion failed: {error_msg}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
