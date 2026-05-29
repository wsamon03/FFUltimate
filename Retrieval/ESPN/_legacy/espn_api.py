"""
ESPN NFL API client functions for fetching scoreboard and game data.
"""

import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ESPN API base URLs
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"

# Headers to mimic browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br"
}


def fetch_scoreboard(date: Optional[str] = None) -> dict:
    """
    Fetch NFL scoreboard data from ESPN API.

    Args:
        date: Optional date in YYYY-MM-DD format to filter games

    Returns:
        JSON response from ESPN API

    Raises:
        requests.RequestException: If API request fails
    """
    params = {}
    if date:
        params["date"] = date

    logger.info(f"Fetching scoreboard from ESPN API{' with date=' + date if date else ''}")

    response = requests.get(SCOREBOARD_URL, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def fetch_game_summary(game_id: str) -> dict:
    """
    Fetch detailed game summary from ESPN API.

    Args:
        game_id: ESPN event ID for the game

    Returns:
        JSON response from ESPN API with full game details

    Raises:
        requests.RequestException: If API request fails
    """
    url = f"{SUMMARY_URL}?event={game_id}"
    logger.info(f"Fetching game summary for event={game_id}")

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    return response.json()


def extract_game_ids(scoreboard: dict) -> list:
    """
    Extract game IDs from scoreboard events array.

    Args:
        scoreboard: JSON response from fetch_scoreboard()

    Returns:
        List of game (event) IDs as strings
    """
    game_ids = []

    # Navigate to leagues -> events array
    leagues = scoreboard.get("leagues", [])
    for league in leagues:
        events = league.get("events", [])
        for event in events:
            event_id = event.get("id")
            if event_id:
                game_ids.append(str(event_id))

    logger.info(f"Extracted {len(game_ids)} game IDs from scoreboard")
    return game_ids


def get_boxscore(data: dict) -> Optional[dict]:
    """
    Extract boxscore from game summary data.

    Args:
        data: JSON response from fetch_game_summary()

    Returns:
        Boxscore dictionary or None if not found
    """
    return data.get("boxscore")


def get_game_info(data: dict) -> Optional[dict]:
    """
    Extract game header/info from game summary data.

    Args:
        data: JSON response from fetch_game_summary()

    Returns:
        Game header dictionary or None if not found
    """
    return data.get("header")
