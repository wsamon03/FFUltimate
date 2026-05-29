-- NFL Fantasy Football Database — Retrieval Functions
-- Read-only functions to fetch aggregated or filtered data
-- All functions are deterministic and do not modify data

-- ============================================================
-- DIMENSION TABLE PROCEDURES
-- ============================================================

-- Retrieve all teams
CREATE OR REPLACE FUNCTION fn_get_all_teams()
RETURNS TABLE(
    id UUID, espn_id VARCHAR, abbr VARCHAR, full_name VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT t.id, t.espn_id, t.abbr, t.full_name
    FROM teams t ORDER BY t.abbr;
END;
$$;

-- Retrieve teams by ESPN ID (matches espn_id column or game_team_espn_ids array)
CREATE OR REPLACE FUNCTION fn_get_teams_by_espn_id(
    p_espn_ids VARCHAR[]
)
RETURNS TABLE(
    id UUID, espn_id VARCHAR, abbr VARCHAR, full_name VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT t.id, t.espn_id, t.abbr, t.full_name
    FROM teams t
    WHERE t.espn_id = ANY(p_espn_ids)
       OR p_espn_ids && t.game_team_espn_ids
    ORDER BY t.abbr;
END;
$$;

-- Retrieve team by ESPN ID (matches espn_id column or game_team_espn_ids array)
CREATE OR REPLACE FUNCTION fn_get_team_by_espn_id(
    p_espn_id VARCHAR
)
RETURNS TABLE(
    id UUID, espn_id VARCHAR, abbr VARCHAR, full_name VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT t.id, t.espn_id, t.abbr, t.full_name
    FROM teams t
    WHERE t.espn_id = p_espn_id OR p_espn_id = ANY(COALESCE(t.game_team_espn_ids, ARRAY[]::VARCHAR[]));
END;
$$;

-- Retrieve all players
CREATE OR REPLACE FUNCTION fn_get_all_players()
RETURNS TABLE(
    id UUID, espn_id VARCHAR, name VARCHAR, position_code VARCHAR, team_id UUID
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT p.id, p.espn_id, p.name, p.position_code, p.team_id
    FROM players p ORDER BY p.name;
END;
$$;

-- Retrieve all active players (for current season)
CREATE OR REPLACE FUNCTION fn_get_active_players(
    p_season_year INT DEFAULT 2025,
    p_position_code VARCHAR DEFAULT NULL
)
RETURNS TABLE(
    id UUID, espn_id VARCHAR, name VARCHAR, position_code VARCHAR, team_id UUID,
    team_abbr VARCHAR, team_full_name VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT p.id, p.espn_id, p.name, p.position_code, p.team_id,
        t.abbr, t.full_name
    FROM players p
    JOIN teams t ON p.team_id = t.id
    WHERE p.season_year = p_season_year
      AND (p_position_code IS NULL OR p.position_code = p_position_code)
    ORDER BY t.full_name, p.name;
END;
$$;

-- Retrieve players by team
CREATE OR REPLACE FUNCTION fn_get_players_by_team(
    p_team_id UUID
)
RETURNS TABLE(
    id UUID, espn_id VARCHAR, name VARCHAR, position_code VARCHAR, team_id UUID
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT p.id, p.espn_id, p.name, p.position_code, p.team_id
    FROM players p
    WHERE p.team_id = p_team_id
    ORDER BY p.position_code, p.name;
END;
$$;

-- Retrieve players by ESPN ID
CREATE OR REPLACE FUNCTION fn_get_players_by_espn_id(
    p_espn_ids VARCHAR[]
)
RETURNS TABLE(
    id UUID, espn_id VARCHAR, name VARCHAR, position_code VARCHAR, team_id UUID
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT p.id, p.espn_id, p.name, p.position_code, p.team_id
    FROM players p
    WHERE p.espn_id = ANY(p_espn_ids)
    ORDER BY p.espn_id;
END;
$$;

-- Retrieve all games
CREATE OR REPLACE FUNCTION fn_get_all_games()
RETURNS TABLE(
    id UUID, espn_id VARCHAR, status_code VARCHAR, game_date TIMESTAMP,
    home_team_id UUID, away_team_id UUID, week INT, season_year INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT g.id, g.espn_id, g.status_code, g.game_date,
        g.home_team_id, g.away_team_id, g.week, g.season_year
    FROM games g
    ORDER BY g.game_date DESC, g.week DESC;
END;
$$;

-- Retrieve games by date range
CREATE OR REPLACE FUNCTION fn_get_games_by_date_range(
    p_start_date DATE,
    p_end_date DATE,
    p_season_year INT DEFAULT 2025
)
RETURNS TABLE(
    id UUID, espn_id VARCHAR, status_code VARCHAR, game_date TIMESTAMP,
    home_team_id UUID, away_team_id UUID, week INT, season_year INT,
    home_team_abbr VARCHAR, home_team_name VARCHAR,
    away_team_abbr VARCHAR, away_team_name VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT g.id, g.espn_id, g.status_code, g.game_date,
        g.home_team_id, g.away_team_id, g.week, g.season_year,
        t1.abbr, t1.full_name,
        t2.abbr, t2.full_name
    FROM games g
    JOIN teams t1 ON g.home_team_id = t1.id
    JOIN teams t2 ON g.away_team_id = t2.id
    WHERE g.game_date >= p_start_date
      AND g.game_date <= p_end_date
      AND g.season_year = p_season_year
    ORDER BY g.game_date DESC, g.week DESC;
END;
$$;

-- Retrieve games by ESPN ID
CREATE OR REPLACE FUNCTION fn_get_games_by_espn_id(
    p_espn_ids VARCHAR[]
)
RETURNS TABLE(
    id UUID, espn_id VARCHAR, status_code VARCHAR, game_date TIMESTAMP,
    home_team_id UUID, away_team_id UUID, week INT, season_year INT,
    home_team_abbr VARCHAR, home_team_name VARCHAR,
    away_team_abbr VARCHAR, away_team_name VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT g.id, g.espn_id, g.status_code, g.game_date,
        g.home_team_id, g.away_team_id, g.week, g.season_year,
        t.abbr, t.full_name,
        t2.abbr, t2.full_name
    FROM games g
    JOIN teams t ON g.home_team_id = t.id
    JOIN teams t2 ON g.away_team_id = t2.id
    WHERE g.espn_id = ANY(p_espn_ids)
    ORDER BY g.espn_id;
END;
$$;

-- Retrieve game by ESPN ID
CREATE OR REPLACE FUNCTION fn_get_game_by_espn_id(
    p_espn_id VARCHAR
)
RETURNS TABLE(
    id UUID, espn_id VARCHAR, status_code VARCHAR, game_date TIMESTAMP,
    home_team_id UUID, away_team_id UUID, week INT, season_year INT,
    home_team_abbr VARCHAR, home_team_name VARCHAR,
    away_team_abbr VARCHAR, away_team_name VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT g.id, g.espn_id, g.status_code, g.game_date,
        g.home_team_id, g.away_team_id, g.week, g.season_year,
        t.abbr, t.full_name,
        t2.abbr, t2.full_name
    FROM games g
    JOIN teams t ON g.home_team_id = t.id
    JOIN teams t2 ON g.away_team_id = t2.id
    WHERE g.espn_id = p_espn_id;
END;
$$;

-- ============================================================
-- TEAM GAME STATS PROCEDURES
-- ============================================================

-- Retrieve team stats for a specific game
CREATE OR REPLACE FUNCTION fn_get_team_stats_for_game(
    p_game_id UUID
)
RETURNS TABLE(
    id UUID, game_id UUID, team_id UUID, team_abbr VARCHAR, abbr VARCHAR, full_name VARCHAR,
    pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    off_first_downs INT, off_total_yds INT, off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    def_sacks NUMERIC(3,1), def_int INT,
    total_turnovers INT, penalties_count INT, penalties_yds INT,
    metadata JSONB, created_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT ts.id, ts.game_id, ts.team_id,
        t.abbr, t.abbr, t.full_name,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
        ts.off_first_downs, ts.off_total_yds, ts.off_plays,
        ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td,
        ts.off_possession_secs,
        ts.def_sacks, ts.def_int,
        ts.total_turnovers, ts.penalties_count, ts.penalties_yds,
        ts.metadata, ts.created_at
    FROM team_game_stats ts
    JOIN teams t ON ts.team_id = t.id
    WHERE ts.game_id = p_game_id
    ORDER BY ts.team_id;
END;
$$;

-- Retrieve team stats for a specific team
CREATE OR REPLACE FUNCTION fn_get_team_stats_for_team(
    p_team_id UUID
)
RETURNS TABLE(
    id UUID, game_id UUID, team_id UUID, game_espn_id VARCHAR,
    team_abbr VARCHAR, abbr VARCHAR, full_name VARCHAR,
    pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    off_first_downs INT, off_total_yds INT, off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    def_sacks NUMERIC(3,1), def_int INT,
    total_turnovers INT, penalties_count INT, penalties_yds INT,
    metadata JSONB, created_at TIMESTAMP, game_date TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT ts.id, ts.game_id, ts.team_id,
        g.espn_id,
        t.abbr, t.abbr, t.full_name,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
        ts.off_first_downs, ts.off_total_yds, ts.off_plays,
        ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td,
        ts.off_possession_secs,
        ts.def_sacks, ts.def_int,
        ts.total_turnovers, ts.penalties_count, ts.penalties_yds,
        ts.metadata, ts.created_at,
        g.game_date
    FROM team_game_stats ts
    JOIN games g ON ts.game_id = g.id
    JOIN teams t ON ts.team_id = t.id
    WHERE ts.team_id = p_team_id
    ORDER BY g.game_date DESC;
END;
$$;

-- Retrieve all team game stats
CREATE OR REPLACE FUNCTION fn_get_all_team_stats()
RETURNS TABLE(
    id UUID, game_id UUID, team_id UUID, game_espn_id VARCHAR,
    team_abbr VARCHAR, abbr VARCHAR, full_name VARCHAR, game_date TIMESTAMP,
    pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    off_first_downs INT, off_total_yds INT, off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    def_sacks NUMERIC(3,1), def_int INT,
    total_turnovers INT, penalties_count INT, penalties_yds INT,
    metadata JSONB, created_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT ts.id, ts.game_id, ts.team_id,
        g.espn_id,
        t.abbr, t.abbr, t.full_name, g.game_date,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
        ts.off_first_downs, ts.off_total_yds, ts.off_plays,
        ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td,
        ts.off_possession_secs,
        ts.def_sacks, ts.def_int,
        ts.total_turnovers, ts.penalties_count, ts.penalties_yds,
        ts.metadata, ts.created_at
    FROM team_game_stats ts
    JOIN games g ON ts.game_id = g.id
    JOIN teams t ON ts.team_id = t.id
    ORDER BY g.game_date DESC, t.abbr;
END;
$$;

-- Retrieve team stats for a team vs opponent
CREATE OR REPLACE FUNCTION fn_get_team_stats_vs_opponent(
    p_team_id UUID,
    p_opponent_abbr VARCHAR
)
RETURNS TABLE(
    id UUID, game_id UUID, team_id UUID, pts_total INT, off_total_yds INT, def_sacks NUMERIC(3,1),
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    off_3rd_att INT, off_3rd_make INT, off_redzone_att INT, off_redzone_td INT,
    total_turnovers INT, penalties_count INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT ts.id, ts.game_id, ts.team_id, ts.pts_total, ts.off_total_yds, ts.def_sacks,
        ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
        ts.off_3rd_att, ts.off_3rd_make, ts.off_redzone_att, ts.off_redzone_td,
        ts.total_turnovers, ts.penalties_count
    FROM team_game_stats ts
    JOIN games g ON ts.game_id = g.id
    JOIN teams t ON ts.team_id = t.id
    JOIN teams opponent ON (g.away_team_id = opponent.id OR g.home_team_id = opponent.id)
    WHERE ts.team_id = p_team_id
      AND opponent.abbr = p_opponent_abbr
    ORDER BY g.game_date DESC;
END;
$$;

-- ============================================================
-- PLAYER GAME STATS PROCEDURES
-- ============================================================

-- Retrieve player stats for a specific game
CREATE OR REPLACE FUNCTION fn_get_player_stats_for_game(
    p_game_id UUID,
    p_player_id UUID
)
RETURNS TABLE(
    id UUID, player_id UUID, game_id UUID,
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    game_espn_id VARCHAR, game_date TIMESTAMP,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    rush_att INT, rush_yds INT, rush_td INT,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    def_solo INT, def_ast INT, def_sacks NUMERIC(3,1), def_tfl INT, def_pd INT, def_qb_hits INT, def_td INT, def_int INT,
    ret_kick_no INT, ret_kick_yds INT, ret_kick_td INT,
    ret_punt_no INT, ret_punt_yds INT, ret_punt_td INT,
    k_fg_make INT, k_fg_att INT, k_xp_make INT, k_xp_att INT,
    p_no INT, p_yds INT, p_in20 INT, p_tb INT, p_fc INT, p_blk INT, p_long INT,
    metadata JSONB, last_updated TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT pgs.id, pgs.player_id, pgs.game_id,
        p.espn_id, p.name, p.position_code,
        g.espn_id, g.game_date,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int, pgs.pass_sacked,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        pgs.def_solo, pgs.def_ast, pgs.def_sacks, pgs.def_tfl, pgs.def_pd, pgs.def_qb_hits, pgs.def_td, pgs.def_int,
        pgs.ret_kick_no, pgs.ret_kick_yds, pgs.ret_kick_td,
        pgs.ret_punt_no, pgs.ret_punt_yds, pgs.ret_punt_td,
        pgs.k_fg_make, pgs.k_fg_att, pgs.k_xp_make, pgs.k_xp_att,
        pgs.p_no, pgs.p_yds, pgs.p_in20, pgs.p_tb, pgs.p_fc, pgs.p_blk, pgs.p_long,
        pgs.metadata, pgs.last_updated
    FROM player_game_stats pgs
    JOIN players p ON pgs.player_id = p.id
    JOIN games g ON pgs.game_id = g.id
    WHERE pgs.player_id = p_player_id AND pgs.game_id = p_game_id;
END;
$$;

-- Retrieve player stats for a specific player
CREATE OR REPLACE FUNCTION fn_get_player_stats_for_player(
    p_player_id UUID
)
RETURNS TABLE(
    id UUID, player_id UUID, game_id UUID,
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    game_espn_id VARCHAR, game_date TIMESTAMP, home_team_id UUID, away_team_id UUID,
    team_pts_total INT,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    rush_att INT, rush_yds INT, rush_td INT,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    def_solo INT, def_ast INT, def_sacks NUMERIC(3,1), def_tfl INT, def_pd INT, def_qb_hits INT, def_td INT, def_int INT,
    ret_kick_no INT, ret_kick_yds INT, ret_kick_td INT,
    ret_punt_no INT, ret_punt_yds INT, ret_punt_td INT,
    k_fg_make INT, k_fg_att INT, k_xp_make INT, k_xp_att INT,
    p_no INT, p_yds INT, p_in20 INT, p_tb INT, p_fc INT, p_blk INT, p_long INT,
    metadata JSONB, last_updated TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT pgs.id, pgs.player_id, pgs.game_id,
        p.espn_id, p.name, p.position_code,
        g.espn_id, g.game_date, g.home_team_id, g.away_team_id,
        ts.pts_total,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int, pgs.pass_sacked,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        pgs.def_solo, pgs.def_ast, pgs.def_sacks, pgs.def_tfl, pgs.def_pd, pgs.def_qb_hits, pgs.def_td, pgs.def_int,
        pgs.ret_kick_no, pgs.ret_kick_yds, pgs.ret_kick_td,
        pgs.ret_punt_no, pgs.ret_punt_yds, pgs.ret_punt_td,
        pgs.k_fg_make, pgs.k_fg_att, pgs.k_xp_make, pgs.k_xp_att,
        pgs.p_no, pgs.p_yds, pgs.p_in20, pgs.p_tb, pgs.p_fc, pgs.p_blk, pgs.p_long,
        pgs.metadata, pgs.last_updated
    FROM player_game_stats pgs
    JOIN players p ON pgs.player_id = p.id
    JOIN games g ON pgs.game_id = g.id
    JOIN team_game_stats ts ON pgs.game_id = ts.game_id AND (ts.team_id = g.home_team_id OR ts.team_id = g.away_team_id)
    WHERE pgs.player_id = p_player_id
    ORDER BY g.game_date DESC;
END;
$$;

-- Retrieve all player game stats
CREATE OR REPLACE FUNCTION fn_get_all_player_stats()
RETURNS TABLE(
    id UUID, player_id UUID, game_id UUID,
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_abbr VARCHAR, team_name VARCHAR,
    game_espn_id VARCHAR, game_date TIMESTAMP, home_team_id UUID, away_team_id UUID,
    team_pts_total INT,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    rush_att INT, rush_yds INT, rush_td INT,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    def_solo INT, def_ast INT, def_sacks NUMERIC(3,1), def_tfl INT, def_pd INT, def_qb_hits INT, def_td INT, def_int INT,
    ret_kick_no INT, ret_kick_yds INT, ret_kick_td INT,
    ret_punt_no INT, ret_punt_yds INT, ret_punt_td INT,
    k_fg_make INT, k_fg_att INT, k_xp_make INT, k_xp_att INT,
    p_no INT, p_yds INT, p_in20 INT, p_tb INT, p_fc INT, p_blk INT, p_long INT,
    metadata JSONB, last_updated TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT pgs.id, pgs.player_id, pgs.game_id,
        p.espn_id, p.name, p.position_code,
        t.abbr, t.full_name,
        g.espn_id, g.game_date, g.home_team_id, g.away_team_id,
        ts.pts_total,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int, pgs.pass_sacked,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        pgs.def_solo, pgs.def_ast, pgs.def_sacks, pgs.def_tfl, pgs.def_pd, pgs.def_qb_hits, pgs.def_td, pgs.def_int,
        pgs.ret_kick_no, pgs.ret_kick_yds, pgs.ret_kick_td,
        pgs.ret_punt_no, pgs.ret_punt_yds, pgs.ret_punt_td,
        pgs.k_fg_make, pgs.k_fg_att, pgs.k_xp_make, pgs.k_xp_att,
        pgs.p_no, pgs.p_yds, pgs.p_in20, pgs.p_tb, pgs.p_fc, pgs.p_blk, pgs.p_long,
        pgs.metadata, pgs.last_updated
    FROM player_game_stats pgs
    JOIN players p ON pgs.player_id = p.id
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON pgs.game_id = g.id
    JOIN team_game_stats ts ON pgs.game_id = ts.game_id AND (ts.team_id = g.home_team_id OR ts.team_id = g.away_team_id)
    ORDER BY g.game_date DESC, p.name, t.full_name;
END;
$$;

-- Retrieve player stats for a player vs opponent
CREATE OR REPLACE FUNCTION fn_get_player_stats_vs_opponent(
    p_player_id UUID,
    p_opponent_abbr VARCHAR
)
RETURNS TABLE(
    id UUID, player_id UUID, game_id UUID,
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    game_espn_id VARCHAR, game_date TIMESTAMP,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    rush_att INT, rush_yds INT, rush_td INT,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    def_solo INT, def_ast INT, def_sacks NUMERIC(3,1), def_tfl INT, def_pd INT, def_qb_hits INT, def_td INT, def_int INT,
    ret_kick_no INT, ret_kick_yds INT, ret_kick_td INT,
    ret_punt_no INT, ret_punt_yds INT, ret_punt_td INT,
    k_fg_make INT, k_fg_att INT, k_xp_make INT, k_xp_att INT,
    p_no INT, p_yds INT, p_in20 INT, p_tb INT, p_fc INT, p_blk INT, p_long INT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT pgs.id, pgs.player_id, pgs.game_id,
        p.espn_id, p.name, p.position_code,
        g.espn_id, g.game_date,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int, pgs.pass_sacked,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        pgs.def_solo, pgs.def_ast, pgs.def_sacks, pgs.def_tfl, pgs.def_pd, pgs.def_qb_hits, pgs.def_td, pgs.def_int,
        pgs.ret_kick_no, pgs.ret_kick_yds, pgs.ret_kick_td,
        pgs.ret_punt_no, pgs.ret_punt_yds, pgs.ret_punt_td,
        pgs.k_fg_make, pgs.k_fg_att, pgs.k_xp_make, pgs.k_xp_att,
        pgs.p_no, pgs.p_yds, pgs.p_in20, pgs.p_tb, pgs.p_fc, pgs.p_blk, pgs.p_long,
        pgs.metadata
    FROM player_game_stats pgs
    JOIN players p ON pgs.player_id = p.id
    JOIN games g ON pgs.game_id = g.id
    JOIN team_game_stats ts ON pgs.game_id = ts.game_id
    JOIN teams t ON ts.team_id = t.id
    WHERE pgs.player_id = p_player_id
      AND (t.abbr = p_opponent_abbr
           OR g.home_team_id = (SELECT id FROM teams WHERE abbr = p_opponent_abbr)
           OR g.away_team_id = (SELECT id FROM teams WHERE abbr = p_opponent_abbr))
    ORDER BY g.game_date DESC;
END;
$$;

-- Retrieve player stats for a team
CREATE OR REPLACE FUNCTION fn_get_player_stats_for_team(
    p_team_id UUID
)
RETURNS TABLE(
    id UUID, player_id UUID, game_id UUID,
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_abbr VARCHAR, team_name VARCHAR,
    game_espn_id VARCHAR, game_date TIMESTAMP,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    rush_att INT, rush_yds INT, rush_td INT,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    def_solo INT, def_ast INT, def_sacks NUMERIC(3,1), def_tfl INT, def_pd INT, def_qb_hits INT, def_td INT, def_int INT,
    ret_kick_no INT, ret_kick_yds INT, ret_kick_td INT,
    ret_punt_no INT, ret_punt_yds INT, ret_punt_td INT,
    k_fg_make INT, k_fg_att INT, k_xp_make INT, k_xp_att INT,
    p_no INT, p_yds INT, p_in20 INT, p_tb INT, p_fc INT, p_blk INT, p_long INT,
    metadata JSONB, last_updated TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT pgs.id, pgs.player_id, pgs.game_id,
        p.espn_id, p.name, p.position_code,
        t.abbr, t.full_name,
        g.espn_id, g.game_date,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int, pgs.pass_sacked,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        pgs.def_solo, pgs.def_ast, pgs.def_sacks, pgs.def_tfl, pgs.def_pd, pgs.def_qb_hits, pgs.def_td, pgs.def_int,
        pgs.ret_kick_no, pgs.ret_kick_yds, pgs.ret_kick_td,
        pgs.ret_punt_no, pgs.ret_punt_yds, pgs.ret_punt_td,
        pgs.k_fg_make, pgs.k_fg_att, pgs.k_xp_make, pgs.k_xp_att,
        pgs.p_no, pgs.p_yds, pgs.p_in20, pgs.p_tb, pgs.p_fc, pgs.p_blk, pgs.p_long,
        pgs.metadata, pgs.last_updated
    FROM player_game_stats pgs
    JOIN players p ON pgs.player_id = p.id
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON pgs.game_id = g.id
    JOIN team_game_stats ts ON pgs.game_id = ts.game_id AND ts.team_id = p_team_id
    WHERE p.team_id = p_team_id
    ORDER BY g.game_date DESC, p.name;
END;
$$;

-- Retrieve top players by passing yards for a game
CREATE OR REPLACE FUNCTION fn_get_top_passers(
    p_game_id UUID,
    p_limit INT DEFAULT 5
)
RETURNS TABLE(
    id UUID, player_id UUID, player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    game_espn_id VARCHAR, game_date TIMESTAMP,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, yards INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT pgs.id, pgs.player_id, p.espn_id, p.name, p.position_code,
        g.espn_id, g.game_date,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int,
        pgs.pass_yds AS yards
    FROM player_game_stats pgs
    JOIN players p ON pgs.player_id = p.id
    JOIN games g ON pgs.game_id = g.id
    WHERE pgs.game_id = p_game_id AND pgs.pass_att > 0
    ORDER BY pgs.pass_yds DESC, pgs.pass_td DESC
    LIMIT p_limit;
END;
$$;

-- Retrieve top rushers for a game
CREATE OR REPLACE FUNCTION fn_get_top_rushers(
    p_game_id UUID,
    p_limit INT DEFAULT 5
)
RETURNS TABLE(
    id UUID, player_id UUID, player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    game_espn_id VARCHAR, game_date TIMESTAMP,
    rush_att INT, rush_yds INT, rush_td INT, yards INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT pgs.id, pgs.player_id, p.espn_id, p.name, p.position_code,
        g.espn_id, g.game_date,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        pgs.rush_yds AS yards
    FROM player_game_stats pgs
    JOIN players p ON pgs.player_id = p.id
    JOIN games g ON pgs.game_id = g.id
    WHERE pgs.game_id = p_game_id AND pgs.rush_att > 0
    ORDER BY pgs.rush_yds DESC, pgs.rush_td DESC
    LIMIT p_limit;
END;
$$;

-- Retrieve top receivers for a game
CREATE OR REPLACE FUNCTION fn_get_top_receivers(
    p_game_id UUID,
    p_limit INT DEFAULT 5
)
RETURNS TABLE(
    id UUID, player_id UUID, player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    game_espn_id VARCHAR, game_date TIMESTAMP,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT, yards INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT pgs.id, pgs.player_id, p.espn_id, p.name, p.position_code,
        g.espn_id, g.game_date,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        pgs.rec_yds AS yards
    FROM player_game_stats pgs
    JOIN players p ON pgs.player_id = p.id
    JOIN games g ON pgs.game_id = g.id
    WHERE pgs.game_id = p_game_id AND pgs.rec_receptions > 0
    ORDER BY pgs.rec_yds DESC, pgs.rec_td DESC
    LIMIT p_limit;
END;
$$;

-- Retrieve team scoring leaders for a game
CREATE OR REPLACE FUNCTION fn_get_team_scoring_leaders(
    p_game_id UUID
)
RETURNS TABLE(
    player_id UUID, player_name VARCHAR, td_total INT, fantasy_score NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH all_player_stats AS (
        SELECT pgs.id, pgs.player_id, pgs.game_id, p.espn_id, p.name,
               COALESCE(pgs.pass_td, 0) + COALESCE(pgs.rush_td, 0) +
               COALESCE(pgs.rec_td, 0) + COALESCE(pgs.ret_kick_td, 0) +
               COALESCE(pgs.k_xp_make, 0) + COALESCE(pgs.ret_punt_td, 0) as td_total
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.id
        WHERE pgs.game_id = p_game_id
    )
    SELECT player_id, player_name, td_total, td_total / (SELECT pts_total FROM team_game_stats WHERE game_id = p_game_id) * 2 as fantasy_score
    FROM all_player_stats
    ORDER BY td_total DESC, fantasy_score DESC
    LIMIT 5;
END;
$$;

-- Retrieve game summary with both team stats
CREATE OR REPLACE FUNCTION fn_get_game_summary(
    p_game_id UUID
)
RETURNS TABLE(
    game_espn_id VARCHAR, game_date TIMESTAMP, status_code VARCHAR,
    home_team_id UUID, away_team_id UUID,
    home_team_abbr VARCHAR, home_team_name VARCHAR,
    away_team_abbr VARCHAR, away_team_name VARCHAR,
    home_team_pts INT, home_off_yds INT, home_def_sacks NUMERIC(3,1),
    home_redzone_att INT, home_redzone_td INT, home_int INT, home_turnovers INT,
    away_team_pts INT, away_off_yds INT, away_def_sacks NUMERIC(3,1),
    away_redzone_att INT, away_redzone_td INT, away_int INT, away_turnovers INT,
    winning_team VARCHAR, point_diff INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT g.espn_id, g.game_date, g.status_code,
        g.home_team_id, g.away_team_id,
        t1.abbr, t1.full_name,
        t2.abbr, t2.full_name,
        ts1.pts_total, ts1.off_total_yds, ts1.def_sacks,
        ts1.off_redzone_att, ts1.off_redzone_td,
        ts1.def_int, ts1.total_turnovers,
        ts2.pts_total, ts2.off_total_yds, ts2.def_sacks,
        ts2.off_redzone_att, ts2.off_redzone_td,
        ts2.def_int, ts2.total_turnovers,
        CASE WHEN ts1.pts_total > ts2.pts_total THEN t1.full_name ELSE t2.full_name END,
        CASE WHEN ts1.pts_total > ts2.pts_total THEN ts1.pts_total - ts2.pts_total ELSE ts2.pts_total - ts1.pts_total END
    FROM games g
    JOIN teams t1 ON g.home_team_id = t1.id
    JOIN teams t2 ON g.away_team_id = t2.id
    JOIN team_game_stats ts1 ON ts1.team_id = g.home_team_id AND ts1.game_id = g.id
    JOIN team_game_stats ts2 ON ts2.team_id = g.away_team_id AND ts2.game_id = g.id
    WHERE g.id = p_game_id;
END;
$$;

-- Retrieve top scoring teams
CREATE OR REPLACE FUNCTION fn_get_top_scoring_teams(
    p_season_year INT DEFAULT 2025,
    p_week INT DEFAULT NULL,
    p_limit INT DEFAULT 10
)
RETURNS TABLE(
    team_id UUID, team_abbr VARCHAR, abbr VARCHAR, full_name VARCHAR,
    pts_total INT, off_total_yds INT, def_sacks NUMERIC(3,1), def_int INT, total_turnovers INT,
    off_redzone_att INT, off_redzone_td INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT ts.team_id, t.abbr, t.abbr, t.full_name,
        ts.pts_total, ts.off_total_yds, ts.def_sacks, ts.def_int, ts.total_turnovers,
        ts.off_redzone_att, ts.off_redzone_td
    FROM team_game_stats ts
    JOIN teams t ON ts.team_id = t.id
    JOIN games g ON ts.game_id = g.id
    WHERE g.season_year = p_season_year
      AND (p_week IS NULL OR g.week = p_week)
    GROUP BY ts.team_id, t.abbr, t.full_name,
             ts.pts_total, ts.off_total_yds, ts.def_sacks, ts.def_int, ts.total_turnovers,
             ts.off_redzone_att, ts.off_redzone_td
    ORDER BY ts.pts_total DESC
    LIMIT p_limit;
END;
$$;
