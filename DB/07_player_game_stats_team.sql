-- Migration 07: Add team_id to player_game_stats
-- Records which team a player was on during each specific game.
-- Without this column, the leaderboard falls back to players.team_id (current team),
-- showing the wrong helmet for players who were traded after a game was ingested.

ALTER TABLE player_game_stats ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES teams(id);

-- Backfill existing rows with the player's current team as a best-effort approximation.
-- Re-ingesting a game will overwrite with the historically correct team.
UPDATE player_game_stats pgs
SET team_id = p.team_id
FROM players p
WHERE pgs.player_id = p.id
  AND pgs.team_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_pgs_team_id ON player_game_stats(team_id);

-- Recreate procedure with new p_team_id parameter (added before p_metadata).
-- All existing positional args ($1-$52) are unchanged; team_id is $53, metadata is $54.
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
