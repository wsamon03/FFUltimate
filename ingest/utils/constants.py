"""Constants for the NFL ingestion system."""

ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

ESPN_SCOREBOARD_URL = f"{ESPN_API_BASE}/scoreboard"
ESPN_SUMMARY_URL = f"{ESPN_API_BASE}/summary"

ESPN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

SEASON_TYPES = {
    1: "Preseason",
    2: "Regular Season",
    3: "Playoffs",
}

WEEKS_REGULAR = 18
WEEKS_PLAYOFFS = 4  # weeks 19-22

RATE_LIMIT_DELAY = 0.5
