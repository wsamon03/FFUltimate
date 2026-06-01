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

    # --- Mock Game Data Store ---
    _GAMES_DATA = {
        "401671749": "49ers vs Rams (2024 Week 4)",
        "401671750": "Cowboys vs Eagles (2024 Week 4)",
        "401671751": "Bills vs Dolphins (2024 Week 4)",
        "401671752": "Chiefs vs Raiders (2024 Week 4)",
        "401671753": "Lions vs Vikings (2024 Week 4)",
    }

    async def fetch_game_summary(self, event_id: str) -> dict:
        if event_id not in MockESPNClient._GAMES_DATA:
            return None
        
        # Realistic summary structure for a generic game
        return {
            "header": {
                "id": event_id,
                "season": {"year": 2024},
                "week": {"number": 4},
                "date": "2024-10-03T22:00:00Z",
                "competitions": [
                    {
                        "id": event_id,
                        "competitors": [
                            {"id": "25", "homeAway": "home", "team": {"id": "25", "abbreviation": "WAS", "displayName": "Washington Commanders"}, "score": "24"},
                            {"id": "21", "homeAway": "away", "team": {"id": "21", "abbreviation": "LAR", "displayName": "Los Angeles Rams"}, "score": "20"}
                        ],
                        "status": {"type": {"state": "post"}}
                    }
                ]
            },
            "boxscore": {
                "teams": [
                    {"homeAway": "home", "team": {"abbreviation": "WAS"}, "statistics": [{"name": "pts_total", "displayValue": "24"}]},
                    {"homeAway": "away", "team": {"abbreviation": "LAR"}, "statistics": [{"name": "pts_total", "displayValue": "20"}]}
                ],
                "players": [
                    {"team": {"abbreviation": "WAS"}, "statistics": [{"name": "Passing", "athletes": [{"athlete": {"id": "1", "displayName": "Jayden Daniels", "position": {"abbreviation": "QB"}, "team": {"id": "25"}}, "stats": ["17", "23", "242", "3", "0", "0", "0", "40", "2", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]}]}]},
                    {"team": {"abbreviation": "LAR"}, "statistics": [{"name": "Passing", "athletes": [{"athlete": {"id": "2", "displayName": "Stevie Diggs", "position": {"abbreviation": "QB"}, "team": {"id": "21"}}, "stats": ["25", "40", "310", "2", "1", "0", "0", "35", "1", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]}]}]}
                ]
            }
        }

    async def fetch_scoreboard(self, date: str) -> dict:
        return {"events": []}

    async def fetch_scoreboard_by_week(self, year: str, week: int, type_id: int) -> dict:
        # Return the 5 mock games we have data for
        return {
            "events": [
                {"id": k} for k in MockESPNClient._GAMES_DATA.keys()
            ]
        }

    async def discover_season_games(self, year: str, include_playoffs: bool = False) -> list:
        return list(MockESPNClient._GAMES_DATA.keys())
