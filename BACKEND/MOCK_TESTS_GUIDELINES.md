# Mock vs Real Testing Guidelines

## 🎯 When to Use What

### ✅ USE MOCK CLIENT for:
- **Unit tests** of parsing/transformer logic
- Testing with **small, controlled datasets**
- **Smoke tests** that don't require API access
- CI/CD pipelines where API calls are slow or rate-limited

### ✅ USE REAL API for:
- **Integration tests** of end-to-end ingestion
- **Production data validation**
- Verifying **multi-category player stats** (QB+RUSH+REC)
- Testing with **week-level bulk data** (W8/2024: 16 games)

---

## 🎭 MockESPNClient Limitations

| Feature | MockESPNClient | RealESPNClient |
|---------|--------|---|
| Games | ✅ 5 hardcoded (Week 4) | ✅ All live games |
| Player Stats | ✅ Basic (pass+rush+rec) | ✅ All ESPN categories |
| Defensive Stats | ⚠️ Limited | ✅ Full |
| Year-over-year | ❌ No | ✅ Historical |
| API Endpoint | `mock_api_client.fetch_*()` | `api_client.fetch_game_summary()` |

**Key Difference**: `fetch_game_summary(event_id)` on Mock returns `None` for non-mocked events!

---

## 🧪 Recommended Test Structure

```python
# ingest/espn/mock_client.py
from ingest.base import APIProvider, Transformer
import json

class MockESPNClient(APIProvider):
    def fetch_game_summary(self, event_id: str) -> Optional[EventSummary]:
        # Only return 5 mock game IDs
        MOCK_EVENT_IDS = [
            '401671685', '401671817', '401671667', '401671852', '401671720'
        ]
        
        if event_id not in MOCK_EVENT_IDS:
            return None  # Critical!
        
        return MockEventSummary(event_id, ...)
    
    # Mock event structure
class MockEventSummary(dict):
    def __init__(self, espn_id: str, season_year: int, week: int):
        self['espn_id'] = espn_id
        self['season_year'] = season_year
        self['week'] = week
        # Add home_team, away_team...
        # Add team_game_stats...
        # Add home_players, away_players
        # Each player has category-specific stats
        self['home_players'] = [
            {'espn_id': 'abc123', 'name': 'Player A', 'stats': {...}},  # category='passing'
            {'espn_id': 'def456', 'name': 'Player B', 'stats': {...}},  # category='rushing'
        ]
```

---

## ⚠️ Test Pattern Example

```python
@pytest.mark.integration
def test_w8_2024_ingestion():
    # Uses REAL ESPNClient
    task = api_client.fetch_week('2024', '8')
    # Verifies 16 W8/2024 games ingested
    assert 16 == count_games_db()
    # Verifies QB stats (pass+rush+rec)
    assert jw_pass_yds == 334  # Jameis Winston
    assert jw_rush_yds == 10

@pytest.mark.unit
def test_player_stats_transform():
    # Uses MockESPNClient
    event = mock_client.fetch_game_summary('401671685')
    # Verify parse_boxscore normalizes player stats
    assert event.home_players has 24+ players
    assert event.home_players[0]['stats']['passing']['pass_yds'] == 100
```

---

## 🧪 Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| MockClient uses 5-game set | Task progress = 16/16 with 0 data | Switch to real API |
| ESPN client fetches `None` | `No data for game <event_id>` | Check event exists first |
| Multi-category upsert fails | QB stats overwritten | Use COALESCE pattern |
| Test runs too slowly | 20+ seconds for single game | Use MockClient in CI |

---

## 📋 Reference

| Component | Mock | Real |
|---------|-----|-----|
| Client | `MockESPNClient` | `ESPNClient` |
| Files | `ingest/espn/mock_client.py` | `ingest/espn/client.py` |
| Used For | Unit tests | Integration tests |
| Games | 5 hardcoded | Live ESPN |
| Default | True (if MOCK_ESPN) | False |

---

**Last Updated**: 2026-06-03  
**Verified With**: Jameis Winston pass_yds preserved after COALESCE
