-- League team expansion: branding, matchups, season stats, transactions, draft picks.
-- Run after 06_league_settings.sql.

-- ---------------------------------------------------------------------------
-- EXTEND user_api.league_teams — branding columns
-- ---------------------------------------------------------------------------

ALTER TABLE user_api.league_teams
    ADD COLUMN IF NOT EXISTS abbreviation       VARCHAR(5),
    ADD COLUMN IF NOT EXISTS logo_url           TEXT,
    ADD COLUMN IF NOT EXISTS slogan             VARCHAR(200),
    ADD COLUMN IF NOT EXISTS primary_color      CHAR(7),
    ADD COLUMN IF NOT EXISTS secondary_color_1  CHAR(7),
    ADD COLUMN IF NOT EXISTS secondary_color_2  CHAR(7);


-- ---------------------------------------------------------------------------
-- league_weekly_matchups — one row per matchup (home vs away) per week
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_api.league_weekly_matchups (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id       UUID        NOT NULL REFERENCES user_api.leagues(id) ON DELETE CASCADE,
    season_year     INT         NOT NULL,
    week            INT         NOT NULL,
    home_team_id    UUID        NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    away_team_id    UUID        NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    home_score      NUMERIC(8,2),
    away_score      NUMERIC(8,2),
    home_projected  NUMERIC(8,2),
    away_projected  NUMERIC(8,2),
    is_playoff      BOOLEAN     NOT NULL DEFAULT FALSE,
    status          VARCHAR(20) NOT NULL DEFAULT 'scheduled',   -- 'scheduled', 'in_progress', 'final'
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_matchup_status CHECK (status IN ('scheduled', 'in_progress', 'final')),
    CONSTRAINT chk_different_teams CHECK (home_team_id != away_team_id),
    UNIQUE (league_id, season_year, week, home_team_id),
    UNIQUE (league_id, season_year, week, away_team_id)
);

CREATE INDEX IF NOT EXISTS idx_matchups_league_season_week
    ON user_api.league_weekly_matchups(league_id, season_year, week);
CREATE INDEX IF NOT EXISTS idx_matchups_home_team ON user_api.league_weekly_matchups(home_team_id);
CREATE INDEX IF NOT EXISTS idx_matchups_away_team ON user_api.league_weekly_matchups(away_team_id);


-- ---------------------------------------------------------------------------
-- league_team_season_stats — per-team, per-season running counters
-- Standings (W/L/PF/PA/streak) are COMPUTED from matchups, not stored here.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_api.league_team_season_stats (
    league_team_id      UUID        NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    season_year         INT         NOT NULL,
    waiver_position     INT,
    waiver_budget_start INT,
    waiver_budget_used  INT         NOT NULL DEFAULT 0,
    total_moves         INT         NOT NULL DEFAULT 0,
    playoff_seed        INT,
    is_eliminated       BOOLEAN     NOT NULL DEFAULT FALSE,
    playoff_result      VARCHAR(30),        -- 'champion', 'runner_up', 'eliminated_rd1', etc.
    PRIMARY KEY (league_team_id, season_year)
);

CREATE INDEX IF NOT EXISTS idx_team_season_stats_season
    ON user_api.league_team_season_stats(season_year);


-- ---------------------------------------------------------------------------
-- league_transactions — log of every add/drop/waiver/trade action
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_api.league_transactions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id       UUID        NOT NULL REFERENCES user_api.leagues(id) ON DELETE CASCADE,
    league_team_id  UUID        NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL,  -- 'add', 'drop', 'waiver', 'trade', 'ir_activate', 'ir_deactivate'
    player_id       UUID        REFERENCES public.players(id),
    related_team_id UUID        REFERENCES user_api.league_teams(id),
    waiver_bid      INT,
    week            INT,
    season_year     INT         NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'approved',  -- 'pending', 'approved', 'vetoed', 'failed'
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_tx_type CHECK (transaction_type IN ('add', 'drop', 'waiver', 'trade', 'ir_activate', 'ir_deactivate')),
    CONSTRAINT chk_tx_status CHECK (status IN ('pending', 'approved', 'vetoed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_transactions_league_season
    ON user_api.league_transactions(league_id, season_year);
CREATE INDEX IF NOT EXISTS idx_transactions_team
    ON user_api.league_transactions(league_team_id);


-- ---------------------------------------------------------------------------
-- league_draft_picks — every pick in a draft event
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_api.league_draft_picks (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id       UUID        NOT NULL REFERENCES user_api.leagues(id) ON DELETE CASCADE,
    draft_year      INT         NOT NULL,
    pick_number     INT         NOT NULL,
    round_number    INT         NOT NULL,
    pick_in_round   INT         NOT NULL,
    league_team_id  UUID        NOT NULL REFERENCES user_api.league_teams(id),
    player_id       UUID        REFERENCES public.players(id),
    bid_amount      INT,                    -- auction only
    nominated_by    UUID        REFERENCES user_api.league_teams(id),   -- auction only
    drafted_at      TIMESTAMP,
    UNIQUE (league_id, draft_year, pick_number)
);

CREATE INDEX IF NOT EXISTS idx_draft_picks_league_year
    ON user_api.league_draft_picks(league_id, draft_year);
CREATE INDEX IF NOT EXISTS idx_draft_picks_team
    ON user_api.league_draft_picks(league_team_id);
