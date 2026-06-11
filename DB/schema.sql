-- NFL Fantasy Football Database Schema
-- PostgreSQL DDL with dimensional data model
-- Follows "Base Atom" principle: stores only raw counting statistics

-- ============================================================================
-- LOOKUP TABLES
-- ============================================================================

CREATE TABLE game_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status_code VARCHAR(20) UNIQUE NOT NULL,
    description VARCHAR(100)
);
CREATE INDEX idx_game_status_code ON game_status(status_code);

CREATE TABLE player_position (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_code VARCHAR(10) UNIQUE NOT NULL,
    description VARCHAR(100)
);
CREATE INDEX idx_player_position_code ON player_position(position_code);

-- ============================================================================
-- DIMENSION TABLES (Entities)
-- ============================================================================

-- teams: Team entities keyed by abbr (stable); espn_id varies per game context
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    espn_id VARCHAR(50),
    abbr VARCHAR(5) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    game_team_espn_ids VARCHAR[]
);

CREATE INDEX idx_teams_abbr ON teams(abbr);
CREATE INDEX idx_teams_game_espn_ids ON teams USING gin (game_team_espn_ids);

-- players: Player entities linked to teams via foreign key
CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    espn_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    position_code VARCHAR(10) NOT NULL REFERENCES player_position(position_code),
    team_id UUID REFERENCES teams(id)
);

CREATE INDEX idx_players_espn_id ON players(espn_id);
CREATE INDEX idx_players_team_id ON players(team_id);
CREATE INDEX idx_players_position_code ON players(position_code);

-- games: Game metadata with ESPN event ID (stable per game); game-specific ESPN team IDs
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    espn_id VARCHAR(50) UNIQUE NOT NULL,
    status_code VARCHAR(20) NOT NULL REFERENCES game_status(status_code),
    game_date TIMESTAMP NOT NULL,
    home_espn_id VARCHAR(50),
    away_espn_id VARCHAR(50),
    home_team_id UUID REFERENCES teams(id),
    away_team_id UUID REFERENCES teams(id),
    home_score INT DEFAULT 0,
    away_score INT DEFAULT 0,
    home_score INT DEFAULT 0,
    away_score INT DEFAULT 0,
    week INT,
    season_year INT
);

CREATE INDEX idx_games_espn_id ON games(espn_id);
CREATE INDEX idx_games_date ON games(game_date);

-- ============================================================================
-- FACT TABLES (Performance Metrics)
-- ============================================================================

-- team_game_stats: Team-level boxscore data for each game
CREATE TABLE team_game_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id),
    -- Scoring
    pts_total INT,
    pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    -- Touchdowns
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    -- Offense
    off_first_downs INT,
    off_total_yds INT,
    off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    -- Defense
    def_sacks NUMERIC(3,1), def_int INT,
    -- Turnovers
    total_turnovers INT,
    -- Penalties
    penalties_count INT, penalties_yds INT,
    -- Metadata for niche/unmapped stats
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, team_id)
);

CREATE INDEX idx_team_stats_game_id ON team_game_stats(game_id);
CREATE INDEX idx_team_stats_team_id ON team_game_stats(team_id);

-- player_game_stats: Granular player performance metrics for each game
CREATE TABLE player_game_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID NOT NULL REFERENCES players(id),
    game_id UUID NOT NULL REFERENCES games(id),
    -- Passing
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    -- Rushing
    rush_att INT, rush_yds INT, rush_td INT,
    -- Receiving
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    -- Defense (Solo/Assist atoms only)
    def_solo INT, def_ast INT, def_sacks NUMERIC(3,1), def_tfl INT,
    def_pd INT, def_qb_hits INT, def_td INT, def_int INT,
    -- Kick Return
    ret_kick_no INT, ret_kick_yds INT, ret_kick_td INT,
    -- Punt Return
    ret_punt_no INT, ret_punt_yds INT, ret_punt_td INT,
    -- Kicking
    k_fg_make INT, k_fg_att INT, k_xp_make INT, k_xp_att INT,
    -- Punting
    p_no INT, p_yds INT, p_in20 INT, p_tb INT, p_fc INT, p_blk INT, p_long INT,
    -- Metadata for niche/unmapped stats
    metadata JSONB,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, game_id)
);

CREATE INDEX idx_player_stats_player_id ON player_game_stats(player_id);
CREATE INDEX idx_player_stats_game_id ON player_game_stats(game_id);
