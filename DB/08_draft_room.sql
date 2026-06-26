-- Draft Room migration: state machine, order, queue, and stored procedures
-- Run after all previous migrations (07_*)

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_api.league_draft_state (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id           UUID NOT NULL REFERENCES user_api.leagues(id) ON DELETE CASCADE,
    draft_year          INT NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','active','paused','completed')),
    current_pick        INT NOT NULL DEFAULT 1,
    pick_started_at     TIMESTAMPTZ,
    paused_seconds_left INT,
    total_rounds        INT NOT NULL DEFAULT 15,
    total_teams         INT NOT NULL DEFAULT 0,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    state_hash          VARCHAR(64) NOT NULL DEFAULT '',
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (league_id, draft_year)
);

CREATE TABLE IF NOT EXISTS user_api.league_draft_order (
    league_id       UUID NOT NULL REFERENCES user_api.leagues(id) ON DELETE CASCADE,
    draft_year      INT NOT NULL,
    slot_position   INT NOT NULL,
    league_team_id  UUID NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    PRIMARY KEY (league_id, draft_year, slot_position)
);

CREATE TABLE IF NOT EXISTS user_api.league_draft_queue (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id       UUID NOT NULL REFERENCES user_api.leagues(id) ON DELETE CASCADE,
    draft_year      INT NOT NULL,
    league_team_id  UUID NOT NULL REFERENCES user_api.league_teams(id) ON DELETE CASCADE,
    player_id       UUID NOT NULL REFERENCES public.players(id) ON DELETE CASCADE,
    priority        INT NOT NULL,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (league_id, draft_year, league_team_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_draft_queue_team
    ON user_api.league_draft_queue(league_id, draft_year, league_team_id, priority);

-- ---------------------------------------------------------------------------
-- fn_get_draft_room — single polling call returns state + order + picks as JSON
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.fn_get_draft_room(
    p_league_id  UUID,
    p_draft_year INT
)
RETURNS JSON AS $$
BEGIN
    RETURN json_build_object(
        'state', (
            SELECT row_to_json(s) FROM (
                SELECT
                    ds.id                                    AS state_id,
                    ds.status,
                    ds.current_pick,
                    ds.total_rounds * ds.total_teams         AS total_picks,
                    ds.pick_started_at,
                    ds.paused_seconds_left,
                    COALESCE(lds.seconds_per_pick, 90)       AS seconds_per_pick,
                    COALESCE(lds.third_round_reversal, FALSE) AS third_round_reversal,
                    ds.started_at,
                    ds.completed_at,
                    ds.state_hash
                FROM user_api.league_draft_state ds
                LEFT JOIN user_api.league_draft_settings lds
                    ON lds.league_id = ds.league_id AND lds.league_year = ds.draft_year
                WHERE ds.league_id = p_league_id AND ds.draft_year = p_draft_year
            ) s
        ),
        'order', (
            SELECT COALESCE(json_agg(o ORDER BY o.slot_position), '[]'::json)
            FROM (
                SELECT
                    do_.slot_position,
                    do_.league_team_id,
                    lt.name AS team_name
                FROM user_api.league_draft_order do_
                JOIN user_api.league_teams lt ON lt.id = do_.league_team_id
                WHERE do_.league_id = p_league_id AND do_.draft_year = p_draft_year
            ) o
        ),
        'picks', (
            SELECT COALESCE(json_agg(pk ORDER BY pk.pick_number), '[]'::json)
            FROM (
                SELECT
                    dp.pick_number,
                    dp.round_number,
                    dp.pick_in_round,
                    dp.league_team_id,
                    dp.player_id,
                    p.name         AS player_name,
                    p.position_code,
                    t.abbr         AS team_abbr,
                    dp.drafted_at
                FROM user_api.league_draft_picks dp
                LEFT JOIN public.players p ON p.id = dp.player_id
                LEFT JOIN public.teams t ON t.id = p.team_id
                WHERE dp.league_id = p_league_id AND dp.draft_year = p_draft_year
            ) pk
        )
    );
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- fn_get_draft_available_players — undrafted players with search/filter
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.fn_get_draft_available_players(
    p_league_id  UUID,
    p_draft_year INT,
    p_name       VARCHAR DEFAULT NULL,
    p_position   VARCHAR DEFAULT NULL,
    p_limit      INT     DEFAULT 50,
    p_offset     INT     DEFAULT 0
)
RETURNS TABLE (
    player_id     UUID,
    espn_id       VARCHAR,
    name          VARCHAR,
    position_code VARCHAR,
    team_abbr     VARCHAR,
    team_name     VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.espn_id,
        p.name,
        p.position_code,
        t.abbr,
        t.full_name
    FROM public.players p
    LEFT JOIN public.teams t ON t.id = p.team_id
    WHERE
        (p_name IS NULL OR p.name ILIKE '%' || p_name || '%')
        AND (p_position IS NULL OR p.position_code = p_position)
        AND p.id NOT IN (
            SELECT dp.player_id
            FROM user_api.league_draft_picks dp
            WHERE dp.league_id = p_league_id
              AND dp.draft_year = p_draft_year
              AND dp.player_id IS NOT NULL
        )
    ORDER BY p.name
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- usp_set_draft_order — commissioner sets team slot order
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.usp_set_draft_order(
    p_league_id  UUID,
    p_draft_year INT,
    p_team_ids   UUID[]
)
RETURNS VOID AS $$
BEGIN
    DELETE FROM user_api.league_draft_order
    WHERE league_id = p_league_id AND draft_year = p_draft_year;

    INSERT INTO user_api.league_draft_order (league_id, draft_year, slot_position, league_team_id)
    SELECT p_league_id, p_draft_year, ordinality, t.id
    FROM unnest(p_team_ids) WITH ORDINALITY AS t(id, ordinality);
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- usp_start_draft — initialize state machine and pre-seed pick slots
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.usp_start_draft(
    p_league_id  UUID,
    p_draft_year INT
)
RETURNS UUID AS $$
DECLARE
    v_state_id     UUID;
    v_team_count   INT;
    v_total_rounds INT;
    v_reversal     BOOL;
    v_pick         INT;
    v_round        INT;
    v_pick_in_rnd  INT;
    v_slot         INT;
    v_r3_offset    INT;
    v_team_id      UUID;
BEGIN
    SELECT COUNT(*) INTO v_team_count
    FROM user_api.league_draft_order
    WHERE league_id = p_league_id AND draft_year = p_draft_year;

    IF v_team_count = 0 THEN
        RAISE EXCEPTION 'Draft order not set — commissioner must set order before starting';
    END IF;

    -- Total rounds = total roster spots (excluding IR)
    SELECT COALESCE(
        (SELECT qb + rb + wr + te + flex + superflex + k + dst + bench
             + idp_dl + idp_dt + idp_edge + idp_lb + idp_ilb + idp_db + idp_cb + idp_s
         FROM user_api.league_roster_config
         WHERE league_id = p_league_id AND league_year = p_draft_year),
        15
    ) INTO v_total_rounds;

    SELECT COALESCE(third_round_reversal, FALSE) INTO v_reversal
    FROM user_api.league_draft_settings
    WHERE league_id = p_league_id AND league_year = p_draft_year;

    -- Create or reset state row
    INSERT INTO user_api.league_draft_state
        (league_id, draft_year, status, current_pick, pick_started_at,
         total_rounds, total_teams, started_at, state_hash)
    VALUES
        (p_league_id, p_draft_year, 'active', 1, now(),
         v_total_rounds, v_team_count, now(), md5(gen_random_uuid()::TEXT))
    ON CONFLICT (league_id, draft_year) DO UPDATE
        SET status          = 'active',
            current_pick    = 1,
            pick_started_at = now(),
            total_rounds    = v_total_rounds,
            total_teams     = v_team_count,
            started_at      = now(),
            completed_at    = NULL,
            paused_seconds_left = NULL,
            state_hash      = md5(gen_random_uuid()::TEXT),
            updated_at      = now()
    RETURNING id INTO v_state_id;

    -- Clear existing pick shells
    DELETE FROM user_api.league_draft_picks
    WHERE league_id = p_league_id AND draft_year = p_draft_year;

    -- Pre-seed pick shells with snake order
    FOR v_pick IN 1..(v_total_rounds * v_team_count) LOOP
        v_round       := ceil(v_pick::FLOAT / v_team_count);
        v_pick_in_rnd := v_pick - (v_round - 1) * v_team_count;

        IF v_reversal THEN
            -- Rounds 1-2 both go forward; round 3+ snakes starting with reverse
            IF v_round <= 2 THEN
                v_slot := v_pick_in_rnd;
            ELSE
                v_r3_offset := v_round - 3;  -- 0-based
                IF v_r3_offset % 2 = 0 THEN
                    v_slot := v_team_count - v_pick_in_rnd + 1;  -- reverse
                ELSE
                    v_slot := v_pick_in_rnd;                     -- forward
                END IF;
            END IF;
        ELSE
            -- Standard snake: odd rounds forward, even rounds reverse
            IF v_round % 2 = 1 THEN
                v_slot := v_pick_in_rnd;
            ELSE
                v_slot := v_team_count - v_pick_in_rnd + 1;
            END IF;
        END IF;

        SELECT league_team_id INTO v_team_id
        FROM user_api.league_draft_order
        WHERE league_id = p_league_id AND draft_year = p_draft_year
          AND slot_position = v_slot;

        INSERT INTO user_api.league_draft_picks
            (league_id, draft_year, pick_number, round_number, pick_in_round, league_team_id)
        VALUES
            (p_league_id, p_draft_year, v_pick, v_round, v_pick_in_rnd, v_team_id);
    END LOOP;

    RETURN v_state_id;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- usp_make_pick — record a player selection and advance draft state
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.usp_make_pick(
    p_league_id   UUID,
    p_draft_year  INT,
    p_pick_number INT,
    p_player_id   UUID,
    p_acting_team UUID  -- NULL means commissioner bypass (skip turn validation)
)
RETURNS TABLE (
    new_pick_number INT,
    draft_completed BOOL,
    state_hash      VARCHAR
) AS $$
DECLARE
    v_state         RECORD;
    v_expected_team UUID;
    v_total_picks   INT;
    v_new_pick      INT;
    v_completed     BOOL := FALSE;
    v_hash          VARCHAR;
BEGIN
    SELECT * INTO v_state
    FROM user_api.league_draft_state
    WHERE league_id = p_league_id AND draft_year = p_draft_year
    FOR UPDATE;

    IF v_state IS NULL THEN
        RAISE EXCEPTION 'Draft not found for league % year %', p_league_id, p_draft_year;
    END IF;
    IF v_state.status NOT IN ('active') THEN
        RAISE EXCEPTION 'Draft is not active (status: %)', v_state.status;
    END IF;
    IF v_state.current_pick != p_pick_number THEN
        RAISE EXCEPTION 'Pick % is no longer current (current is %)', p_pick_number, v_state.current_pick;
    END IF;

    -- Validate turn (skip if commissioner bypass)
    IF p_acting_team IS NOT NULL THEN
        SELECT league_team_id INTO v_expected_team
        FROM user_api.league_draft_picks
        WHERE league_id = p_league_id AND draft_year = p_draft_year AND pick_number = p_pick_number;

        IF v_expected_team IS DISTINCT FROM p_acting_team THEN
            RAISE EXCEPTION 'Not your turn — expected team %, got %', v_expected_team, p_acting_team;
        END IF;
    END IF;

    -- Ensure player not already drafted
    IF EXISTS (
        SELECT 1 FROM user_api.league_draft_picks
        WHERE league_id = p_league_id AND draft_year = p_draft_year AND player_id = p_player_id
    ) THEN
        RAISE EXCEPTION 'Player % already drafted in this league', p_player_id;
    END IF;

    -- Record the pick
    UPDATE user_api.league_draft_picks
    SET player_id  = p_player_id,
        drafted_at = now()
    WHERE league_id = p_league_id AND draft_year = p_draft_year AND pick_number = p_pick_number;

    -- Remove player from all queues in this draft
    DELETE FROM user_api.league_draft_queue
    WHERE league_id = p_league_id AND draft_year = p_draft_year AND player_id = p_player_id;

    v_total_picks := v_state.total_rounds * v_state.total_teams;
    v_new_pick    := p_pick_number + 1;

    IF v_new_pick > v_total_picks THEN
        -- Draft complete — auto-populate rosters
        v_completed := TRUE;
        v_hash      := md5('completed-' || gen_random_uuid()::TEXT);

        UPDATE user_api.league_draft_state
        SET status       = 'completed',
            current_pick = v_new_pick,
            pick_started_at = NULL,
            completed_at = now(),
            state_hash   = v_hash,
            updated_at   = now()
        WHERE league_id = p_league_id AND draft_year = p_draft_year;

        INSERT INTO user_api.roster_players (league_team_id, player_id, slot_position, added_at)
        SELECT dp.league_team_id, dp.player_id, p.position_code, dp.drafted_at
        FROM user_api.league_draft_picks dp
        JOIN public.players p ON p.id = dp.player_id
        WHERE dp.league_id = p_league_id AND dp.draft_year = p_draft_year
          AND dp.player_id IS NOT NULL
        ON CONFLICT (league_team_id, player_id) DO NOTHING;
    ELSE
        v_hash := md5('active-' || v_new_pick::TEXT || '-' || gen_random_uuid()::TEXT);

        UPDATE user_api.league_draft_state
        SET current_pick    = v_new_pick,
            pick_started_at = now(),
            state_hash      = v_hash,
            updated_at      = now()
        WHERE league_id = p_league_id AND draft_year = p_draft_year;
    END IF;

    RETURN QUERY SELECT v_new_pick, v_completed, v_hash;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- usp_autopick — pick top queue item or first available player
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.usp_autopick(
    p_league_id  UUID,
    p_draft_year INT
)
RETURNS TABLE (
    new_pick_number INT,
    draft_completed BOOL,
    state_hash      VARCHAR,
    player_picked   UUID
) AS $$
DECLARE
    v_state       RECORD;
    v_on_clock    UUID;
    v_player_id   UUID;
BEGIN
    SELECT * INTO v_state
    FROM user_api.league_draft_state
    WHERE league_id = p_league_id AND draft_year = p_draft_year;

    IF v_state IS NULL OR v_state.status != 'active' THEN
        RAISE EXCEPTION 'Draft is not active';
    END IF;

    -- Which team is on the clock?
    SELECT league_team_id INTO v_on_clock
    FROM user_api.league_draft_picks
    WHERE league_id = p_league_id AND draft_year = p_draft_year
      AND pick_number = v_state.current_pick;

    -- Try top queue item for that team (not yet drafted)
    SELECT q.player_id INTO v_player_id
    FROM user_api.league_draft_queue q
    WHERE q.league_id = p_league_id AND q.draft_year = p_draft_year
      AND q.league_team_id = v_on_clock
      AND q.player_id NOT IN (
          SELECT dp.player_id FROM user_api.league_draft_picks dp
          WHERE dp.league_id = p_league_id AND dp.draft_year = p_draft_year
            AND dp.player_id IS NOT NULL
      )
    ORDER BY q.priority
    LIMIT 1;

    -- Fall back to first available player alphabetically
    IF v_player_id IS NULL THEN
        SELECT p.id INTO v_player_id
        FROM public.players p
        WHERE p.id NOT IN (
            SELECT dp.player_id FROM user_api.league_draft_picks dp
            WHERE dp.league_id = p_league_id AND dp.draft_year = p_draft_year
              AND dp.player_id IS NOT NULL
        )
        ORDER BY p.name
        LIMIT 1;
    END IF;

    IF v_player_id IS NULL THEN
        RAISE EXCEPTION 'No players available to autopick';
    END IF;

    RETURN QUERY
    SELECT r.new_pick_number, r.draft_completed, r.state_hash, v_player_id
    FROM user_api.usp_make_pick(p_league_id, p_draft_year, v_state.current_pick, v_player_id, NULL) r;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- usp_pause_draft / usp_resume_draft
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION user_api.usp_pause_draft(
    p_league_id  UUID,
    p_draft_year INT
)
RETURNS VOID AS $$
DECLARE
    v_state   RECORD;
    v_elapsed INT;
    v_left    INT;
BEGIN
    SELECT ds.*, COALESCE(lds.seconds_per_pick, 90) AS secs_per_pick
    INTO v_state
    FROM user_api.league_draft_state ds
    LEFT JOIN user_api.league_draft_settings lds
        ON lds.league_id = ds.league_id AND lds.league_year = ds.draft_year
    WHERE ds.league_id = p_league_id AND ds.draft_year = p_draft_year
    FOR UPDATE OF ds;

    IF v_state IS NULL OR v_state.status != 'active' THEN
        RAISE EXCEPTION 'Draft is not active';
    END IF;

    v_elapsed := EXTRACT(EPOCH FROM (now() - v_state.pick_started_at))::INT;
    v_left    := GREATEST(0, v_state.secs_per_pick - v_elapsed);

    UPDATE user_api.league_draft_state
    SET status              = 'paused',
        paused_seconds_left = v_left,
        state_hash          = md5('paused-' || gen_random_uuid()::TEXT),
        updated_at          = now()
    WHERE league_id = p_league_id AND draft_year = p_draft_year;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION user_api.usp_resume_draft(
    p_league_id  UUID,
    p_draft_year INT
)
RETURNS VOID AS $$
DECLARE
    v_secs_left INT;
    v_secs_per  INT;
BEGIN
    SELECT ds.paused_seconds_left, COALESCE(lds.seconds_per_pick, 90)
    INTO v_secs_left, v_secs_per
    FROM user_api.league_draft_state ds
    LEFT JOIN user_api.league_draft_settings lds
        ON lds.league_id = ds.league_id AND lds.league_year = ds.draft_year
    WHERE ds.league_id = p_league_id AND ds.draft_year = p_draft_year;

    IF v_secs_left IS NULL THEN
        v_secs_left := v_secs_per;
    END IF;

    -- Set pick_started_at so that (now - pick_started_at) = elapsed = secs_per - secs_left
    UPDATE user_api.league_draft_state
    SET status              = 'active',
        pick_started_at     = now() - ((v_secs_per - v_secs_left) * INTERVAL '1 second'),
        paused_seconds_left = NULL,
        state_hash          = md5('resumed-' || gen_random_uuid()::TEXT),
        updated_at          = now()
    WHERE league_id = p_league_id AND draft_year = p_draft_year AND status = 'paused';
END;
$$ LANGUAGE plpgsql;
