"""ESPN API response normalizers."""

from datetime import datetime
from typing import Optional

from ingest.espn.models import NormalizedTeam, NormalizedPlayer, NormalizedGame

ESPN_TO_DB_STATUS = {
    "post": "final",
    "pre": "scheduled",
    "preview": "scheduled",
    "live": "live",
    "in progress": "live",
    "final": "final",
    "all": "final",
}


def _map_espn_status(espn_status: str) -> str:
    """Map ESPN API status code to our DB game_status status_code."""
    if not espn_status:
        return "unknown"
    return ESPN_TO_DB_STATUS.get(espn_status.lower(), "unknown")


def _safe_int(v) -> int:
    """Safely convert to int."""
    if v is None:
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


def _parse_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime."""
    if not date_str:
        return datetime.now()
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.now()


def parse_scoreboard(raw: dict) -> list[dict]:
    """Parse scoreboard response into list of game summary dicts (no stats).

    Scoreboard provides lightweight game metadata only - discovery data.
    Returns list of dicts with game IDs and basic team info.
    """
    games = []
    for league in raw.get("leagues", []):
        for event in league.get("events", []):
            game_id = event.get("id")
            if not game_id:
                continue
            competitions = event.get("competitions", [])
            if not competitions:
                continue
            comp = competitions[0]
            date_str = comp.get("date", "")
            status = event.get("status", {}).get("type", {}).get("state")
            if not status:
                for sub_comp in comp.get("competitions", [comp]):
                    status = sub_comp.get("status", {}).get("type", {}).get("state")
                    if status:
                        break
            if not status:
                status = "unknown"
            status = _map_espn_status(status)
            teams = []
            for c in comp.get("competitors", []):
                teams.append({
                    "espn_id": str(c.get("team", {}).get("id", "")),
                    "abbr": c.get("team", {}).get("abbreviation", ""),
                    "display_name": c.get("team", {}).get("displayName", ""),
                    "home_away": c.get("homeAway", ""),
                    "score": _safe_int(c.get("score")),
                })
            games.append({
                "game_id": str(game_id),
                "date_str": date_str,
                "status_code": status,
                "teams": teams,
            })
    return games


def parse_summary(raw: dict) -> Optional[NormalizedGame]:
    """Parse full game summary/boxscore response into a NormalizedGame."""
    if not raw:
        return None

    header = raw.get("header", {})
    boxscore = raw.get("boxscore", {})
    if not header or not boxscore:
        return None

    # Extract game metadata from header
    season_info = header.get("season", {})
    week_info = header.get("week", {})
    if isinstance(week_info, dict):
        week = week_info.get("number", week_info.get("week", 0))
    else:
        week = week_info if isinstance(week_info, int) else 0

    season_year = season_info.get("year", 0) if isinstance(season_info, dict) else 0
    if not season_year and week_info and isinstance(week_info, dict):
        season_year = week_info.get("year", 0)
    if not season_year:
        for league in raw.get("leagues", []):
            s = league.get("season", {})
            if isinstance(s, dict):
                season_year = s.get("year", 0)
                break

    date_str = header.get("date", "")
    if not date_str:
        # Fallback: get date from competitions list in header
        for comp in header.get("competitions", []):
            date_str = comp.get("date", "")
            if date_str:
                break
    game_date = _parse_date(date_str) if date_str else datetime.now()

    # Extract status from the correct ESPN API path
    status = header.get("status", {}).get("type", {}).get("state")
    if not status:
        # ESPN puts status in competitions[0].status.type.state
        for comp in header.get("competitions", []):
            status = comp.get("status", {}).get("type", {}).get("state")
            if status:
                break
    if not status:
        status = "unknown"

    # Map ESPN status codes to DB game_status codes
    status = _map_espn_status(status)

    # Extract home/away teams from header competitors
    home_team = None
    away_team = None
    for comp in header.get("competitions", []):
        for c in comp.get("competitors", []):
            team = c.get("team", {})
            ha = c.get("homeAway", "")
            team_data = {
                "espn_id": str(team.get("id", "")),
                "abbr": team.get("abbreviation", ""),
                "display_name": team.get("displayName", team.get("name", "")),
                "home_away": ha,
                "score": _safe_int(c.get("score")),
                "team_statistics": [],  # filled below from boxscore
            }
            if ha == "home":
                home_team = NormalizedTeam(**team_data)
            else:
                away_team = NormalizedTeam(**team_data)

    if not home_team or not away_team:
        return None

    # Populate team statistics from boxscore.teams
    for team_stat in boxscore.get("teams", []):
        ha = team_stat.get("homeAway", "")
        team_abbr = team_stat.get("team", {}).get("abbreviation", "")
        if ha == "home" and home_team:
            home_team.team_statistics = team_stat.get("statistics", [])
        elif ha == "away" and away_team:
            away_team.team_statistics = team_stat.get("statistics", [])

    # Parse players from boxscore.players
    home_players = []
    away_players = []
    players_data = boxscore.get("players", [])
    for team_entry in players_data:
        team_info = team_entry.get("team", {})
        stats_cats = team_entry.get("statistics", [])
        team_abbr = team_info.get("abbreviation", "")
        if not team_abbr:
            continue

        for cat in stats_cats:
            athletes = cat.get("athletes", [])
            if not athletes:
                continue
            # Labels/stats may be on the cat itself or nested inside each entry's category
            labels = cat.get("labels", [])
            for entry in athletes:
                # entry-level category can override cat-level labels/stats
                entry_cat = entry.get("category", {})
                cat_labels = entry_cat.get("labels", None)
                cat_stats = entry_cat.get("stats", None)
                entry_labels = cat_labels if cat_labels is not None else labels
                entry_stats = cat_stats if cat_stats is not None else entry.get("stats", [])
                if not entry_labels:
                    continue
                athlete = entry.get("athlete", {})
                player_data = {
                    "espn_id": str(athlete.get("id", "")),
                    "display_name": athlete.get("displayName", ""),
                    "position_code": athlete.get("position", {}).get("abbreviation", ""),
                    "team_abbr": team_abbr,
                    "category_name": cat.get("name", ""),
                    "raw_category": {"labels": entry_labels, "stats": entry_stats},
                }
                player = NormalizedPlayer(**player_data)
                if team_info.get("homeAway") == "home" or team_abbr == home_team.abbr:
                    home_players.append(player)
                else:
                    away_players.append(player)

    return NormalizedGame(
        espn_id=str(header.get("id", header.get("eventId", raw.get("header", {}).get("id", "")))),
        status_code=status,
        game_date=game_date,
        home_team=home_team,
        away_team=away_team,
        week=week or 0,
        season_year=season_year,
        home_players=home_players,
        away_players=away_players,
    )
