-- League team expansion — stored procedures and functions.
-- Run after 07_league_team_expansion.sql.

-- ---------------------------------------------------------------------------
-- fn_get_league_teams — now includes branding columns
-- ---------------------------------------------------------------------------

DROP FUNCTION IF EXISTS user_api.fn_get_league_teams(UUID);

CREATE FUNCTION user_api.fn_get_league_teams(p_league_id UUID)
RETURNS TABLE (
    id                  UUID,
    name                VARCHAR,
    abbreviation        VARCHAR,
    logo_url            TEXT,
    slogan              VARCHAR,
    primary_color       CHAR(7),
    secondary_color_1   CHAR(7),
    secondary_color_2   CHAR(7),
    created_by_id       UUID,
    created_at          TIMESTAMP,
    owner_count         BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        lt.id,
        lt.name,
        lt.abbreviation,
        lt.logo_url,
        lt.slogan,
        lt.primary_color,
        lt.secondary_color_1,
        lt.secondary_color_2,
        lt.created_by_id,
        lt.created_at,
        COUNT(lto.id) AS owner_count
    FROM user_api.league_teams lt
    LEFT JOIN user_api.league_team_owners lto
        ON lto.league_team_id = lt.id AND lto.is_active = TRUE
    WHERE lt.league_id = p_league_id
    GROUP BY lt.id, lt.name, lt.abbreviation, lt.logo_url, lt.slogan,
             lt.primary_color, lt.secondary_color_1, lt.secondary_color_2,
             lt.created_by_id, lt.created_at
    ORDER BY lt.created_at;
END;
$$ LANGUAGE plpgsql;


-- ---------------------------------------------------------------------------
-- fn_get_league_standings — compute all standings metrics from matchups
-- ---------------------------------------------------------------------------

DROP FUNCTION IF EXISTS user_api.fn_get_league_standings(UUID, INT);

CREATE FUNCTION user_api.fn_get_league_standings(
    p_league_id     UUID,
    p_season_year   INT
)
RETURNS TABLE (
    team_id         UUID,
    team_name       VARCHAR,
    abbreviation    VARCHAR,
    primary_color   CHAR(7),
    wins            INT,
    losses          INT,
    ties            INT,
    win_pct         NUMERIC,
    wins_vs_median  INT,
    points_for      NUMERIC,
    points_against  NUMERIC,
    points_diff     NUMERIC,
    games_behind    NUMERIC,
    streak_type     VARCHAR,
    streak_count    INT,
    score_high      NUMERIC,
    score_low       NUMERIC,
    score_avg       NUMERIC,
    score_std_dev   NUMERIC,
    all_play_wins   INT,
    all_play_losses INT,
    playoff_seed    INT,
    is_eliminated   BOOLEAN,
    playoff_result  VARCHAR
) AS $$
DECLARE
    v_median_game BOOLEAN;
BEGIN
    SELECT ls.median_game INTO v_median_game
    FROM user_api.league_scoring ls
    WHERE ls.league_id = p_league_id AND ls.league_year = p_season_year;
    v_median_game := COALESCE(v_median_game, FALSE);

    RETURN QUERY
    WITH
    -- One row per team per week (regular season, final games only)
    matchup_flat AS (
        SELECT m.week, m.home_team_id AS team_id,
               m.home_score AS team_score, m.away_score AS opp_score
        FROM user_api.league_weekly_matchups m
        WHERE m.league_id = p_league_id AND m.season_year = p_season_year
          AND m.status = 'final' AND m.is_playoff = FALSE
        UNION ALL
        SELECT m.week, m.away_team_id,
               m.away_score, m.home_score
        FROM user_api.league_weekly_matchups m
        WHERE m.league_id = p_league_id AND m.season_year = p_season_year
          AND m.status = 'final' AND m.is_playoff = FALSE
    ),
    -- Weekly medians (for median-game leagues)
    weekly_medians AS (
        SELECT week,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY team_score) AS median_score
        FROM matchup_flat
        GROUP BY week
    ),
    -- Per-team basic aggregations
    team_stats AS (
        SELECT
            mf.team_id,
            COUNT(*) FILTER (WHERE mf.team_score > mf.opp_score)::INT AS wins,
            COUNT(*) FILTER (WHERE mf.team_score < mf.opp_score)::INT AS losses,
            COUNT(*) FILTER (WHERE mf.team_score = mf.opp_score)::INT AS ties,
            COALESCE(SUM(mf.team_score), 0)       AS points_for,
            COALESCE(SUM(mf.opp_score), 0)        AS points_against,
            COALESCE(MAX(mf.team_score), 0)       AS score_high,
            COALESCE(MIN(mf.team_score), 0)       AS score_low,
            COALESCE(AVG(mf.team_score), 0)       AS score_avg,
            COALESCE(STDDEV_POP(mf.team_score), 0) AS score_std_dev
        FROM matchup_flat mf
        GROUP BY mf.team_id
    ),
    -- Median wins (only meaningful when median_game = TRUE)
    median_wins_cte AS (
        SELECT mf.team_id,
               COUNT(*) FILTER (WHERE mf.team_score > wm.median_score)::INT AS wins_vs_median
        FROM matchup_flat mf
        JOIN weekly_medians wm ON mf.week = wm.week
        GROUP BY mf.team_id
    ),
    -- All-play: how many teams would this team beat each week?
    all_play_cte AS (
        SELECT
            a.team_id,
            COUNT(*) FILTER (WHERE a.team_score > b.team_score)::INT AS all_play_wins,
            COUNT(*) FILTER (WHERE a.team_score < b.team_score)::INT AS all_play_losses
        FROM matchup_flat a
        JOIN matchup_flat b ON a.week = b.week AND a.team_id != b.team_id
        GROUP BY a.team_id
    ),
    -- Streak: gap-and-islands on week-ordered results per team
    results_ranked AS (
        SELECT
            mf.team_id, mf.week,
            CASE WHEN mf.team_score > mf.opp_score THEN 'W'
                 WHEN mf.team_score < mf.opp_score THEN 'L'
                 ELSE 'T' END AS result,
            ROW_NUMBER() OVER (PARTITION BY mf.team_id ORDER BY mf.week DESC) AS rn
        FROM matchup_flat mf
    ),
    results_grouped AS (
        SELECT team_id, week, result, rn,
               rn - ROW_NUMBER() OVER (PARTITION BY team_id, result ORDER BY rn) AS island_id
        FROM results_ranked
    ),
    latest_island AS (
        SELECT team_id, island_id AS current_island
        FROM results_grouped WHERE rn = 1
    ),
    streak_cte AS (
        SELECT rg.team_id, rg.result AS streak_type, COUNT(*)::INT AS streak_count
        FROM results_grouped rg
        JOIN latest_island li ON rg.team_id = li.team_id AND rg.island_id = li.current_island
        GROUP BY rg.team_id, rg.result
    ),
    -- Leader record for games-behind calculation
    best_record AS (
        SELECT MAX(COALESCE(ts.wins, 0) + COALESCE(ts.ties, 0) * 0.5) AS best_pts
        FROM team_stats ts
    ),
    -- Season stats (playoff seed, elimination status, result)
    season_stats AS (
        SELECT ltss.league_team_id, ltss.playoff_seed,
               ltss.is_eliminated, ltss.playoff_result
        FROM user_api.league_team_season_stats ltss
        WHERE ltss.season_year = p_season_year
    )
    SELECT
        lt.id                                                   AS team_id,
        lt.name                                                 AS team_name,
        lt.abbreviation,
        lt.primary_color,
        COALESCE(ts.wins, 0)                                    AS wins,
        COALESCE(ts.losses, 0)                                  AS losses,
        COALESCE(ts.ties, 0)                                    AS ties,
        CASE
            WHEN COALESCE(ts.wins,0)+COALESCE(ts.losses,0)+COALESCE(ts.ties,0) = 0 THEN 0.000
            ELSE ROUND(
                (COALESCE(ts.wins,0) + COALESCE(ts.ties,0)*0.5) /
                (COALESCE(ts.wins,0) + COALESCE(ts.losses,0) + COALESCE(ts.ties,0)),
                3)
        END                                                     AS win_pct,
        CASE WHEN v_median_game THEN COALESCE(mw.wins_vs_median,0) ELSE 0 END AS wins_vs_median,
        ROUND(COALESCE(ts.points_for,    0), 2)                 AS points_for,
        ROUND(COALESCE(ts.points_against,0), 2)                 AS points_against,
        ROUND(COALESCE(ts.points_for,0)-COALESCE(ts.points_against,0), 2) AS points_diff,
        ROUND(br.best_pts-(COALESCE(ts.wins,0)+COALESCE(ts.ties,0)*0.5), 1) AS games_behind,
        COALESCE(sc.streak_type, NULL)::VARCHAR                 AS streak_type,
        COALESCE(sc.streak_count, 0)                            AS streak_count,
        ROUND(COALESCE(ts.score_high,    0), 2)                 AS score_high,
        ROUND(COALESCE(ts.score_low,     0), 2)                 AS score_low,
        ROUND(COALESCE(ts.score_avg,     0), 2)                 AS score_avg,
        ROUND(COALESCE(ts.score_std_dev, 0), 2)                 AS score_std_dev,
        COALESCE(ap.all_play_wins,   0)                         AS all_play_wins,
        COALESCE(ap.all_play_losses, 0)                         AS all_play_losses,
        ss.playoff_seed,
        COALESCE(ss.is_eliminated, FALSE)                       AS is_eliminated,
        ss.playoff_result
    FROM user_api.league_teams lt
    LEFT JOIN team_stats ts         ON lt.id = ts.team_id
    LEFT JOIN median_wins_cte mw    ON lt.id = mw.team_id
    LEFT JOIN all_play_cte ap       ON lt.id = ap.team_id
    LEFT JOIN streak_cte sc         ON lt.id = sc.team_id
    LEFT JOIN season_stats ss       ON lt.id = ss.league_team_id
    CROSS JOIN best_record br
    WHERE lt.league_id = p_league_id
    ORDER BY
        COALESCE(ts.wins,0) DESC,
        COALESCE(ts.ties,0)*0.5 DESC,
        ROUND(COALESCE(ts.points_for,0), 2) DESC;
END;
$$ LANGUAGE plpgsql;


-- ---------------------------------------------------------------------------
-- usp_update_team_branding — PATCH branding fields on a league team
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE user_api.usp_update_team_branding(
    p_team_id           UUID,
    p_league_id         UUID,
    p_abbreviation      VARCHAR(5),
    p_logo_url          TEXT,
    p_slogan            VARCHAR(200),
    p_primary_color     CHAR(7),
    p_secondary_color_1 CHAR(7),
    p_secondary_color_2 CHAR(7)
) LANGUAGE plpgsql AS $$
BEGIN
    UPDATE user_api.league_teams
    SET
        abbreviation      = COALESCE(p_abbreviation,      abbreviation),
        logo_url          = COALESCE(p_logo_url,          logo_url),
        slogan            = COALESCE(p_slogan,            slogan),
        primary_color     = COALESCE(p_primary_color,     primary_color),
        secondary_color_1 = COALESCE(p_secondary_color_1, secondary_color_1),
        secondary_color_2 = COALESCE(p_secondary_color_2, secondary_color_2),
        updated_at        = NOW()
    WHERE id = p_team_id AND league_id = p_league_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Team % not found in league %', p_team_id, p_league_id;
    END IF;
END;
$$;


-- ---------------------------------------------------------------------------
-- usp_create_matchup — schedule a matchup for a week
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.usp_create_matchup(
    p_league_id     UUID,
    p_season_year   INT,
    p_week          INT,
    p_home_team_id  UUID,
    p_away_team_id  UUID,
    p_is_playoff    BOOLEAN DEFAULT FALSE
) RETURNS UUID LANGUAGE plpgsql AS $$
DECLARE
    v_matchup_id UUID;
BEGIN
    INSERT INTO user_api.league_weekly_matchups
        (league_id, season_year, week, home_team_id, away_team_id, is_playoff)
    VALUES
        (p_league_id, p_season_year, p_week, p_home_team_id, p_away_team_id, p_is_playoff)
    RETURNING id INTO v_matchup_id;

    RETURN v_matchup_id;
END;
$$;


-- ---------------------------------------------------------------------------
-- usp_update_matchup_score — update scores and optionally set status to 'final'
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE user_api.usp_update_matchup_score(
    p_matchup_id    UUID,
    p_league_id     UUID,
    p_home_score    NUMERIC(8,2),
    p_away_score    NUMERIC(8,2),
    p_home_proj     NUMERIC(8,2),
    p_away_proj     NUMERIC(8,2),
    p_status        VARCHAR(20)
) LANGUAGE plpgsql AS $$
BEGIN
    UPDATE user_api.league_weekly_matchups
    SET
        home_score     = COALESCE(p_home_score, home_score),
        away_score     = COALESCE(p_away_score, away_score),
        home_projected = COALESCE(p_home_proj,  home_projected),
        away_projected = COALESCE(p_away_proj,  away_projected),
        status         = COALESCE(p_status,     status)
    WHERE id = p_matchup_id AND league_id = p_league_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Matchup % not found', p_matchup_id;
    END IF;
END;
$$;


-- ---------------------------------------------------------------------------
-- usp_upsert_team_season_stats — create or update a team's season stats row
-- ---------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE user_api.usp_upsert_team_season_stats(
    p_league_team_id        UUID,
    p_season_year           INT,
    p_waiver_position       INT         DEFAULT NULL,
    p_waiver_budget_start   INT         DEFAULT NULL,
    p_waiver_budget_used    INT         DEFAULT NULL,
    p_total_moves           INT         DEFAULT NULL,
    p_playoff_seed          INT         DEFAULT NULL,
    p_is_eliminated         BOOLEAN     DEFAULT NULL,
    p_playoff_result        VARCHAR(30) DEFAULT NULL
) LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO user_api.league_team_season_stats
        (league_team_id, season_year, waiver_position, waiver_budget_start,
         waiver_budget_used, total_moves, playoff_seed, is_eliminated, playoff_result)
    VALUES
        (p_league_team_id, p_season_year,
         p_waiver_position, p_waiver_budget_start,
         COALESCE(p_waiver_budget_used, 0), COALESCE(p_total_moves, 0),
         p_playoff_seed, COALESCE(p_is_eliminated, FALSE), p_playoff_result)
    ON CONFLICT (league_team_id, season_year) DO UPDATE
        SET waiver_position      = COALESCE(EXCLUDED.waiver_position,    league_team_season_stats.waiver_position),
            waiver_budget_start  = COALESCE(EXCLUDED.waiver_budget_start, league_team_season_stats.waiver_budget_start),
            waiver_budget_used   = COALESCE(p_waiver_budget_used,         league_team_season_stats.waiver_budget_used),
            total_moves          = COALESCE(p_total_moves,                league_team_season_stats.total_moves),
            playoff_seed         = COALESCE(EXCLUDED.playoff_seed,        league_team_season_stats.playoff_seed),
            is_eliminated        = COALESCE(p_is_eliminated,              league_team_season_stats.is_eliminated),
            playoff_result       = COALESCE(EXCLUDED.playoff_result,      league_team_season_stats.playoff_result);
END;
$$;


-- ---------------------------------------------------------------------------
-- usp_log_transaction — append a transaction record
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.usp_log_transaction(
    p_league_id         UUID,
    p_league_team_id    UUID,
    p_transaction_type  VARCHAR(20),
    p_player_id         UUID,
    p_related_team_id   UUID,
    p_waiver_bid        INT,
    p_week              INT,
    p_season_year       INT,
    p_status            VARCHAR(20) DEFAULT 'approved'
) RETURNS UUID LANGUAGE plpgsql AS $$
DECLARE
    v_tx_id UUID;
BEGIN
    INSERT INTO user_api.league_transactions
        (league_id, league_team_id, transaction_type, player_id, related_team_id,
         waiver_bid, week, season_year, status)
    VALUES
        (p_league_id, p_league_team_id, p_transaction_type, p_player_id,
         p_related_team_id, p_waiver_bid, p_week, p_season_year, p_status)
    RETURNING id INTO v_tx_id;

    RETURN v_tx_id;
END;
$$;


-- ---------------------------------------------------------------------------
-- usp_record_draft_pick — record a draft pick
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.usp_record_draft_pick(
    p_league_id         UUID,
    p_draft_year        INT,
    p_pick_number       INT,
    p_round_number      INT,
    p_pick_in_round     INT,
    p_league_team_id    UUID,
    p_player_id         UUID,
    p_bid_amount        INT         DEFAULT NULL,
    p_nominated_by      UUID        DEFAULT NULL
) RETURNS UUID LANGUAGE plpgsql AS $$
DECLARE
    v_pick_id UUID;
BEGIN
    INSERT INTO user_api.league_draft_picks
        (league_id, draft_year, pick_number, round_number, pick_in_round,
         league_team_id, player_id, bid_amount, nominated_by, drafted_at)
    VALUES
        (p_league_id, p_draft_year, p_pick_number, p_round_number, p_pick_in_round,
         p_league_team_id, p_player_id, p_bid_amount, p_nominated_by, NOW())
    ON CONFLICT (league_id, draft_year, pick_number) DO UPDATE
        SET player_id      = EXCLUDED.player_id,
            league_team_id = EXCLUDED.league_team_id,
            bid_amount     = EXCLUDED.bid_amount,
            nominated_by   = EXCLUDED.nominated_by,
            drafted_at     = NOW()
    RETURNING id INTO v_pick_id;

    RETURN v_pick_id;
END;
$$;
