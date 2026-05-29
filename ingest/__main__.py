#!/usr/bin/env python3
"""NFL Fantasy Football Database - CLI Entry Point

Usage:
    python -m ingest --game-id <id>
    python -m ingest --date <YYYY-MM-DD>
    python -m ingest --week <year> <week>
    python -m ingest --season <year> [--include-playoffs]
    python -m ingest --counts
    python -m ingest --service
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime

from ingest.espn.client import ESPNClient
from ingest.espn.transformer import ESPNTransformer
from ingest.engine import IngestionEngine
from ingest.db_writer import PgDBWriter
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def _log_counts():
    """Show database table counts."""
    from ingest.db_writer import PgDBWriter
    writer = PgDBWriter()
    tables = ["teams", "players", "games", "team_game_stats", "player_game_stats"]
    with writer._get_conn() as conn:
        with conn.cursor() as cur:
            for table in tables:
                cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cur.fetchone()[0]
                logging.info(f"  {table}: {count}")


def _seed():
    """Seed lookup tables before any ingestion."""
    writer = PgDBWriter()
    writer.seed_lookup_tables()
    logging.info("Lookup tables seeded")


async def _run_ingestion(game_ids: list[str]):
    """Run ingestion for a list of game IDs."""
    _seed()
    provider = ESPNClient()
    transformer = ESPNTransformer()
    writer = PgDBWriter()
    engine = IngestionEngine(provider, transformer, writer)
    return await engine.process_game_ids(game_ids)


async def _run_week_ingestion(year: str, week: int, type_id: int = 2):
    """Run ingestion for a specific week."""
    _seed()
    provider = ESPNClient()
    transformer = ESPNTransformer()
    writer = PgDBWriter()
    engine = IngestionEngine(provider, transformer, writer)
    return await engine.process_week(year, week, type_id)


async def _run_season_ingestion(year: str, include_playoffs: bool):
    """Run ingestion for an entire season."""
    _seed()
    provider = ESPNClient()
    transformer = ESPNTransformer()
    writer = PgDBWriter()
    engine = IngestionEngine(provider, transformer, writer)
    return await engine.process_season(year, include_playoffs)


async def _run_single_game(event_id: str):
    """Run ingestion for a single game."""
    _seed()
    provider = ESPNClient()
    transformer = ESPNTransformer()
    writer = PgDBWriter()
    engine = IngestionEngine(provider, transformer, writer)
    result = await engine.process_game(event_id)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="NFL Fantasy Football Database - ESPN API Ingestion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ingest --game-id 401500000000
  python -m ingest --date 2025-09-04
  python -m ingest --week 2025 1
  python -m ingest --season 2025 --include-playoffs
  python -m ingest --counts
  python -m ingest --service
        """,
    )

    parser.add_argument("--game-id", "-g", type=str, help="Single ESPN game/event ID to process")
    parser.add_argument("--date", "-d", type=str, help="Date in YYYY-MM-DD format to fetch games for")
    parser.add_argument("--week", "-w", nargs=2, metavar=("YEAR", "WEEK"), help="Year and week to ingest")
    parser.add_argument("--season", "-s", type=str, help="Process entire season (e.g., 2025)")
    parser.add_argument("--include-playoffs", "-p", action="store_true", help="Include playoffs in download")
    parser.add_argument("--counts", "-c", action="store_true", help="Show database table counts")
    parser.add_argument("--service", action="store_true", help="Start FastAPI web service")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress INFO logging")
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging")

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle --counts only
    if args.counts:
        _log_counts()
        return

    # Handle --service
    if args.service:
        import uvicorn
        logging.info("Starting FastAPI service on http://0.0.0.0:8000")
        uvicorn.run("ingest.service.app:app", host="0.0.0.0", port=8000, reload=False)
        return

    async def _main():
        if args.season:
            logging.info(f"Processing entire {args.season} season")
            processed, failed = await _run_season_ingestion(args.season, args.include_playoffs)
            logging.info(f"Completed: {processed} succeeded, {failed} failed")
        elif args.week:
            year, week = args.week[0], int(args.week[1])
            logging.info(f"Processing year={year}, week={week}")
            processed, failed = await _run_week_ingestion(year, week)
            logging.info(f"Completed: {processed} succeeded, {failed} failed")
        elif args.game_id:
            logging.info(f"Processing game: {args.game_id}")
            result = await _run_single_game(args.game_id)
            logging.info(f"Game ID: {result}")
        elif args.date:
            logging.info(f"Fetching scoreboard for date: {args.date}")
            from ingest.espn.client import ESPNClient
            client = ESPNClient()
            sb = await client.fetch_scoreboard(args.date)
            ids = []
            for league in sb.get("leagues", []):
                for event in league.get("events", []):
                    eid = event.get("id")
                    if eid:
                        ids.append(str(eid))
            if not ids:
                logging.warning("No games found for this date")
                return
            logging.info(f"Found {len(ids)} game(s)")
            processed, failed = await _run_ingestion(ids)
            logging.info(f"Completed: {processed} succeeded, {failed} failed")
        else:
            parser.print_help()

    asyncio.run(_main())


if __name__ == "__main__":
    main()
