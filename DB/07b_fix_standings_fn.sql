-- Fix fn_get_league_standings: rewrite as LANGUAGE sql to avoid PL/pgSQL
-- variable scope ambiguity on column name "team_id" (RETURNS TABLE vs CTE alias).

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
) LANGUAGE sql AS $$
WITH
-- Inline lookup of median_game flag
league_cfg AS (
    SELECT COALESCE((
        SELECT ls.median_game
        FROM user_api.league_scoring ls
        WHERE ls.league_id = p_league_id AND ls.league_year = p_season_year
    ), FALSE) AS median_game
),
-- One row per team per week (regular season, final games only)
matchup_flat AS (
    SELECT m.week,
           m.home_team_id                  AS mf_team_id,
           m.home_score                    AS team_score,
           m.away_score                    AS opp_score
    FROM user_api.league_weekly_matchups m
    WHERE m.league_id = p_league_id
      AND m.season_year = p_season_year
      AND m.status = 'final'
      AND m.is_playoff = FALSE
    UNION ALL
    SELECT m.week,
           m.away_team_id,
           m.away_score,
           m.home_score
    FROM user_api.league_weekly_matchups m
    WHERE m.league_id = p_league_id
      AND m.season_year = p_season_year
      AND m.status = 'final'
      AND m.is_playoff = FALSE
),
-- Weekly medians
weekly_medians AS (
    SELECT mf.week,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mf.team_score) AS median_score
    FROM matchup_flat mf
    GROUP BY mf.week
),
-- Per-team aggregations
team_stats AS (
    SELECT
        mf.mf_team_id,
        COUNT(*) FILTER (WHERE mf.team_score > mf.opp_score)::INT    AS wins,
        COUNT(*) FILTER (WHERE mf.team_score < mf.opp_score)::INT    AS losses,
        COUNT(*) FILTER (WHERE mf.team_score = mf.opp_score)::INT    AS ties,
        COALESCE(SUM(mf.team_score),        0)                        AS points_for,
        COALESCE(SUM(mf.opp_score),         0)                        AS points_against,
        COALESCE(MAX(mf.team_score),        0)                        AS score_high,
        COALESCE(MIN(mf.team_score),        0)                        AS score_low,
        COALESCE(AVG(mf.team_score),        0)                        AS score_avg,
        COALESCE(STDDEV_POP(mf.team_score), 0)                        AS score_std_dev
    FROM matchup_flat mf
    GROUP BY mf.mf_team_id
),
-- Median wins
median_wins_cte AS (
    SELECT mf.mf_team_id,
           COUNT(*) FILTER (WHERE mf.team_score > wm.median_score)::INT AS wins_vs_median
    FROM matchup_flat mf
    JOIN weekly_medians wm ON mf.week = wm.week
    GROUP BY mf.mf_team_id
),
-- All-play
all_play_cte AS (
    SELECT
        a.mf_team_id,
        COUNT(*) FILTER (WHERE a.team_score > b.team_score)::INT AS all_play_wins,
        COUNT(*) FILTER (WHERE a.team_score < b.team_score)::INT AS all_play_losses
    FROM matchup_flat a
    JOIN matchup_flat b ON a.week = b.week AND a.mf_team_id != b.mf_team_id
    GROUP BY a.mf_team_id
),
-- Streak (gap-and-islands)
results_ranked AS (
    SELECT
        mf.mf_team_id,
        mf.week,
        CASE WHEN mf.team_score > mf.opp_score THEN 'W'
             WHEN mf.team_score < mf.opp_score THEN 'L'
             ELSE 'T' END AS result,
        ROW_NUMBER() OVER (PARTITION BY mf.mf_team_id ORDER BY mf.week DESC) AS rn
    FROM matchup_flat mf
),
results_grouped AS (
    SELECT rr.mf_team_id, rr.week, rr.result, rr.rn,
           rr.rn - ROW_NUMBER() OVER (PARTITION BY rr.mf_team_id, rr.result ORDER BY rr.rn) AS island_id
    FROM results_ranked rr
),
latest_island AS (
    SELECT rg.mf_team_id, rg.island_id AS current_island
    FROM results_grouped rg WHERE rg.rn = 1
),
streak_cte AS (
    SELECT rg.mf_team_id, rg.result AS streak_type, COUNT(*)::INT AS streak_count
    FROM results_grouped rg
    JOIN latest_island li ON rg.mf_team_id = li.mf_team_id AND rg.island_id = li.current_island
    GROUP BY rg.mf_team_id, rg.result
),
-- Leader record for games-behind
best_record AS (
    SELECT MAX(COALESCE(ts.wins, 0) + COALESCE(ts.ties, 0) * 0.5) AS best_pts
    FROM team_stats ts
),
-- Season stats
season_stats AS (
    SELECT ltss.league_team_id, ltss.playoff_seed,
           ltss.is_eliminated, ltss.playoff_result
    FROM user_api.league_team_season_stats ltss
    WHERE ltss.season_year = p_season_year
)
SELECT
    lt.id                                                               AS team_id,
    lt.name                                                             AS team_name,
    lt.abbreviation,
    lt.primary_color,
    COALESCE(ts.wins, 0)                                                AS wins,
    COALESCE(ts.losses, 0)                                              AS losses,
    COALESCE(ts.ties, 0)                                                AS ties,
    CASE
        WHEN COALESCE(ts.wins,0)+COALESCE(ts.losses,0)+COALESCE(ts.ties,0) = 0 THEN 0.000
        ELSE ROUND(
            (COALESCE(ts.wins,0) + COALESCE(ts.ties,0)*0.5) /
            (COALESCE(ts.wins,0)+COALESCE(ts.losses,0)+COALESCE(ts.ties,0)),
        3)
    END                                                                 AS win_pct,
    CASE WHEN lc.median_game THEN COALESCE(mw.wins_vs_median, 0) ELSE 0 END AS wins_vs_median,
    ROUND(COALESCE(ts.points_for,     0), 2)                            AS points_for,
    ROUND(COALESCE(ts.points_against, 0), 2)                            AS points_against,
    ROUND(COALESCE(ts.points_for,0) - COALESCE(ts.points_against,0), 2) AS points_diff,
    ROUND(COALESCE(br.best_pts, 0) - (COALESCE(ts.wins,0)+COALESCE(ts.ties,0)*0.5), 1) AS games_behind,
    sc.streak_type::VARCHAR,
    COALESCE(sc.streak_count, 0)                                        AS streak_count,
    ROUND(COALESCE(ts.score_high,     0), 2)                            AS score_high,
    ROUND(COALESCE(ts.score_low,      0), 2)                            AS score_low,
    ROUND(COALESCE(ts.score_avg,      0), 2)                            AS score_avg,
    ROUND(COALESCE(ts.score_std_dev,  0), 2)                            AS score_std_dev,
    COALESCE(ap.all_play_wins,   0)                                     AS all_play_wins,
    COALESCE(ap.all_play_losses, 0)                                     AS all_play_losses,
    ss.playoff_seed,
    COALESCE(ss.is_eliminated, FALSE)                                   AS is_eliminated,
    ss.playoff_result
FROM user_api.league_teams lt
CROSS JOIN league_cfg lc
LEFT JOIN team_stats ts      ON lt.id = ts.mf_team_id
LEFT JOIN median_wins_cte mw ON lt.id = mw.mf_team_id
LEFT JOIN all_play_cte ap    ON lt.id = ap.mf_team_id
LEFT JOIN streak_cte sc      ON lt.id = sc.mf_team_id
LEFT JOIN season_stats ss    ON lt.id = ss.league_team_id
CROSS JOIN best_record br
WHERE lt.league_id = p_league_id
ORDER BY
    COALESCE(ts.wins, 0) DESC,
    COALESCE(ts.ties, 0)*0.5 DESC,
    ROUND(COALESCE(ts.points_for, 0), 2) DESC;
$$;
