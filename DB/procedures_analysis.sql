-- NFL Fantasy Football Database — Multi-Table Analysis Functions
-- Convenience functions for common analysis patterns
-- Multi-table joins for: players, teams, games, and all stat types

-- ============================================================
-- PLAYER-FOCUSED MULTI-TABLE FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION fn_get_player_game_complete(
    p_player_id UUID DEFAULT NULL,
    p_game_id UUID DEFAULT NULL
)
RETURNS TABLE(
    player_id UUID, player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    player_team_name VARCHAR, player_team_abbr VARCHAR,
    game_id UUID, game_espn_id VARCHAR, home_team_id UUID, away_team_id UUID,
    game_date TIMESTAMP, status_code VARCHAR, season_year INT, week INT,
    game_pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    off_total_yds INT, off_plays INT, off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT, off_possession_secs INT,
    team_def_sacks NUMERIC, team_def_int INT, total_turnovers INT, penalties_count INT, penalties_yds INT,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    rush_att INT, rush_yds INT, rush_td INT,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    def_solo INT, def_ast INT, def_sks NUMERIC, def_tfl INT, def_pd INT, def_qb_hits INT, def_td INT, def_irt INT,
    ret_kick_no INT, ret_kick_yds INT, ret_kick_td INT,
    ret_punt_no INT, ret_punt_yds INT, ret_punt_td INT,
    k_fg_make INT, k_fg_att INT, k_xp_make INT, k_xp_att INT,
    p_no INT, p_yds INT, p_in20 INT, p_tb INT, p_fc INT, p_blk INT, p_long INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id, p.espn_id, p.name, p.position_code,
        t.full_name, t.abbr,
        g.id, g.espn_id, g.home_team_id, g.away_team_id,
        g.game_date, g.status_code, g.season_year, g.week,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
        ts.off_total_yds, ts.off_plays, ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td, ts.off_possession_secs,
        ts.def_sacks, ts.def_int, ts.total_turnovers, ts.penalties_count, ts.penalties_yds,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int, pgs.pass_sacked,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        pgs.def_solo, pgs.def_ast, pgs.def_sacks, pgs.def_tfl, pgs.def_pd, pgs.def_qb_hits, pgs.def_td, pgs.def_int,
        pgs.ret_kick_no, pgs.ret_kick_yds, pgs.ret_kick_td,
        pgs.ret_punt_no, pgs.ret_punt_yds, pgs.ret_punt_td,
        pgs.k_fg_make, pgs.k_fg_att, pgs.k_xp_make, pgs.k_xp_att,
        pgs.p_no, pgs.p_yds, pgs.p_in20, pgs.p_tb, pgs.p_fc, pgs.p_blk, pgs.p_long
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.id = p_game_id
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id) AND ts.game_id = g.id
    JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE p.id = p_player_id
      AND g.id = p_game_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_player_season_complete(
    p_player_id UUID DEFAULT NULL,
    p_season_year INT DEFAULT 2025
)
RETURNS TABLE(
    player_id UUID, player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_name VARCHAR, team_abbr VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP, status_code VARCHAR,
    team_pts_total INT,
    pass_comp BIGINT, pass_att BIGINT, pass_yds BIGINT, pass_td BIGINT, pass_int BIGINT, pass_sacked INT,
    rush_att BIGINT, rush_yds BIGINT, rush_td BIGINT,
    rec_receptions BIGINT, rec_targets BIGINT, rec_yds BIGINT, rec_td BIGINT,
    def_solo BIGINT, def_ast BIGINT, def_sacks NUMERIC, def_tfl BIGINT, def_pd BIGINT, def_qb_hits BIGINT, def_td BIGINT,
    ret_kick_no BIGINT, ret_kick_yds BIGINT, ret_kick_td BIGINT,
    ret_punt_no BIGINT, ret_punt_yds BIGINT, ret_punt_td BIGINT,
    k_fg_make BIGINT, k_fg_att BIGINT, k_xp_make BIGINT, k_xp_att BIGINT,
    p_no BIGINT, p_yds BIGINT,
    games_played BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id, p.espn_id, p.name, p.position_code,
        t.full_name, t.abbr,
        g.season_year, g.week, g.game_date, g.status_code,
        ts.pts_total,
        SUM(pgs.pass_comp), SUM(pgs.pass_att), SUM(pgs.pass_yds), SUM(pgs.pass_td), SUM(pgs.pass_int), MAX(pgs.pass_sacked),
        SUM(pgs.rush_att), SUM(pgs.rush_yds), SUM(pgs.rush_td),
        SUM(pgs.rec_receptions), SUM(pgs.rec_targets), SUM(pgs.rec_yds), SUM(pgs.rec_td),
        SUM(pgs.def_solo), SUM(pgs.def_ast), SUM(pgs.def_sacks), SUM(pgs.def_tfl), SUM(pgs.def_pd), SUM(pgs.def_qb_hits), SUM(pgs.def_td),
        SUM(pgs.ret_kick_no), SUM(pgs.ret_kick_yds), SUM(pgs.ret_kick_td),
        SUM(pgs.ret_punt_no), SUM(pgs.ret_punt_yds), SUM(pgs.ret_punt_td),
        SUM(pgs.k_fg_make), SUM(pgs.k_fg_att), SUM(pgs.k_xp_make), SUM(pgs.k_xp_att),
        SUM(pgs.p_no), SUM(pgs.p_yds),
        COUNT(g.id)
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.season_year = p_season_year
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id) AND ts.game_id = g.id
    JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE p.id = p_player_id
      AND g.season_year = p_season_year
    GROUP BY p.id, p.espn_id, p.name, p.position_code,
             t.full_name, t.abbr, g.season_year, g.week, g.game_date, g.status_code,
             ts.pts_total
    HAVING SUM(pgs.pass_att + pgs.rush_att + pgs.rec_receptions + pgs.ret_kick_no + pgs.p_no + pgs.ret_punt_no) > 0
    ORDER BY g.week;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_player_season_week_by_week(
    p_player_id UUID DEFAULT NULL,
    p_season_year INT DEFAULT 2025
)
RETURNS TABLE(
    player_id UUID, player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_name VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP, status_code VARCHAR,
    team_pts_total INT,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    rush_att INT, rush_yds INT, rush_td INT,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    def_solo INT, def_ast INT, def_sacks NUMERIC, def_tfl INT, def_pd INT, def_qb_hits INT, def_td INT, def_int INT,
    ret_kick_no INT, ret_kick_yds INT, ret_kick_td INT,
    ret_punt_no INT, ret_punt_yds INT, ret_punt_td INT,
    k_fg_make INT, k_fg_att INT, k_xp_make INT, k_xp_att INT,
    p_no INT, p_yds INT, p_in20 INT, p_tb INT, p_fc INT, p_blk INT, p_long INT,
    yards INT, game_date_ts TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id, p.espn_id, p.name, p.position_code,
        t.full_name,
        g.season_year, g.week, g.game_date, g.status_code,
        ts.pts_total,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int, pgs.pass_sacked,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        pgs.def_solo, pgs.def_ast, pgs.def_sacks, pgs.def_tfl, pgs.def_pd, pgs.def_qb_hits, pgs.def_td, pgs.def_int,
        pgs.ret_kick_no, pgs.ret_kick_yds, pgs.ret_kick_td,
        pgs.ret_punt_no, pgs.ret_punt_yds, pgs.ret_punt_td,
        pgs.k_fg_make, pgs.k_fg_att, pgs.k_xp_make, pgs.k_xp_att,
        pgs.p_no, pgs.p_yds, pgs.p_in20, pgs.p_tb, pgs.p_fc, pgs.p_blk, pgs.p_long,
        CASE WHEN pgs.pass_yds > 0 THEN pgs.pass_yds WHEN pgs.rush_yds > 0 THEN pgs.rush_yds WHEN pgs.rec_yds > 0 THEN pgs.rec_yds ELSE 0 END,
        g.game_date
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.season_year = p_season_year
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id) AND ts.game_id = g.id
    LEFT JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE p.id = p_player_id
      AND g.season_year = p_season_year
    ORDER BY g.week, g.game_date;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_player_career_complete(
    p_player_id UUID DEFAULT NULL
)
RETURNS TABLE(
    player_id UUID, player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_name VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP, status_code VARCHAR,
    team_abbr VARCHAR,
    pass_comp BIGINT, pass_att BIGINT, pass_yds BIGINT, pass_td BIGINT, pass_int BIGINT, pass_sacked INT,
    rush_att BIGINT, rush_yds BIGINT, rush_td BIGINT,
    rec_receptions BIGINT, rec_targets BIGINT, rec_yds BIGINT, rec_td BIGINT,
    def_solo BIGINT, def_ast BIGINT, def_sacks NUMERIC, def_tfl BIGINT, def_pd BIGINT, def_qb_hits BIGINT, def_td BIGINT,
    ret_kick_no BIGINT, ret_kick_yds BIGINT, ret_kick_td BIGINT,
    ret_punt_no BIGINT, ret_punt_yds BIGINT, ret_punt_td BIGINT,
    k_fg_make BIGINT, k_fg_att BIGINT, k_xp_make BIGINT, k_xp_att BIGINT,
    p_no BIGINT, p_yds BIGINT,
    games_played BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id, p.espn_id, p.name, p.position_code,
        t.full_name,
        g.season_year, g.week, g.game_date, g.status_code,
        t.abbr,
        SUM(pgs.pass_comp), SUM(pgs.pass_att), SUM(pgs.pass_yds), SUM(pgs.pass_td), SUM(pgs.pass_int), MAX(pgs.pass_sacked),
        SUM(pgs.rush_att), SUM(pgs.rush_yds), SUM(pgs.rush_td),
        SUM(pgs.rec_receptions), SUM(pgs.rec_targets), SUM(pgs.rec_yds), SUM(pgs.rec_td),
        SUM(pgs.def_solo), SUM(pgs.def_ast), SUM(pgs.def_sacks), SUM(pgs.def_tfl), SUM(pgs.def_pd), SUM(pgs.def_qb_hits), SUM(pgs.def_td),
        SUM(pgs.ret_kick_no), SUM(pgs.ret_kick_yds), SUM(pgs.ret_kick_td),
        SUM(pgs.ret_punt_no), SUM(pgs.ret_punt_yds), SUM(pgs.ret_punt_td),
        SUM(pgs.k_fg_make), SUM(pgs.k_fg_att), SUM(pgs.k_xp_make), SUM(pgs.k_xp_att),
        SUM(pgs.p_no), SUM(pgs.p_yds),
        COUNT(g.id)
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.season_year IS NOT NULL
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id) AND ts.game_id = g.id
    LEFT JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE p.id = p_player_id
    GROUP BY p.id, p.espn_id, p.name, p.position_code,
             t.full_name, t.abbr, g.season_year, g.week, g.game_date, g.status_code
    HAVING SUM(pgs.pass_att + pgs.rush_att + pgs.rec_receptions + pgs.ret_kick_no + pgs.p_no + pgs.ret_punt_no) > 0
    ORDER BY g.season_year DESC, g.week DESC;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_player_career_by_team(
    p_player_id UUID DEFAULT NULL
)
RETURNS TABLE(
    player_id UUID, player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_name VARCHAR, team_abbr VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP, status_code VARCHAR,
    team_pts_total INT,
    pass_comp BIGINT, pass_att BIGINT, pass_yds BIGINT, pass_td BIGINT, pass_int BIGINT, pass_sacked INT,
    rush_att BIGINT, rush_yds BIGINT, rush_td BIGINT,
    rec_receptions BIGINT, rec_targets BIGINT, rec_yds BIGINT, rec_td BIGINT,
    def_solo BIGINT, def_ast BIGINT, def_sacks NUMERIC, def_tfl BIGINT, def_pd BIGINT, def_qb_hits BIGINT, def_td BIGINT,
    ret_kick_no BIGINT, ret_kick_yds BIGINT, ret_kick_td BIGINT,
    ret_punt_no BIGINT, ret_punt_yds BIGINT, ret_punt_td BIGINT,
    k_fg_make BIGINT, k_fg_att BIGINT, k_xp_make BIGINT, k_xp_att BIGINT,
    p_no BIGINT, p_yds BIGINT,
    games_played BIGINT,
    stat_leader TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id, p.espn_id, p.name, p.position_code,
        t.full_name, t.abbr,
        g.season_year, g.week, g.game_date, g.status_code,
        ts.pts_total,
        SUM(pgs.pass_comp), SUM(pgs.pass_att), SUM(pgs.pass_yds), SUM(pgs.pass_td), SUM(pgs.pass_int), MAX(pgs.pass_sacked),
        SUM(pgs.rush_att), SUM(pgs.rush_yds), SUM(pgs.rush_td),
        SUM(pgs.rec_receptions), SUM(pgs.rec_targets), SUM(pgs.rec_yds), SUM(pgs.rec_td),
        SUM(pgs.def_solo), SUM(pgs.def_ast), SUM(pgs.def_sacks), SUM(pgs.def_tfl), SUM(pgs.def_pd), SUM(pgs.def_qb_hits), SUM(pgs.def_td),
        SUM(pgs.ret_kick_no), SUM(pgs.ret_kick_yds), SUM(pgs.ret_kick_td),
        SUM(pgs.ret_punt_no), SUM(pgs.ret_punt_yds), SUM(pgs.ret_punt_td),
        SUM(pgs.k_fg_make), SUM(pgs.k_fg_att), SUM(pgs.k_xp_make), SUM(pgs.k_xp_att),
        SUM(pgs.p_no), SUM(pgs.p_yds),
        COUNT(g.id),
        CASE WHEN SUM(pgs.pass_yds) > SUM(pgs.rush_yds) AND SUM(pgs.pass_yds) > SUM(pgs.rec_yds) THEN 'pass'
             WHEN SUM(pgs.rush_yds) > SUM(pgs.pass_yds) AND SUM(pgs.rush_yds) > SUM(pgs.rec_yds) THEN 'rush'
             WHEN SUM(pgs.rec_yds) > SUM(pgs.pass_yds) AND SUM(pgs.rec_yds) > SUM(pgs.rush_yds) THEN 'rec'
             ELSE 'none' END
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.season_year IS NOT NULL
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id) AND ts.game_id = g.id
    LEFT JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE p.id = p_player_id
    GROUP BY p.id, p.espn_id, p.name, p.position_code,
             t.full_name, t.abbr, g.season_year, g.week, g.game_date, g.status_code,
             ts.pts_total
    HAVING SUM(pgs.pass_att + pgs.rush_att + pgs.rec_receptions + pgs.ret_kick_no + pgs.p_no + pgs.ret_punt_no) > 0
    ORDER BY g.season_year DESC, g.week DESC, team_name;
END;
$$;

-- ============================================================
-- TEAM-FOCUSED MULTI-TABLE FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION fn_get_game_both_teams(
    p_game_id UUID DEFAULT NULL
)
RETURNS TABLE(
    game_espn_id VARCHAR, game_date TIMESTAMP, status_code VARCHAR,
    home_team_id UUID, away_team_id UUID, season_year INT, week INT,
    home_pts INT, home_pts_q1 INT, home_pts_q2 INT, home_pts_q3 INT, home_pts_q4 INT, home_pts_ot INT,
    home_td_pass INT, home_td_rush INT, home_td_ret INT, home_td_def INT,
    home_off_yds INT, home_off_plays INT, home_3rd_att INT, home_3rd_make INT,
    home_redzone_att INT, home_redzone_td INT, home_possession_secs INT, home_def_sacks NUMERIC, home_def_int INT,
    home_turnovers INT, home_penalties_count INT, home_penalty_yds INT,
    home_team_name VARCHAR, home_team_abbr VARCHAR,
    away_pts INT, away_pts_q1 INT, away_pts_q2 INT, away_pts_q3 INT, away_pts_q4 INT, away_pts_ot INT,
    away_td_pass INT, away_td_rush INT, away_td_ret INT, away_td_def INT,
    away_off_yds INT, away_off_plays INT, away_3rd_att INT, away_3rd_make INT,
    away_redzone_att INT, away_redzone_td INT, away_possession_secs INT, away_def_sacks NUMERIC, away_def_int INT,
    away_turnovers INT, away_penalties_count INT, away_penalty_yds INT,
    away_team_name VARCHAR, away_team_abbr VARCHAR,
    winning_team VARCHAR, point_margin INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        g.espn_id, g.game_date, g.status_code,
        g.home_team_id, g.away_team_id, g.season_year, g.week,
        home.ts.pts_total, home.ts.pts_q1, home.ts.pts_q2, home.ts.pts_q3, home.ts.pts_q4, home.ts.pts_ot,
        home.ts.td_pass, home.ts.td_rush, home.ts.td_ret, home.ts.td_def,
        home.ts.off_total_yds, home.ts.off_plays, home.ts.off_3rd_att, home.ts.off_3rd_make,
        home.ts.off_redzone_att, home.ts.off_redzone_td, home.ts.off_possession_secs, home.ts.def_sacks, home.ts.def_int,
        home.ts.total_turnovers, home.ts.penalties_count, home.ts.penalties_yds,
        t1.full_name, t1.abbr,
        away.ts.pts_total, away.ts.pts_q1, away.ts.pts_q2, away.ts.pts_q3, away.ts.pts_q4, away.ts.pts_ot,
        away.ts.td_pass, away.ts.td_rush, away.ts.td_ret, away.ts.td_def,
        away.ts.off_total_yds, away.ts.off_plays, away.ts.off_3rd_att, away.ts.off_3rd_make,
        away.ts.off_redzone_att, away.ts.off_redzone_td, away.ts.off_possession_secs, away.ts.def_sacks, away.ts.def_int,
        away.ts.total_turnovers, away.ts.penalties_count, away.ts.penalties_yds,
        t2.full_name, t2.abbr,
        CASE WHEN home.ts.pts_total > away.ts.pts_total THEN t1.full_name ELSE t2.full_name END,
        CASE WHEN home.ts.pts_total > away.ts.pts_total THEN home.ts.pts_total - away.ts.pts_total
             ELSE away.ts.pts_total - home.ts.pts_total END
    FROM games g
    JOIN teams t1 ON g.home_team_id = t1.id
    JOIN teams t2 ON g.away_team_id = t2.id
    JOIN team_game_stats home ON home.team_id = g.home_team_id AND home.game_id = g.id
    JOIN team_game_stats away ON away.team_id = g.away_team_id AND away.game_id = g.id
    WHERE g.id = p_game_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_team_season_complete(
    p_team_id UUID DEFAULT NULL,
    p_season_year INT DEFAULT 2025
)
RETURNS TABLE(
    team_id UUID, team_abbr VARCHAR, team_name VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP, status_code VARCHAR,
    pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass BIGINT, td_rush BIGINT, td_ret BIGINT, td_def BIGINT,
    off_first_downs INT, off_total_yds INT, off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    def_sacks NUMERIC, def_int INT,
    total_turnovers INT,
    penalties_count INT, penalties_yds INT,
    games_played BIGINT,
    season_pts_total BIGINT, season_off_yds BIGINT, season_def_sacks NUMERIC, season_def_int BIGINT,
    season_td_total BIGINT, season_3rd_down_pct BIGINT, season_penalties BIGINT, season_penalty_yds BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id, t.abbr, t.full_name,
        g.season_year, g.week, g.game_date, g.status_code,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        SUM(ts.td_pass), SUM(ts.td_rush), SUM(ts.td_ret), SUM(ts.td_def),
        ts.off_first_downs, ts.off_total_yds, ts.off_plays,
        ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td,
        ts.off_possession_secs,
        ts.def_sacks, ts.def_int,
        ts.total_turnovers,
        ts.penalties_count, ts.penalties_yds,
        COUNT(*),
        SUM(ts.pts_total), SUM(ts.off_total_yds), SUM(ts.def_sacks), SUM(ts.def_int),
        SUM(ts.td_pass + ts.td_rush + ts.td_ret + ts.td_def),
        SUM(ts.off_3rd_att) - SUM(ts.off_3rd_make),
        SUM(ts.penalties_count), SUM(ts.penalties_yds)
    FROM teams t
    JOIN games g ON g.home_team_id = t.id OR g.away_team_id = t.id
    JOIN team_game_stats ts ON ts.team_id = t.id AND ts.game_id = g.id
    WHERE t.id = p_team_id
      AND g.season_year = p_season_year
    GROUP BY t.id, t.abbr, t.full_name,
             g.season_year, g.week, g.game_date, g.status_code,
             ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
             ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
             ts.off_first_downs, ts.off_total_yds, ts.off_plays,
             ts.off_3rd_att, ts.off_3rd_make,
             ts.off_redzone_att, ts.off_redzone_td,
             ts.off_possession_secs,
             ts.def_sacks, ts.def_int,
             ts.total_turnovers,
             ts.penalties_count, ts.penalties_yds
    ORDER BY g.week, g.game_date;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_team_season_week_by_week(
    p_team_id UUID DEFAULT NULL,
    p_season_year INT DEFAULT 2025
)
RETURNS TABLE(
    team_id UUID, team_abbr VARCHAR, team_name VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP, status_code VARCHAR,
    pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    off_first_downs INT, off_total_yds INT, off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    def_sacks NUMERIC, def_int INT,
    total_turnovers INT,
    penalties_count INT, penalties_yds INT,
    metadata JSONB,
    scoring_category TEXT, defense_category TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id, t.abbr, t.full_name,
        g.season_year, g.week, g.game_date, g.status_code,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
        ts.off_first_downs, ts.off_total_yds, ts.off_plays,
        ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td,
        ts.off_possession_secs,
        ts.def_sacks, ts.def_int,
        ts.total_turnovers,
        ts.penalties_count, ts.penalties_yds,
        ts.metadata,
        CASE WHEN ts.off_total_yds > 500 THEN 'high_scoring'
             WHEN ts.off_total_yds < 250 THEN 'low_scoring'
             ELSE 'medium_scoring' END,
        CASE WHEN ts.def_sacks > 5 THEN 'strong_dfs'
             WHEN ts.def_int > 3 THEN 'int_heavy'
             ELSE 'standard_defense' END
    FROM teams t
    JOIN games g ON g.home_team_id = t.id OR g.away_team_id = t.id
    JOIN team_game_stats ts ON ts.team_id = t.id AND ts.game_id = g.id
    WHERE t.id = p_team_id
      AND g.season_year = p_season_year
    ORDER BY g.week, g.game_date;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_team_career_complete(
    p_team_id UUID DEFAULT NULL
)
RETURNS TABLE(
    team_id UUID, team_abbr VARCHAR, team_name VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP, status_code VARCHAR,
    pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass BIGINT, td_rush BIGINT, td_ret BIGINT, td_def BIGINT,
    off_first_downs INT, off_total_yds INT, off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    def_sacks NUMERIC, def_int BIGINT,
    total_turnovers BIGINT,
    penalties_count BIGINT, penalties_yds BIGINT,
    games_played BIGINT,
    career_pts_total BIGINT, career_off_yds BIGINT, career_def_sacks NUMERIC, career_def_int BIGINT,
    career_td_total BIGINT,
    wins BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id, t.abbr, t.full_name,
        g.season_year, g.week, g.game_date, g.status_code,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        SUM(ts.td_pass), SUM(ts.td_rush), SUM(ts.td_ret), SUM(ts.td_def),
        ts.off_first_downs, ts.off_total_yds, ts.off_plays,
        ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td,
        ts.off_possession_secs,
        SUM(ts.def_sacks), SUM(ts.def_int),
        SUM(ts.total_turnovers),
        SUM(ts.penalties_count), SUM(ts.penalties_yds),
        COUNT(*),
        SUM(ts.pts_total), SUM(ts.off_total_yds), SUM(ts.def_sacks), SUM(ts.def_int),
        SUM(ts.td_pass + ts.td_rush + ts.td_ret + ts.td_def),
        SUM(CASE WHEN ts.pts_total > (
            SELECT ts2.pts_total FROM team_game_stats ts2
            JOIN teams t3 ON ts2.team_id = t3.id
            JOIN games g2 ON ts2.game_id = g2.id
            WHERE g2.home_team_id = g.home_team_id OR g2.away_team_id = g.home_team_id
              AND (g.home_team_id = t3.id OR g.away_team_id = t3.id)
              AND ts2.game_id = g.id
        ) THEN 1 ELSE 0 END)
    FROM teams t
    JOIN games g ON g.home_team_id = t.id OR g.away_team_id = t.id
    JOIN team_game_stats ts ON ts.team_id = t.id AND ts.game_id = g.id
    WHERE t.id = p_team_id
    GROUP BY t.id, t.abbr, t.full_name,
             g.season_year, g.week, g.game_date, g.status_code,
             ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
             ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
             ts.off_first_downs, ts.off_total_yds, ts.off_plays,
             ts.off_3rd_att, ts.off_3rd_make,
             ts.off_redzone_att, ts.off_redzone_td,
             ts.off_possession_secs
    HAVING COUNT(*) > 0
    ORDER BY g.season_year DESC, g.week DESC;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_team_vs_opponent(
    p_team_id UUID DEFAULT NULL,
    p_opponent_abbr VARCHAR DEFAULT NULL
)
RETURNS TABLE(
    game_espn_id VARCHAR, game_date TIMESTAMP, status_code VARCHAR,
    team_name VARCHAR, team_abbr VARCHAR,
    opponent_name VARCHAR, opponent_abbr VARCHAR,
    pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    off_first_downs INT, off_total_yds INT, off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    def_sacks NUMERIC, def_int INT,
    total_turnovers INT,
    penalties_count INT, penalties_yds INT,
    result TEXT, point_margin INT,
    opponent_pts INT,
    opp_td_pass INT, opp_td_rush INT, opp_td_ret INT, opp_td_def INT,
    opponent_off_yds INT, opponent_def_sacks NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        g.espn_id, g.game_date, g.status_code,
        t1.full_name, t1.abbr,
        t2.full_name, t2.abbr,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
        ts.off_first_downs, ts.off_total_yds, ts.off_plays,
        ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td,
        ts.off_possession_secs,
        ts.def_sacks, ts.def_int,
        ts.total_turnovers,
        ts.penalties_count, ts.penalties_yds,
        CASE WHEN ts.pts_total > opp.ts.pts_total THEN 'W'
             WHEN ts.pts_total < opp.ts.pts_total THEN 'L'
             ELSE 'T' END,
        ts.pts_total - opp.ts.pts_total,
        opp.ts.pts_total,
        opp.ts.td_pass, opp.ts.td_rush, opp.ts.td_ret, opp.ts.td_def,
        opp.ts.off_total_yds, opp.ts.def_sacks
    FROM teams t1
    JOIN teams t2 ON t2.abbr = p_opponent_abbr
    JOIN games g ON g.home_team_id = t1.id OR g.away_team_id = t1.id
    JOIN team_game_stats ts ON ts.team_id = t1.id
    JOIN team_game_stats opp ON opp.team_id = t2.id AND opp.game_id = g.id
    WHERE t1.id = p_team_id
      AND t2.abbr = p_opponent_abbr
    ORDER BY g.game_date DESC;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_team_season_all_games(
    p_team_id UUID DEFAULT NULL,
    p_season_year INT DEFAULT 2025
)
RETURNS TABLE(
    team_id UUID, team_abbr VARCHAR, team_name VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP, status_code VARCHAR,
    home_team_id UUID, away_team_id UUID,
    pts_total INT, pts_q1 INT, pts_q2 INT, pts_q3 INT, pts_q4 INT, pts_ot INT,
    td_pass INT, td_rush INT, td_ret INT, td_def INT,
    off_first_downs INT, off_total_yds INT, off_plays INT,
    off_3rd_att INT, off_3rd_make INT,
    off_redzone_att INT, off_redzone_td INT,
    off_possession_secs INT,
    def_sacks NUMERIC, def_int INT,
    total_turnovers INT,
    penalties_count INT, penalties_yds INT,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id, t.abbr, t.full_name,
        g.season_year, g.week, g.game_date, g.status_code,
        g.home_team_id, g.away_team_id,
        ts.pts_total, ts.pts_q1, ts.pts_q2, ts.pts_q3, ts.pts_q4, ts.pts_ot,
        ts.td_pass, ts.td_rush, ts.td_ret, ts.td_def,
        ts.off_first_downs, ts.off_total_yds, ts.off_plays,
        ts.off_3rd_att, ts.off_3rd_make,
        ts.off_redzone_att, ts.off_redzone_td,
        ts.off_possession_secs,
        ts.def_sacks, ts.def_int,
        ts.total_turnovers,
        ts.penalties_count, ts.penalties_yds,
        ts.metadata
    FROM teams t
    JOIN games g ON g.home_team_id = t.id OR g.away_team_id = t.id
    JOIN team_game_stats ts ON ts.team_id = t.id AND ts.game_id = g.id
    WHERE t.id = p_team_id
      AND g.season_year = p_season_year
    ORDER BY g.week, g.game_date;
END;
$$;

-- ============================================================
-- POSITION-SPECIFIC ANALYSIS FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION fn_get_game_passing_leaders(
    p_game_id UUID DEFAULT NULL,
    p_limit INT DEFAULT 20
)
RETURNS TABLE(
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_name VARCHAR, game_espn_id VARCHAR, game_date TIMESTAMP,
    pass_comp INT, pass_att INT, pass_yds INT, pass_td INT, pass_int INT, pass_sacked INT,
    ypc NUMERIC, pct NUMERIC, btr NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.espn_id, p.name, p.position_code,
        t.full_name,
        g.espn_id, g.game_date,
        pgs.pass_comp, pgs.pass_att, pgs.pass_yds, pgs.pass_td, pgs.pass_int, pgs.pass_sacked,
        ROUND(CASE WHEN pgs.pass_att > 0 THEN pgs.pass_yds::NUMERIC / pgs.pass_att ELSE 0 END, 1),
        ROUND(CASE WHEN pgs.pass_att > 0 THEN (pgs.pass_td::NUMERIC / pgs.pass_att) * 100 ELSE 0 END, 2),
        CASE WHEN pgs.pass_sacked > 0 THEN (pgs.pass_int::NUMERIC / (pgs.pass_int + pgs.pass_sacked)) * 100 ELSE 0 END
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.id = p_game_id
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id)
    JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE g.id = p_game_id
      AND pgs.pass_att > 0
    ORDER BY pgs.pass_yds DESC, pgs.pass_td DESC
    LIMIT p_limit;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_game_rushing_leaders(
    p_game_id UUID DEFAULT NULL,
    p_limit INT DEFAULT 20
)
RETURNS TABLE(
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_name VARCHAR, game_espn_id VARCHAR, game_date TIMESTAMP,
    rush_att INT, rush_yds INT, rush_td INT,
    ypc NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.espn_id, p.name, p.position_code,
        t.full_name,
        g.espn_id, g.game_date,
        pgs.rush_att, pgs.rush_yds, pgs.rush_td,
        ROUND(CASE WHEN pgs.rush_att > 0 THEN pgs.rush_yds::NUMERIC / pgs.rush_att ELSE 0 END, 1)
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.id = p_game_id
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id)
    JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE g.id = p_game_id
      AND pgs.rush_att > 0
    ORDER BY pgs.rush_yds DESC, pgs.rush_td DESC
    LIMIT p_limit;
END;
$$;

CREATE OR REPLACE FUNCTION fn_get_game_receiving_leaders(
    p_game_id UUID DEFAULT NULL,
    p_limit INT DEFAULT 20
)
RETURNS TABLE(
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_name VARCHAR, game_espn_id VARCHAR, game_date TIMESTAMP,
    rec_receptions INT, rec_targets INT, rec_yds INT, rec_td INT,
    ypr NUMERIC, rtc NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.espn_id, p.name, p.position_code,
        t.full_name,
        g.espn_id, g.game_date,
        pgs.rec_receptions, pgs.rec_targets, pgs.rec_yds, pgs.rec_td,
        ROUND(CASE WHEN pgs.rec_receptions > 0 THEN pgs.rec_yds::NUMERIC / pgs.rec_receptions ELSE 0 END, 1),
        ROUND(CASE WHEN pgs.rec_targets > 0 THEN pgs.rec_receptions::NUMERIC / pgs.rec_targets * 100 ELSE 0 END, 1)
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.id = p_game_id
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id)
    JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE g.id = p_game_id
      AND pgs.rec_receptions > 0
    ORDER BY pgs.rec_yds DESC, pgs.rec_td DESC
    LIMIT p_limit;
END;
$$;

-- ============================================================
-- FANTASY-FRIENDLY ANALYSIS FUNCTIONS
-- ============================================================

CREATE OR REPLACE FUNCTION fn_get_player_fantasy_stats(
    p_player_id UUID DEFAULT NULL
)
RETURNS TABLE(
    player_espn_id VARCHAR, player_name VARCHAR, position_code VARCHAR,
    team_name VARCHAR,
    season_year INT, week INT, game_date TIMESTAMP,
    total_yards NUMERIC,
    pass_td BIGINT, rush_td BIGINT, rec_td BIGINT,
    kick_extra_pts BIGINT, ret_td BIGINT, def_td BIGINT,
    def_int BIGINT, def_sacks NUMERIC, def_qb_hits BIGINT, def_tfl BIGINT, def_tackles BIGINT,
    pass_int BIGINT, def_int_positive BIGINT,
    fantasy_points NUMERIC,
    games_played BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.espn_id, p.name, p.position_code,
        t.full_name,
        g.season_year, g.week, g.game_date,
        COALESCE(SUM(pgs.pass_yds), 0) + COALESCE(SUM(pgs.rush_yds), 0) + COALESCE(SUM(pgs.rec_yds), 0) +
        COALESCE(SUM(pgs.ret_punt_yds), 0) + COALESCE(SUM(pgs.ret_kick_yds), 0),
        COALESCE(SUM(pgs.pass_td), 0),
        COALESCE(SUM(pgs.rush_td), 0),
        COALESCE(SUM(pgs.rec_td), 0),
        COALESCE(SUM(pgs.k_xp_make), 0) + COALESCE(SUM(pgs.k_fg_make), 0),
        COALESCE(SUM(pgs.ret_kick_td), 0) + COALESCE(SUM(pgs.ret_punt_td), 0),
        COALESCE(SUM(pgs.def_td), 0),
        COALESCE(SUM(pgs.def_int), 0),
        COALESCE(SUM(pgs.def_sacks), 0),
        COALESCE(SUM(pgs.def_qb_hits), 0),
        COALESCE(SUM(pgs.def_tfl), 0),
        COALESCE(SUM(pgs.def_solo) + COALESCE(SUM(pgs.def_ast)), 0),
        SUM(CASE WHEN pgs.pass_int > 0 THEN pgs.pass_int ELSE 0 END),
        SUM(CASE WHEN pgs.def_int > 0 THEN pgs.def_int ELSE 0 END),
        (
            COALESCE(SUM(pgs.pass_yds), 0) / 10 +
            COALESCE(SUM(pgs.rush_yds), 0) / 10 +
            COALESCE(SUM(pgs.rec_yds), 0) / 10 +
            COALESCE(SUM(pgs.ret_punt_yds), 0) / 10 +
            COALESCE(SUM(pgs.ret_kick_yds), 0) / 10 +
            COALESCE(SUM(pgs.pass_td), 0) * 4 +
            COALESCE(SUM(pgs.rush_td), 0) * 6 +
            COALESCE(SUM(pgs.rec_td), 0) * 6 +
            COALESCE(SUM(pgs.k_xp_make), 0) * 1 +
            COALESCE(SUM(pgs.k_fg_make), 0) * 3 +
            COALESCE(SUM(pgs.ret_kick_td), 0) * 6 +
            COALESCE(SUM(pgs.ret_punt_td), 0) * 6 +
            COALESCE(SUM(pgs.def_td), 0) * 6 +
            COALESCE(SUM(pgs.def_int), 0) * 2 +
            COALESCE(SUM(pgs.def_sacks), 0) * 2.5 +
            COALESCE(SUM(pgs.def_qb_hits), 0) * 1.5 +
            COALESCE(SUM(pgs.def_tfl), 0) * 1 +
            COALESCE(SUM(pgs.def_solo) + COALESCE(SUM(pgs.def_ast)), 0) * 0.5 -
            (COALESCE(SUM(pgs.pass_int), 0) * 2) -
            COALESCE(SUM(pgs.total_turnovers), 0) * 2
        ),
        COUNT(*)
    FROM players p
    JOIN teams t ON p.team_id = t.id
    JOIN games g ON g.season_year IS NOT NULL
    JOIN team_game_stats ts ON ts.team_id IN (g.home_team_id, g.away_team_id) AND ts.game_id = g.id
    LEFT JOIN player_game_stats pgs ON pgs.player_id = p.id AND pgs.game_id = g.id
    WHERE p.id = p_player_id
    GROUP BY p.espn_id, p.name, p.position_code,
             t.full_name, g.season_year, g.week, g.game_date
    HAVING SUM(CASE WHEN pgs.pass_att > 0 THEN 1 WHEN pgs.rush_att > 0 THEN 1 WHEN pgs.rec_receptions > 0 THEN 1
           WHEN pgs.ret_kick_no > 0 THEN 1 WHEN pgs.ret_punt_no > 0 THEN 1
           WHEN pgs.p_no > 0 THEN 1 WHEN pgs.def_solo > 0 THEN 1 ELSE 0 END) > 0;
END;
$$;
