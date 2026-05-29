#!/usr/bin/env python3
"""
NFL Fantasy Football Database - Main Entry Point

Usage:
    python run.py --help
    python run.py --game-id 401500000000
    python run.py --date 2025-09-04
    python run.py --scoreboard
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta

from database import get_connection
from espn_api import fetch_scoreboard, extract_game_ids
from ingestion import run_ingestion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def log_table_counts(conn):
    """Log row counts for all tables."""
    from database import execute_query

    tables = ["teams", "players", "games", "team_game_stats", "player_game_stats"]
    counts = {}

    for table in tables:
        result = execute_query(f"SELECT COUNT(*) as count FROM {table}", fetch=True)
        if result:
            counts[table] = result[0]["count"]

    logger.info("Database table counts:")
    for table, count in counts.items():
        logger.info(f"  {table}: {count}")

    return counts


def _get_season_games(season_year: str) -> list:
    """
    Fetch all game IDs for a given NFL season.

    Args:
        season_year: Year string (e.g., "2025")

    Returns:
        List of game IDs for the season

    The NFL regular season is 17 weeks:
        - Week 1: ~September 4
        - Week 18: ~January 6 (or January 11 for playoffs)
    """
    from datetime import datetime

    season_year = int(season_year)
    # NFL season starts in the year before the season number
    # e.g., 2025 season starts Sept 2025, 2026 season starts Sept 2026
    calendar_year = season_year

    logger.info(f"Fetching games for {season_year} NFL season ({calendar_year} calendar year)")

    game_ids = set()
    week = 1
    current_date = datetime(calendar_year, 9, 4)  # NFL season typically starts week 1 in early Sept

    max_weeks = 18  # Regular season weeks

    while week <= max_weeks:
        # Poll this date for games
        date_str = current_date.strftime("%Y-%m-%d")
        try:
            scoreboard = fetch_scoreboard(date_str)
            game_ids.update(extract_game_ids(scoreboard))
        except Exception:
            # Skip this date if no games or API error
            pass

        # Move to next week
        current_date += timedelta(days=7)
        week += 1

        # Stop after max weeks
        if week > max_weeks:
            break

    # Remove duplicates
    return sorted(game_ids)


def main():
    parser = argparse.ArgumentParser(
        description="NFL Fantasy Football Database - ESPN API Ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single game by ESPN ID
  python run.py --game-id 401500000000

  # Process all games from a specific date
  python run.py --date 2025-09-04

  # Fetch and process all games from the scoreboard
  python run.py --scoreboard

  # Show database counts (no ingestion)
  python run.py --counts
        """
    )

    parser.add_argument(
        "--game-id", "-g",
        type=str,
        help="Single ESPN game/event ID to process"
    )

    parser.add_argument(
        "--date", "-d",
        type=str,
        help="Date in YYYY-MM-DD format to fetch games for"
    )

    parser.add_argument(
        "--scoreboard", "-s",
        action="store_true",
        help="Fetch all games from ESPN scoreboard"
    )

    parser.add_argument(
        "--season",
        type=str,
        help="Process entire season (e.g., 2025 for 2025 regular season)"
    )

    parser.add_argument(
        "--counts", "-c",
        action="store_true",
        help="Show database table counts without ingestion"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress INFO logging"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG logging"
    )

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
            counts = log_table_counts(conn)
            conn.close()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            sys.exit(1)

        return

    # Handle --season: process entire season
    if args.season:
        logger.info(f"Processing entire {args.season} season")
        game_ids = _get_season_games(args.season)
    else:
    # Determine game IDs to process
        game_ids = []

        if args.game_id:
            game_ids = [args.game_id]
        elif args.date:
            logger.info(f"Fetching scoreboard for date: {args.date}")
            try:
                scoreboard = fetch_scoreboard(args.date)
                game_ids = extract_game_ids(scoreboard)
                if not game_ids:
                    logger.warning("No games found for this date")
                    return
            except Exception as e:
                logger.error(f"Failed to fetch scoreboard: {e}")
                sys.exit(1)
        elif args.scoreboard:
            logger.info("Fetching current scoreboard...")
            try:
                scoreboard = fetch_scoreboard()
                game_ids = extract_game_ids(scoreboard)
                if not game_ids:
                    logger.warning("No games found in scoreboard")
                    return
            except Exception as e:
                logger.error(f"Failed to fetch scoreboard: {e}")
                sys.exit(1)
        else:
            parser.print_help()
            logger.info("\nPlease specify a game ID, date, season, or --scoreboard")
            return

    logger.info(f"Processing {len(game_ids)} game(s): {', '.join(game_ids[:5])}{'...' if len(game_ids) > 5 else ''}")

    # Run ingestion
    try:
        conn = get_connection()

        logger.info("Starting ingestion...")
        start_time = datetime.now()

        processed, failed = run_ingestion(conn, game_ids)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Completed in {elapsed:.2f} seconds")

        # Log final counts
        log_table_counts(conn)

        conn.close()

        if failed > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
