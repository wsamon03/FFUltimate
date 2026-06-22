-- NFL Fantasy Football Database — Stored Procedures
-- All procedures use upsert semantics (insert or update)
-- for dimension tables keyed on espn_id.
-- Fact tables are keyed on their business unique constraints.

-- ============================================================
-- LOOKUP TABLE PROCEDURES
-- ============================================================

-- Seed game_status entries (run once per environment)
CREATE OR REPLACE PROCEDURE usp_seed_game_status()
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO game_status (status_code, description) VALUES
        ('scheduled', 'Game has not started'),
        ('live',     'Game is in progress'),
        ('final',    'Game is complete')
    ON CONFLICT (status_code) DO NOTHING;
END;
$$;

-- Seed player_position entries (run once per environment)
CREATE OR REPLACE PROCEDURE usp_seed_player_position()
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO player_position (position_code, description) VALUES
        ('QB', 'Quarterback'),
        ('RB', 'Running Back'),
        ('WR', 'Wide Receiver'),
        ('TE', 'Tight End'),
        ('K',  'Kicker'),
        ('DL', 'Defensive Lineman'),
        ('LB', 'Linebacker'),
        ('CB', 'Cornerback'),
        ('S',  'Safety'),
        ('DP', 'Defensive Player'),
        ('P',  'Punter'),
        ('HS', 'Defensive Specialist'),
        ('',   'Non-position / Special'),
        ('C',  'Center'),
        ('DE', 'Defensive End'),
        ('DT', 'Defensive Tackle'),
        ('FB', 'Fullback'),
        ('G',  'Guard'),
        ('LS', 'Long Snapper'),
        ('OT', 'Offensive Tackle'),
        ('PK', 'Placekicker')
    ON CONFLICT (position_code) DO NOTHING;
END;
$$;

-- ============================================================
-- TEAMS
-- ============================================================

CREATE OR REPLACE PROCEDURE usp_upsert_team(
    p_espn_id         VARCHAR,
    p_abbr            VARCHAR,
    p_full_name       VARCHAR,
    p_game_espn_id    VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_team_id UUID;
    v_has_id  BOOLEAN;
BEGIN
    -- Check if team with this abbr already exists
    SELECT id, (espn_id IS NOT NULL) INTO v_team_id, v_has_id
    FROM teams WHERE abbr = p_abbr LIMIT 1;

    IF v_team_id IS NOT NULL THEN
        -- Update existing team
        UPDATE teams SET
            abbr      = p_abbr,
            full_name = p_full_name,
            espn_id   = COALESCE(espn_id, p_espn_id),
            game_team_espn_ids = COALESCE(
                game_team_espn_ids || ARRAY[p_espn_id],
                ARRAY[p_espn_id]
            )
        WHERE id = v_team_id
        AND (
            abbr <> p_abbr
            OR full_name <> p_full_name
            OR NOT p_espn_id = ANY(COALESCE(game_team_espn_ids, ARRAY[]::VARCHAR[]))
        );
    ELSE
        -- Insert new team
        INSERT INTO teams (espn_id, abbr, full_name, game_team_espn_ids)
            VALUES (p_espn_id, p_abbr, p_full_name, ARRAY[p_espn_id]);
    END IF;
END;
$$;

-- ============================================================
-- PLAYERS
-- ============================================================

CREATE OR REPLACE PROCEDURE usp_upsert_player(
    p_espn_id     VARCHAR,
    p_name        VARCHAR,
    p_position_code VARCHAR,
    p_team_id     UUID
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO players (espn_id, name, position_code, team_id)
        VALUES (p_espn_id, p_name, COALESCE(p_position_code, ''), p_team_id)
    ON CONFLICT (espn_id) DO UPDATE SET
        name            = EXCLUDED.name,
        -- Never overwrite a known position with NULL/empty (ESPN omits position for some stat categories)
        position_code   = CASE
            WHEN EXCLUDED.position_code IS NOT NULL AND EXCLUDED.position_code <> ''
            THEN EXCLUDED.position_code
            ELSE players.position_code
        END,
        team_id         = EXCLUDED.team_id
    WHERE players.name <> EXCLUDED.name
       OR (EXCLUDED.position_code IS NOT NULL AND EXCLUDED.position_code <> '' AND players.position_code IS DISTINCT FROM EXCLUDED.position_code)
       OR players.team_id <> EXCLUDED.team_id;
END;
$$;

-- ============================================================
-- GAMES
-- ============================================================

CREATE OR REPLACE PROCEDURE usp_upsert_game(
    p_espn_id       VARCHAR,
    p_status_code   VARCHAR,
    p_game_date     TIMESTAMP,
    p_home_espn_id  VARCHAR,
    p_away_espn_id  VARCHAR,
    p_home_score    INT,
    p_away_score    INT,
    p_week          INT,
    p_season_year   INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_home_team_id UUID;
    v_away_team_id UUID;
BEGIN
    -- Resolve team UUIDs via espn_id matching (checks espn_id column and game_team_espn_ids array)
    SELECT id INTO v_home_team_id FROM teams WHERE espn_id = p_home_espn_id OR p_home_espn_id = ANY(COALESCE(game_team_espn_ids, ARRAY[]::VARCHAR[])) LIMIT 1;
    SELECT id INTO v_away_team_id FROM teams WHERE espn_id = p_away_espn_id OR p_away_espn_id = ANY(COALESCE(game_team_espn_ids, ARRAY[]::VARCHAR[])) LIMIT 1;

    IF v_home_team_id IS NULL OR v_away_team_id IS NULL THEN
        RAISE EXCEPTION 'Could not resolve home team (espn_id=%) or away team (espn_id=%)', p_home_espn_id, p_away_espn_id;
    END IF;

    INSERT INTO games (espn_id, status_code, game_date, home_espn_id, away_espn_id, home_team_id, away_team_id, home_score, away_score, week, season_year)
        VALUES (p_espn_id, p_status_code, p_game_date, p_home_espn_id, p_away_espn_id, v_home_team_id, v_away_team_id, p_home_score, p_away_score, p_week, p_season_year)
    ON CONFLICT (espn_id) DO UPDATE SET
        status_code    = EXCLUDED.status_code,
        game_date      = EXCLUDED.game_date,
        home_espn_id   = EXCLUDED.home_espn_id,
        away_espn_id   = EXCLUDED.away_espn_id,
        home_team_id   = EXCLUDED.home_team_id,
        away_team_id   = EXCLUDED.away_team_id,
        week           = EXCLUDED.week,
        season_year    = EXCLUDED.season_year
    WHERE games.status_code <> EXCLUDED.status_code
       OR games.game_date <> EXCLUDED.game_date
       OR games.home_espn_id <> EXCLUDED.home_espn_id
       OR games.away_espn_id <> EXCLUDED.away_espn_id
       OR games.home_team_id <> EXCLUDED.home_team_id
       OR games.away_team_id <> EXCLUDED.away_team_id
       OR games.week <> EXCLUDED.week
       OR games.season_year <> EXCLUDED.season_year
       OR games.home_score <> EXCLUDED.home_score
       OR games.away_score <> EXCLUDED.away_score;
END;
$$;

-- ============================================================
-- TEAM GAME STATS
-- ============================================================

CREATE OR REPLACE PROCEDURE usp_upsert_team_game_stats(
    p_game_id          UUID,
    p_team_id          UUID,
    p_pts_total        INT,
    p_pts_q1           INT,
    p_pts_q2           INT,
    p_pts_q3           INT,
    p_pts_q4           INT,
    p_pts_ot           INT,
    p_td_pass          INT,
    p_td_rush          INT,
    p_td_ret           INT,
    p_td_def           INT,
    p_off_first_downs  INT,
    p_off_total_yds    INT,
    p_off_plays        INT,
    p_off_3rd_att      INT,
    p_off_3rd_make     INT,
    p_off_redzone_att  INT,
    p_off_redzone_td   INT,
    p_off_possession_secs INT,
    p_def_sacks        NUMERIC,
    p_def_int          INT,
    p_total_turnovers  INT,
    p_penalties_count  INT,
    p_penalties_yds    INT,
    p_metadata         JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO team_game_stats (
        game_id, team_id,
        pts_total, pts_q1, pts_q2, pts_q3, pts_q4, pts_ot,
        td_pass, td_rush, td_ret, td_def,
        off_first_downs, off_total_yds, off_plays,
        off_3rd_att, off_3rd_make,
        off_redzone_att, off_redzone_td,
        off_possession_secs,
        def_sacks, def_int,
        total_turnovers,
        penalties_count, penalties_yds,
        metadata
    ) VALUES (
        p_game_id, p_team_id,
        p_pts_total, p_pts_q1, p_pts_q2, p_pts_q3, p_pts_q4, p_pts_ot,
        p_td_pass, p_td_rush, p_td_ret, p_td_def,
        p_off_first_downs, p_off_total_yds, p_off_plays,
        p_off_3rd_att, p_off_3rd_make,
        p_off_redzone_att, p_off_redzone_td,
        p_off_possession_secs,
        p_def_sacks, p_def_int,
        p_total_turnovers,
        p_penalties_count, p_penalties_yds,
        p_metadata
    )
    ON CONFLICT (game_id, team_id) DO UPDATE SET
        pts_total         = EXCLUDED.pts_total,
        pts_q1            = EXCLUDED.pts_q1,
        pts_q2            = EXCLUDED.pts_q2,
        pts_q3            = EXCLUDED.pts_q3,
        pts_q4            = EXCLUDED.pts_q4,
        pts_ot            = EXCLUDED.pts_ot,
        td_pass           = EXCLUDED.td_pass,
        td_rush           = EXCLUDED.td_rush,
        td_ret            = EXCLUDED.td_ret,
        td_def            = EXCLUDED.td_def,
        off_first_downs   = EXCLUDED.off_first_downs,
        off_total_yds     = EXCLUDED.off_total_yds,
        off_plays         = EXCLUDED.off_plays,
        off_3rd_att       = EXCLUDED.off_3rd_att,
        off_3rd_make      = EXCLUDED.off_3rd_make,
        off_redzone_att   = EXCLUDED.off_redzone_att,
        off_redzone_td    = EXCLUDED.off_redzone_td,
        off_possession_secs = EXCLUDED.off_possession_secs,
        def_sacks         = EXCLUDED.def_sacks,
        def_int           = EXCLUDED.def_int,
        total_turnovers   = EXCLUDED.total_turnovers,
        penalties_count   = EXCLUDED.penalties_count,
        penalties_yds     = EXCLUDED.penalties_yds,
        metadata          = EXCLUDED.metadata,
        created_at        = CURRENT_TIMESTAMP;
END;
$$;

-- ============================================================
-- PLAYER GAME STATS
-- ============================================================

DROP PROCEDURE IF EXISTS usp_upsert_player_game_stats;

CREATE OR REPLACE PROCEDURE usp_upsert_player_game_stats(
    p_player_id      UUID,
    p_game_id        UUID,
    -- Passing
    p_pass_comp      INT,
    p_pass_att       INT,
    p_pass_yds       INT,
    p_pass_td        INT,
    p_pass_int       INT,
    p_pass_sacked    INT,
    p_pass_long      INT,
    p_pass_qbr       NUMERIC(5,2),
    p_pass_rating    NUMERIC(5,2),
    -- Rushing
    p_rush_att       INT,
    p_rush_yds       INT,
    p_rush_td        INT,
    p_rush_long      INT,
    -- Receiving
    p_rec_receptions INT,
    p_rec_targets    INT,
    p_rec_yds        INT,
    p_rec_td         INT,
    p_rec_long       INT,
    -- Fumbles
    p_fum_total      INT,
    p_fum_lost       INT,
    p_fum_rec        INT,
    -- Defense
    p_def_solo       INT,
    p_def_ast        INT,
    p_def_sacks      NUMERIC(3,1),
    p_def_tfl        INT,
    p_def_pd         INT,
    p_def_qb_hits    INT,
    p_def_td         INT,
    p_def_int        INT,
    p_def_int_yds    INT,
    -- Kick Returns
    p_ret_kick_no    INT,
    p_ret_kick_yds   INT,
    p_ret_kick_td    INT,
    p_ret_kick_long  INT,
    -- Punt Returns
    p_ret_punt_no    INT,
    p_ret_punt_yds   INT,
    p_ret_punt_td    INT,
    p_ret_punt_long  INT,
    -- Kicking
    p_k_fg_make      INT,
    p_k_fg_att       INT,
    p_k_fg_long      INT,
    p_k_xp_make      INT,
    p_k_xp_att       INT,
    -- Punting
    p_p_no           INT,
    p_p_yds          INT,
    p_p_in20         INT,
    p_p_tb           INT,
    p_p_fc           INT,
    p_p_blk          INT,
    p_p_long         INT,
    p_team_id        UUID,
    p_metadata       JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO player_game_stats (
        player_id, game_id, team_id,
        pass_comp, pass_att, pass_yds, pass_td, pass_int, pass_sacked,
        pass_long, pass_qbr, pass_rating,
        rush_att, rush_yds, rush_td, rush_long,
        rec_receptions, rec_targets, rec_yds, rec_td, rec_long,
        fum_total, fum_lost, fum_rec,
        def_solo, def_ast, def_sacks, def_tfl, def_pd, def_qb_hits, def_td, def_int,
        def_int_yds,
        ret_kick_no, ret_kick_yds, ret_kick_td, ret_kick_long,
        ret_punt_no, ret_punt_yds, ret_punt_td, ret_punt_long,
        k_fg_make, k_fg_att, k_fg_long, k_xp_make, k_xp_att,
        p_no, p_yds, p_in20, p_tb, p_fc, p_blk, p_long,
        metadata
    ) VALUES (
        p_player_id, p_game_id, p_team_id,
        p_pass_comp, p_pass_att, p_pass_yds, p_pass_td, p_pass_int, p_pass_sacked,
        p_pass_long, p_pass_qbr, p_pass_rating,
        p_rush_att, p_rush_yds, p_rush_td, p_rush_long,
        p_rec_receptions, p_rec_targets, p_rec_yds, p_rec_td, p_rec_long,
        p_fum_total, p_fum_lost, p_fum_rec,
        p_def_solo, p_def_ast, p_def_sacks, p_def_tfl, p_def_pd, p_def_qb_hits, p_def_td, p_def_int,
        p_def_int_yds,
        p_ret_kick_no, p_ret_kick_yds, p_ret_kick_td, p_ret_kick_long,
        p_ret_punt_no, p_ret_punt_yds, p_ret_punt_td, p_ret_punt_long,
        p_k_fg_make, p_k_fg_att, p_k_fg_long, p_k_xp_make, p_k_xp_att,
        p_p_no, p_p_yds, p_p_in20, p_p_tb, p_p_fc, p_p_blk, p_p_long,
        p_metadata
    )
    ON CONFLICT (player_id, game_id) DO UPDATE SET
        team_id        = COALESCE(EXCLUDED.team_id, player_game_stats.team_id),
        pass_comp      = COALESCE(EXCLUDED.pass_comp, player_game_stats.pass_comp),
        pass_att       = COALESCE(EXCLUDED.pass_att, player_game_stats.pass_att),
        pass_yds       = COALESCE(EXCLUDED.pass_yds, player_game_stats.pass_yds),
        pass_td        = COALESCE(EXCLUDED.pass_td, player_game_stats.pass_td),
        pass_int       = COALESCE(EXCLUDED.pass_int, player_game_stats.pass_int),
        pass_sacked    = COALESCE(EXCLUDED.pass_sacked, player_game_stats.pass_sacked),
        pass_long      = COALESCE(EXCLUDED.pass_long, player_game_stats.pass_long),
        pass_qbr       = COALESCE(EXCLUDED.pass_qbr, player_game_stats.pass_qbr),
        pass_rating    = COALESCE(EXCLUDED.pass_rating, player_game_stats.pass_rating),
        rush_att       = COALESCE(EXCLUDED.rush_att, player_game_stats.rush_att),
        rush_yds       = COALESCE(EXCLUDED.rush_yds, player_game_stats.rush_yds),
        rush_td        = COALESCE(EXCLUDED.rush_td, player_game_stats.rush_td),
        rush_long      = COALESCE(EXCLUDED.rush_long, player_game_stats.rush_long),
        rec_receptions = COALESCE(EXCLUDED.rec_receptions, player_game_stats.rec_receptions),
        rec_targets    = COALESCE(EXCLUDED.rec_targets, player_game_stats.rec_targets),
        rec_yds        = COALESCE(EXCLUDED.rec_yds, player_game_stats.rec_yds),
        rec_td         = COALESCE(EXCLUDED.rec_td, player_game_stats.rec_td),
        rec_long       = COALESCE(EXCLUDED.rec_long, player_game_stats.rec_long),
        fum_total      = COALESCE(EXCLUDED.fum_total, player_game_stats.fum_total),
        fum_lost       = COALESCE(EXCLUDED.fum_lost, player_game_stats.fum_lost),
        fum_rec        = COALESCE(EXCLUDED.fum_rec, player_game_stats.fum_rec),
        def_solo       = COALESCE(EXCLUDED.def_solo, player_game_stats.def_solo),
        def_ast        = COALESCE(EXCLUDED.def_ast, player_game_stats.def_ast),
        def_sacks      = COALESCE(EXCLUDED.def_sacks, player_game_stats.def_sacks),
        def_tfl        = COALESCE(EXCLUDED.def_tfl, player_game_stats.def_tfl),
        def_pd         = COALESCE(EXCLUDED.def_pd, player_game_stats.def_pd),
        def_qb_hits    = COALESCE(EXCLUDED.def_qb_hits, player_game_stats.def_qb_hits),
        def_td         = COALESCE(EXCLUDED.def_td, player_game_stats.def_td),
        def_int        = COALESCE(EXCLUDED.def_int, player_game_stats.def_int),
        def_int_yds    = COALESCE(EXCLUDED.def_int_yds, player_game_stats.def_int_yds),
        ret_kick_no    = COALESCE(EXCLUDED.ret_kick_no, player_game_stats.ret_kick_no),
        ret_kick_yds   = COALESCE(EXCLUDED.ret_kick_yds, player_game_stats.ret_kick_yds),
        ret_kick_td    = COALESCE(EXCLUDED.ret_kick_td, player_game_stats.ret_kick_td),
        ret_kick_long  = COALESCE(EXCLUDED.ret_kick_long, player_game_stats.ret_kick_long),
        ret_punt_no    = COALESCE(EXCLUDED.ret_punt_no, player_game_stats.ret_punt_no),
        ret_punt_yds   = COALESCE(EXCLUDED.ret_punt_yds, player_game_stats.ret_punt_yds),
        ret_punt_td    = COALESCE(EXCLUDED.ret_punt_td, player_game_stats.ret_punt_td),
        ret_punt_long  = COALESCE(EXCLUDED.ret_punt_long, player_game_stats.ret_punt_long),
        k_fg_make      = COALESCE(EXCLUDED.k_fg_make, player_game_stats.k_fg_make),
        k_fg_att       = COALESCE(EXCLUDED.k_fg_att, player_game_stats.k_fg_att),
        k_fg_long      = COALESCE(EXCLUDED.k_fg_long, player_game_stats.k_fg_long),
        k_xp_make      = COALESCE(EXCLUDED.k_xp_make, player_game_stats.k_xp_make),
        k_xp_att       = COALESCE(EXCLUDED.k_xp_att, player_game_stats.k_xp_att),
        p_no           = COALESCE(EXCLUDED.p_no, player_game_stats.p_no),
        p_yds          = COALESCE(EXCLUDED.p_yds, player_game_stats.p_yds),
        p_in20         = COALESCE(EXCLUDED.p_in20, player_game_stats.p_in20),
        p_tb           = COALESCE(EXCLUDED.p_tb, player_game_stats.p_tb),
        p_fc           = COALESCE(EXCLUDED.p_fc, player_game_stats.p_fc),
        p_blk          = COALESCE(EXCLUDED.p_blk, player_game_stats.p_blk),
        p_long         = COALESCE(EXCLUDED.p_long, player_game_stats.p_long),
        metadata       = EXCLUDED.metadata,
        last_updated   = CURRENT_TIMESTAMP;
END;
$$;

