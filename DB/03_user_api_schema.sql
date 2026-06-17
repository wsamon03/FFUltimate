-- User API schema: users, auth tokens, leagues, teams, owners, rosters, lineups, favorites
-- Run after schema.sql (requires public.players and public.teams to exist)

CREATE SCHEMA IF NOT EXISTS user_api;

-- ---------------------------------------------------------------------------
-- 1. users
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider        VARCHAR(20)  NOT NULL,        -- 'google' | 'microsoft'
    provider_sub    VARCHAR(255) NOT NULL,         -- stable OAuth subject ID from provider
    email           VARCHAR(255) NOT NULL,
    display_name    VARCHAR(255),
    avatar_url      TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (provider, provider_sub)
);

CREATE INDEX IF NOT EXISTS idx_users_email ON user_api.users(email);

-- ---------------------------------------------------------------------------
-- 2. refresh_tokens
-- Only the SHA-256 hash is stored; the raw token lives in an HttpOnly cookie.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES user_api.users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,    -- SHA-256 hex of the raw opaque token
    issued_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMP NOT NULL,
    revoked     BOOLEAN NOT NULL DEFAULT FALSE,
    user_agent  TEXT,
    ip_address  INET
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON user_api.refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires  ON user_api.refresh_tokens(expires_at)
    WHERE revoked = FALSE;

-- ---------------------------------------------------------------------------
-- 3. local_credentials
-- Stores bcrypt password hashes for provider='local' users only.
-- Kept separate from users so the OAuth schema stays clean.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.local_credentials (
    user_id       UUID PRIMARY KEY REFERENCES user_api.users(id) ON DELETE CASCADE,
    password_hash VARCHAR(72) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- 5. leagues
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.leagues (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(150) NOT NULL,
    created_by  UUID NOT NULL REFERENCES user_api.users(id),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leagues_created_by ON user_api.leagues(created_by);

-- ---------------------------------------------------------------------------
-- 6. league_teams
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.league_teams (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id       UUID NOT NULL REFERENCES user_api.leagues(id) ON DELETE CASCADE,
    created_by_id   UUID NOT NULL REFERENCES user_api.users(id),
    name            VARCHAR(100) NOT NULL DEFAULT 'My Team',
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_league_teams_league_id     ON user_api.league_teams(league_id);
CREATE INDEX IF NOT EXISTS idx_league_teams_created_by_id ON user_api.league_teams(created_by_id);

-- ---------------------------------------------------------------------------
-- 7. league_team_owners
-- Many users can co-own a team. The team creator is auto-inserted as commissioner
-- by usp_create_league_team.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.league_team_owners (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_team_id      UUID NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES user_api.users(id) ON DELETE CASCADE,
    is_commissioner     BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    user_display_name   VARCHAR(100),
    is_email_displayed  BOOLEAN NOT NULL DEFAULT FALSE,
    joined_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (league_team_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_league_team_owners_team_id ON user_api.league_team_owners(league_team_id);
CREATE INDEX IF NOT EXISTS idx_league_team_owners_user_id ON user_api.league_team_owners(user_id);

-- ---------------------------------------------------------------------------
-- 8. roster_players
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.roster_players (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_team_id  UUID NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    player_id       UUID NOT NULL REFERENCES public.players(id),
    slot_position   VARCHAR(10),    -- 'QB', 'RB1', 'FLEX', 'BN1', etc.
    added_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (league_team_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_roster_players_league_team_id ON user_api.roster_players(league_team_id);

-- ---------------------------------------------------------------------------
-- 9. weekly_lineups
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.weekly_lineups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_team_id  UUID NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    player_id       UUID NOT NULL REFERENCES public.players(id),
    season_year     INT NOT NULL,
    week            INT NOT NULL,
    slot_position   VARCHAR(10) NOT NULL,
    set_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (league_team_id, player_id, season_year, week)
);

CREATE INDEX IF NOT EXISTS idx_weekly_lineups_team_week
    ON user_api.weekly_lineups(league_team_id, season_year, week);

-- ---------------------------------------------------------------------------
-- 10. favorites
-- One row per bookmark; exactly one of player_id / team_id is non-null.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api.favorites (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES user_api.users(id) ON DELETE CASCADE,
    kind          TEXT,  -- 'player' or 'team' (redundant with nullability but useful for queries)
    player_id     UUID REFERENCES public.players(id),
    team_id       UUID REFERENCES public.teams(id),
    target_name   VARCHAR,  -- cached player/team name for display
    extra         VARCHAR,  -- cached position_code for players, abbr for teams
    added_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_one_target CHECK (
        (player_id IS NOT NULL AND team_id IS NULL) OR
        (player_id IS NULL     AND team_id IS NOT NULL)
    ),
    UNIQUE (user_id, player_id),
    UNIQUE (user_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON user_api.favorites(user_id);
