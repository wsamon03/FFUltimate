"""Mock ESPN client for sandbox testing."""

from ingest.base import APIProvider

class MockESPNClient(APIProvider):
    """A mock client that returns realistic NFL data without external API calls."""
    
    @property
    def name(self) -> str:
        return "mock"

    @property
    def rate_limit_delay(self) -> float:
        return 0.0

    async def fetch_game_summary(self, event_id: str) -> dict:
        games = {
            "401671749": {
                "header": {
                    "id": event_id,
                    "season": {"year": 2024},
                    "week": {"number": 20},
                    "date": "2024-01-28T22:00:00Z",
                    "competitions": [
                        {
                            "id": f"{event_id}",
                            "competitors": [
                                {"id": "25", "homeAway": "home", "team": {"id": "25", "abbreviation": "WAS", "displayName": "Washington Commanders"}, "score": "54"},
                                {"id": "21", "homeAway": "away", "team": {"id": "21", "abbreviation": "LAR", "displayName": "Los Angeles Rams"}, "score": "7"}
                            ],
                            "status": {"type": {"state": "post"}}
                        }
                    ]
                },
                "boxscore": {
                    "teams": [
                        {"homeAway": "home", "team": {"abbreviation": "WAS"}, "statistics": [{"name": "pts_total", "displayValue": "54"}]},
                        {"homeAway": "away", "team": {"abbreviation": "LAR"}, "statistics": [{"name": "pts_total", "displayValue": "7"}]}
                    ],
                    "players": [
                        {"team": {"abbreviation": "WAS"}, "statistics": [{"name": "Passing", "athletes": [{"athlete": {"id": "1", "displayName": "Jayden Daniels", "position": {"abbreviation": "QB"}, "team": {"id": "25"}}, "stats": ["17", "23", "242", "3", "0", "0", "0", "40", "2", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]}]}]}
                    ]
                }
            }
        }
        return games.get(event_id)

    async def fetch_scoreboard(self, date: str) -> dict:
        return {"events": []}

    async def fetch_scoreboard_by_week(self, year: str, week: int, type_id: int) -> dict:
        return { "events": [] }

    async def discover_season_games(self, year: str, include_playoffs: bool = False) -> list:
        if include_playoffs:
            return ["401671749"]
        return ["401671749"]
