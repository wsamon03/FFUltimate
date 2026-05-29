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
        # NFC Championship data (real game: NFC Championship 2024)
        if event_id == "401671749":
            return {
                "header": {
                    "id": event_id,
                    "competitions": [
                        {
                            "id": f"401671749",
                            "competitors": [
                                {
                                    "id": "25",
                                    "uid": "s:20,l:28,t:25",
                                    "type": "team",
                                    "order": 0,
                                    "homeAway": "home",
                                    "team": {"id": "25", "abbreviation": "WAS", "displayName": "Washington Commanders", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/was.png"},
                                    "score": "54"
                                },
                                {
                                    "id": "21",
                                    "uid": "s:20,l:28,t:21",
                                    "type": "team",
                                    "order": 1,
                                    "homeAway": "away",
                                    "team": {"id": "21", "abbreviation": "LAR", "displayName": "Los Angeles Rams", "logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png"},
                                    "score": "7"
                                }
                            ]
                        }
                    ]
                },
                "boxscore": {
                    "athletes": [
                        {"athlete": {"id": "3139477", "fullName": "Jayden Daniels", "slug": "jayden-daniels", "headshot": "https://a.espncdn.com/i/headshots/nfl/players/full/3139477.png", "team": {"id": "25"}}, "statistics": [{"name": "passing_yards", "displayValue": "242"}, {"name": "passing_tds", "displayValue": "3"}]},
                        {"athlete": {"id": "4362887", "fullName": "Brian Robinson Jr", "slug": "brian-robinson-jr", "headshot": "https://a.espncdn.com/i/headshots/nfl/players/full/4362887.png", "team": {"id": "25"}}, "statistics": [{"name": "rushing_yards", "displayValue": "67"}, {"name": "rushing_tds", "displayValue": "1"}]}
                    ]
                },
                "drives": {
                    "previous": [
                        {"id": "4016717490", "team": {"id": "25"}, "start": {"yardLine": 25}, "end": {"yardLine": 68}, "time": "0:00", "result": "Touchdown"},
                        {"id": "4016717491", "team": {"id": "21"}, "start": {"yardLine": 25}, "end": {"yardLine": 45}, "time": "0:00", "result": "Punt"}
                    ]
                },
                "winProbability": [],
                "players": {
                    "home": [
                        {"athlete": {"id": "3139477", "fullName": "Jayden Daniels", "slug": "jayden-daniels", "headshot": "https://a.espncdn.com/i/headshots/nfl/players/full/3139477.png", "team": {"id": "25"}, "position": {"abbreviation": "QB"}}, "stats": {"passing_yards": 242, "passing_tds": 3, "completions": 17, "attempts": 23, "rushing_yards": 40, "rushing_tds": 2}},
                        {"athlete": {"id": "4362887", "fullName": "Brian Robinson Jr", "slug": "brian-robinson-jr", "headshot": "https://a.espncdn.com/i/headshots/nfl/players/full/4362887.png", "team": {"id": "25"}, "position": {"abbreviation": "RB"}}, "stats": {"rushing_yards": 67, "rushing_attempts": 11, "rushing_tds": 1, "receptions": 1, "receiving_yards": 22}},
                        {"athlete": {"id": "4429693", "fullName": "Austin Ekeler", "slug": "austin-ekeler", "headshot": "https://a.espncdn.com/i/headshots/nfl/players/full/4429693.png", "team": {"id": "25"}, "position": {"abbreviation": "RB"}}, "stats": {"rushing_yards": 40, "rushing_attempts": 7, "receptions": 2, "receiving_yards": 30}}
                    ],
                    "away": [
                        {"athlete": {"id": "4241457", "fullName": "Matthew Stafford", "slug": "matthew-stafford", "headshot": "https://a.espncdn.com/i/headshots/nfl/players/full/4241457.png", "team": {"id": "21"}}, "stats": {"passing_yards": 205, "passing_tds": 0, "completions": 18, "attempts": 35, "interceptions": 2}},
                        {"athlete": {"id": "4426515", "fullName": "Kyren Williams", "slug": "kyren-williams", "headshot": "https://a.espncdn.com/i/headshots/nfl/players/full/4426515.png", "team": {"id": "21"}}, "stats": {"rushing_yards": 61, "rushing_attempts": 14, "rushing_tds": 1, "receptions": 5, "receiving_yards": 45}}
                    ]
                }
            }
        return None

    async def fetch_scoreboard_by_week(self, year: str, week: int, type_id: int) -> dict:
        return {
            "events": [
                {"id": "401671749"}, # NFC Championship
                {"id": "401671750"}, # AFC Championship
                {"id": "401671751"}  # Example week 20 game
            ]
        }

    async def discover_season_games(self, year: str, include_playoffs: bool = False) -> list:
        if include_playoffs:
            return ["401671749", "401671750"]
        return ["401671749", "401671750", "401671751", "401671752", "401671753", "401671754"]
