# User API Service Guide

## Overview

**`user_api/`**, **`DB/03_user_api_schema.sql`**, **`DB/04_user_api_procedures.sql`**

A **separate FastAPI microservice** on port `8001`. Handles:
- OAuth 2.0 PKCE login (Google / Microsoft)
- JWT access tokens + HttpOnly refresh tokens
- Fantasy leagues & teams
- Roster & lineup management
- Favorites system

---

## Architecture

```
┌──────────────┬─────────────────────────────────────────────────────────────┐
│   FRONTEND   │                                                              │
│ (port 3000)  │  GET /auth/login?provider=google                            │
└──────────────┼─────────────────────────────────────────────────────────────┘
               │ OAuth redirect
               ↓
┌──────────────┬─────────────────────────────────────────────────────────────┐
│    OAuth    │                        │  backend: oauth_service.exchange │
│ provider    │  (code + signed state) │ code(state, code) → user info   │
└──────────────┼─────────────────────────────────────────────────────────────┘
               │ callback params
               ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│  user_api service (port 8001)                                                 │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────────────────────────────────────────┐ │
│  │ /auth/           │  │ /api/leagues/, /api/stats/, /player/, etc.      │ │
│  │ oauth            │  │                                                  │ │
│  └──────────────────┘  └──────────────────────────────────────────────────┘ │
│                                                                                 │
│  Auth: Bearer JWT (15 min) + HttpOnly cookie (30 days rotation)              │
└───────────────────────────────────────────────────────────────────────────────┘

Flow:
  Frontend → GET /auth/login → OAuth provider → callback → JWT + refresh cookie
  (PKCE state signing via itsdangerous; never stores session data)
```

---

## Database Schema (`user_api` schema)

### Core tables
| Table | Purpose |
|-------|-------|
| `users` | oauth users (provider + provider_sub unique identifier) |
| `refresh_tokens` | SHA-256 hashed refresh tokens (opaque; user_id + expiry queried from DB during validation) |
| `leagues` | fantasy leagues |
| `league_teams` | teams in a league |
| `league_team_owners` | user ownership (many-to-many, with commissioner + email_display settings) |
| `roster_players` | current roster (1:1 player per team) |
| `weekly_lineups` | per-slot per-week lineup (season_week_player triple unique) |
| `favorites` | player / team bookmarks (chk_one_target ensures only one of player_id OR team_id non-null) |

---

## Stored Procedures

### Write functions (`usp_*`) — returns UUID
| Procedure | Purpose |
|-----------|--------|
| `usp_upsert_user` | upsert user, returns new UUID, ON CONFLICT updates timestamp |
| `usp_store_refresh_token` | insert hashed token |
| `usp_cleanup_expired_tokens` | purge expired / revoked tokens |
| `usp_create_league` | new league, returns UUID |
| `usp_create_league_team` | new team + automatically make creator the commissioner-owner |
| `usp_add_league_team_owner` | upsert co-owner (conflict on (league_team_id, user_id) merges + upserts) |

### Read functions (`fn_get_*`) — return tables
| Function | Purpose |
|----------|--------|
| `fn_get_user_leagues` | leagues user participates in |
| `fn_get_league_teams` | teams in a league with owner_count |
| `fn_get_team_owners` | owners of a team with email_display settings |
| `fn_get_team_roster` | roster including NFL team info |
| `fn_get_team_lineup` | started lineup for specific season/week |
| `fn_get_user_favorites` | UNION of player favorites + team favorites |

---

## Services

### `jwt_service.py`
```python
from datetime import timedelta, timezone
import jwt

def issue_access_token(user_id: UUID, email: str, provider: str) -> str:
    now = datetime.now(tz=timezone.utc)
    claims = {
        "sub": str(user_id),
        "email": email,
        "provider": provider,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
```
- HS256, 15 min default TTL
- Payload: `{sub, email, provider, iat, exp}`

### `oauth_service.py` — PKCE, S256
```python
def build_authorization_url(provider: str) -> tuple[str, str]:
    """Returns (redirect_url, signed_state).
    State signed state: server never stores session data.
    """
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'').decode()
    challenge = _sha256(verifier)
    return redirect_url, itsdangerous.dumps({"provider": provider, "verifier": verifier})

async def exchange_code(state: str, code: str) -> dict:
    token_exchange → OAuth userinfo → {"sub", "email", "display_name", "avatar_url"}
```

### `user_service.py`
```python
async def upsert_user(conn, provider, provider_sub, email, ...) -> UUID
async def generate_refresh_token() -> str
async def store_refresh_token(conn, user_id, raw_token, ...)
async def validate_refresh_token(conn, raw_token) -> UUID | None
async def revoke_refresh_token(conn, raw_token) -> None
```

---

## Routers

### Auth routes (`/auth`)
| Endpoint | Method |
|----------|--------|
| `/login` | GET |
| `/callback` | GET |
| `/refresh` | POST |
| `/logout` | POST |
| `/me` | GET |

### Fantasy routes (`/api/`)
| Prefix | Method | Purpose |
|--------|--------|--------|
| `/leagues` | GET | user's leagues |
| `/leagues` | POST | create league |
| `/leagues/{id}` | GET | fetch league |
| `/leagues/{id}/teams` | GET | teams in league |
| `/leagues/{id}/teams` | POST | create team |
| `/leagues/{id}/teams/{tid}` | PATCH | rename team |
| `/leagues/{id}/teams/{tid}/owners` | GET | owners |
| `/leagues/{id}/teams/{tid}/owners` | POST | add owner |
| `/leagues/{id}/teams/{tid}/owners/{uid}` | PATCH | update owner settings |
| `/leagues/{id}/teams/{tid}/owners/{uid}` | DELETE | remove owner |
| `/leagues/{id}/teams/{tid}/roster` | GET | roster |
| `/leagues/{id}/teams/{tid}/roster` | POST | add player |
| `/leagues/{id}/teams/{tid}/roster/{pid}` | DELETE | drop player |
| `/leagues/{id}/teams/{tid}/lineup/{s}/{w}` | GET | lineup |
| `/leagues/{id}/teams/{tid}/lineup/{s}/{w}` | PUT | replace lineup |
| `/favorites` | GET | list favorites |
| `/favorites/players` | POST | favorite player |
| `/favorites/players/{pid}` | DELETE | unfavorite |
| `/favorites/teams` | POST | favorite team |
| `/favorites/teams/{tid}` | DELETE | unfavorite |
| `/players` | GET | search |
| `/players/{pid}` | GET | player info |
| `/stats/teams` | GET | all teams |
| `/stats/games` | GET | game list |
| `/stats/game/{g}` | GET | game details |
| `/stats/player/{p}` | GET | player career |
| `/stats/team/{t}` | GET | team season |
| `/stats/leaderboard/{g}/{cat}` | GET | game stats leader |
| `/stats/fantasy/{p}` | GET | player fantasy |

---

## Config (`user_api/config.py`)

Required env vars:
```bash
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/callback?provider=google
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=common
AZURE_REDIRECT_URI=http://localhost:8001/auth/callback?provider=microsoft
JWT_SECRET_KEY=<32 hex bytes>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
STATE_SECRET_KEY=<32 hex bytes>
```

---

## Startup

```bash
cd user_api
uvicorn app:app --host 0.0.0.0 --port 8001
# or
python -m user_api
```

---

## Auth Flow Details

### Login (PKCE)
```
GET /auth/login?provider=google → OAuth redirect
(user provides credentials)
GET /auth/callback?code=XXX&state=YYY
↓
Backend verifies state → code_verifier → matches OAuth state
↓
exchange_code() → OAuth userinfo
↓
upsert_user(conn, ...) → new UUID
↓
store_refresh_token(conn, ...) → hashed refresh token in cookie
↓
issue_access_token() → JWT access token
↓
response: access_token + refresh_token-cookie
```

### Refresh (cookie-based)
```
POST /auth/refresh (cookie auto-sent)
↓
validate_refresh_token(conn, raw_token)
↓
revoke_refresh_token(conn, raw_token)  # rotation
↓
new refresh token + access token
```

### Logout
```
POST /auth/logout
↓
revoke_refresh_token  # no session cleanup needed
↓
clear refresh cookie
```

---

## Notes

- PKCE over S256; state encodes code_verifier so server never stores session data
- Refresh tokens are opaque SHA-256 hashes in HttpOnly cookie; validate by hash + query expiry from DB
- Team owners handled by upsert conflict (auto-add creator as commissioner)
- Lineup replace clears old lineup then inserts new slots within transaction
