-- User API stored procedures and functions
-- Naming convention: usp_* for writes, fn_get_* for reads (matches procedures.sql)

-- ---------------------------------------------------------------------------
-- AUTH / USER
-- ---------------------------------------------------------------------------

-- Upsert a user on OAuth login. Returns the user's UUID.
CREATE OR REPLACE FUNCTION user_api.usp_upsert_user(
    p_provider      VARCHAR(20),
    p_provider_sub  VARCHAR(255),
    p_email         VARCHAR(255),
    p_display_name  VARCHAR(255),
    p_avatar_url    TEXT
) RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    INSERT INTO user_api.users (provider, provider_sub, email, display_name, avatar_url)
    VALUES (p_provider, p_provider_sub, p_email, p_display_name, p_avatar_url)
    ON CONFLICT (provider, provider_sub) DO UPDATE
        SET last_login_at = NOW(),
            display_name  = EXCLUDED.display_name,
            avatar_url    = EXCLUDED.avatar_url
    RETURNING id INTO v_user_id;

    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql;

-- Store a refresh token (only the SHA-256 hash is persisted).
CREATE OR REPLACE PROCEDURE user_api.usp_store_refresh_token(
    p_user_id   UUID,
    p_token_hash VARCHAR(64),
    p_expires_at TIMESTAMP,
    p_user_agent TEXT,
    p_ip         INET
) AS $$
BEGIN
    INSERT INTO user_api.refresh_tokens (user_id, token_hash, expires_at, user_agent, ip_address)
    VALUES (p_user_id, p_token_hash, p_expires_at, p_user_agent, p_ip);
END;
$$ LANGUAGE plpgsql;

-- Revoke a refresh token by its hash.
CREATE OR REPLACE PROCEDURE user_api.usp_revoke_refresh_token(
    p_token_hash VARCHAR(64)
) AS $$
BEGIN
    UPDATE user_api.refresh_tokens
    SET    revoked = TRUE
    WHERE  token_hash = p_token_hash;
END;
$$ LANGUAGE plpgsql;

-- Delete all expired or revoked tokens (run periodically).
CREATE OR REPLACE PROCEDURE user_api.usp_cleanup_expired_tokens() AS $$
BEGIN
    DELETE FROM user_api.refresh_tokens
    WHERE  expires_at < NOW() OR revoked = TRUE;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- LOCAL AUTH
-- ---------------------------------------------------------------------------

-- Register a new local (email/password) user and store the credential atomically.
-- Returns the new user UUID.
-- Raises a UniqueViolationError (23505) on (provider, provider_sub) if the email
-- is already registered as a local account — caller converts to HTTP 409.
CREATE OR REPLACE FUNCTION user_api.usp_register_local_user(
    p_email         VARCHAR(255),
    p_display_name  VARCHAR(255),
    p_password_hash VARCHAR(72)
) RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    INSERT INTO user_api.users (provider, provider_sub, email, display_name, avatar_url)
    VALUES ('local', p_email, p_email, p_display_name, NULL)
    RETURNING id INTO v_user_id;

    INSERT INTO user_api.local_credentials (user_id, password_hash)
    VALUES (v_user_id, p_password_hash);

    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql;

-- Return (user_id, password_hash, is_active) for a local login attempt.
-- Returns no rows if the email does not exist as a local user.
CREATE OR REPLACE FUNCTION user_api.fn_get_local_credentials(
    p_email VARCHAR(255)
) RETURNS TABLE (
    user_id       UUID,
    password_hash VARCHAR(72),
    is_active     BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, lc.password_hash, u.is_active
    FROM user_api.users u
    JOIN user_api.local_credentials lc ON lc.user_id = u.id
    WHERE u.provider = 'local'
      AND u.email    = p_email;
END;
$$ LANGUAGE plpgsql;

-- Update last_login_at after a successful local login.
CREATE OR REPLACE PROCEDURE user_api.usp_update_last_login(
    p_user_id UUID
) AS $$
BEGIN
    UPDATE user_api.users SET last_login_at = NOW() WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- LEAGUES
-- ---------------------------------------------------------------------------

-- Create a league. Returns new league UUID.
CREATE OR REPLACE FUNCTION user_api.usp_create_league(
    p_name       VARCHAR(150),
    p_created_by UUID
) RETURNS UUID AS $$
DECLARE
    v_league_id UUID;
BEGIN
    INSERT INTO user_api.leagues (name, created_by)
    VALUES (p_name, p_created_by)
    RETURNING id INTO v_league_id;

    RETURN v_league_id;
END;
$$ LANGUAGE plpgsql;

-- Create a league team and auto-insert the creator as commissioner.
CREATE OR REPLACE FUNCTION user_api.usp_create_league_team(
    p_league_id     UUID,
    p_created_by_id UUID,
    p_name          VARCHAR(100)
) RETURNS UUID AS $$
DECLARE
    v_team_id UUID;
BEGIN
    INSERT INTO user_api.league_teams (league_id, created_by_id, name)
    VALUES (p_league_id, p_created_by_id, p_name)
    RETURNING id INTO v_team_id;

    -- Creator automatically becomes the team's commissioner
    INSERT INTO user_api.league_team_owners (league_team_id, user_id, is_commissioner)
    VALUES (v_team_id, p_created_by_id, TRUE);

    RETURN v_team_id;
END;
$$ LANGUAGE plpgsql;

-- Add (or update) an owner on a league team.
CREATE OR REPLACE PROCEDURE user_api.usp_add_league_team_owner(
    p_league_team_id     UUID,
    p_user_id            UUID,
    p_is_commissioner    BOOLEAN,
    p_display_name       VARCHAR(100),
    p_is_email_displayed BOOLEAN
) AS $$
BEGIN
    INSERT INTO user_api.league_team_owners
        (league_team_id, user_id, is_commissioner, user_display_name, is_email_displayed)
    VALUES
        (p_league_team_id, p_user_id, p_is_commissioner, p_display_name, p_is_email_displayed)
    ON CONFLICT (league_team_id, user_id) DO UPDATE
        SET is_commissioner    = EXCLUDED.is_commissioner,
            user_display_name  = EXCLUDED.user_display_name,
            is_email_displayed = EXCLUDED.is_email_displayed;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- READ FUNCTIONS
-- ---------------------------------------------------------------------------

-- All leagues a user participates in (as creator or as an owner of any team).
CREATE OR REPLACE FUNCTION user_api.fn_get_user_leagues(p_user_id UUID)
RETURNS TABLE (
    league_id   UUID,
    league_name VARCHAR,
    created_by  UUID,
    created_at  TIMESTAMP,
    team_count  BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        l.id,
        l.name,
        l.created_by,
        l.created_at,
        COUNT(DISTINCT lt.id) AS team_count
    FROM user_api.leagues l
    LEFT JOIN user_api.league_teams lt ON lt.league_id = l.id
    LEFT JOIN user_api.league_team_owners lto ON lto.league_team_id = lt.id AND lto.is_active = TRUE
    WHERE l.created_by = p_user_id
       OR lto.user_id = p_user_id
    GROUP BY l.id, l.name, l.created_by, l.created_at
    ORDER BY l.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- All teams in a league with owner summary.
CREATE OR REPLACE FUNCTION user_api.fn_get_league_teams(p_league_id UUID)
RETURNS TABLE (
    team_id         UUID,
    team_name       VARCHAR,
    created_by_id   UUID,
    created_at      TIMESTAMP,
    owner_count     BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        lt.id,
        lt.name,
        lt.created_by_id,
        lt.created_at,
        COUNT(lto.id) AS owner_count
    FROM user_api.league_teams lt
    LEFT JOIN user_api.league_team_owners lto ON lto.league_team_id = lt.id AND lto.is_active = TRUE
    WHERE lt.league_id = p_league_id
    GROUP BY lt.id, lt.name, lt.created_by_id, lt.created_at
    ORDER BY lt.created_at;
END;
$$ LANGUAGE plpgsql;

-- All owners of a team with their settings.
CREATE OR REPLACE FUNCTION user_api.fn_get_team_owners(p_league_team_id UUID)
RETURNS TABLE (
    user_id             UUID,
    email               VARCHAR,
    display_name        VARCHAR,
    avatar_url          TEXT,
    is_commissioner     BOOLEAN,
    is_active           BOOLEAN,
    user_display_name   VARCHAR,
    is_email_displayed  BOOLEAN,
    joined_at           TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.email,
        u.display_name,
        u.avatar_url,
        lto.is_commissioner,
        lto.is_active,
        lto.user_display_name,
        lto.is_email_displayed,
        lto.joined_at
    FROM user_api.league_team_owners lto
    JOIN user_api.users u ON u.id = lto.user_id
    WHERE lto.league_team_id = p_league_team_id
    ORDER BY lto.is_commissioner DESC, lto.joined_at;
END;
$$ LANGUAGE plpgsql;

-- Full roster for a team with player and NFL team details.
CREATE OR REPLACE FUNCTION user_api.fn_get_team_roster(p_league_team_id UUID)
RETURNS TABLE (
    roster_player_id  UUID,
    player_id         UUID,
    player_name       VARCHAR,
    position_code     VARCHAR,
    nfl_team_abbr     VARCHAR,
    nfl_team_name     VARCHAR,
    slot_position     VARCHAR,
    added_at          TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        rp.id,
        p.id,
        p.name,
        p.position_code,
        t.abbr,
        t.full_name,
        rp.slot_position,
        rp.added_at
    FROM user_api.roster_players rp
    JOIN public.players p ON p.id = rp.player_id
    LEFT JOIN public.teams t ON t.id = p.team_id
    WHERE rp.league_team_id = p_league_team_id
    ORDER BY rp.slot_position NULLS LAST, p.name;
END;
$$ LANGUAGE plpgsql;

-- Started lineup for a team in a specific week.
CREATE OR REPLACE FUNCTION user_api.fn_get_team_lineup(
    p_league_team_id UUID,
    p_season_year    INT,
    p_week           INT
)
RETURNS TABLE (
    player_id     UUID,
    player_name   VARCHAR,
    position_code VARCHAR,
    nfl_team_abbr VARCHAR,
    slot_position VARCHAR,
    set_at        TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        p.position_code,
        t.abbr,
        wl.slot_position,
        wl.set_at
    FROM user_api.weekly_lineups wl
    JOIN public.players p ON p.id = wl.player_id
    LEFT JOIN public.teams t ON t.id = p.team_id
    WHERE wl.league_team_id = p_league_team_id
      AND wl.season_year    = p_season_year
      AND wl.week           = p_week
    ORDER BY wl.slot_position;
END;
$$ LANGUAGE plpgsql;

-- All favorites (players + teams) for a user.
CREATE OR REPLACE FUNCTION user_api.fn_get_user_favorites(p_user_id UUID)
RETURNS TABLE (
    favorite_id   UUID,
    kind          TEXT,       -- 'player' or 'team'
    target_id     UUID,
    name          VARCHAR,
    full_name     VARCHAR,
    position_code VARCHAR,    -- for players
    team_code     VARCHAR,    -- player's NFL team abbr
    abbr          VARCHAR,    -- for NFL teams
    added_at      TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    -- Favorited players
    SELECT
        f.id,
        'player'::TEXT,
        p.id,
        p.name,
        p.name,
        p.position_code,
        t.abbr,
        NULL::VARCHAR,
        f.added_at
    FROM user_api.favorites f
    JOIN public.players p ON p.id = f.player_id
    LEFT JOIN public.teams t ON t.id = p.team_id
    WHERE f.user_id = p_user_id AND f.player_id IS NOT NULL

    UNION ALL

    -- Favorited NFL teams
    SELECT
        f.id,
        'team'::TEXT,
        t.id,
        t.abbr,
        t.full_name,
        NULL::VARCHAR,
        NULL::VARCHAR,
        t.abbr,
        f.added_at
    FROM user_api.favorites f
    JOIN public.teams t ON t.id = f.team_id
    WHERE f.user_id = p_user_id AND f.team_id IS NOT NULL

    ORDER BY added_at DESC;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- USER API — AD-HOC SQL CONVERSIONS
-- ---------------------------------------------------------------------------

-- Insert/replace a roster player with conflict handling (includes slot_position, not used by ingest)
CREATE OR REPLACE FUNCTION user_api.usp_add_roster_player(
    p_league_team_id UUID,
    p_player_id      UUID,
    p_slot_position  VARCHAR(10)
) RETURNS UUID AS $$
DECLARE
    v_roster_id UUID;
BEGIN
    INSERT INTO user_api.roster_players (league_team_id, player_id, slot_position)
    VALUES (p_league_team_id, p_player_id, p_slot_position)
    ON CONFLICT (league_team_id, player_id) DO UPDATE
        SET slot_position = p_slot_position,
            added_at = NOW()
    RETURNING id INTO v_roster_id;

    RETURN v_roster_id;
END;
$$ LANGUAGE plpgsql;

-- Drop a roster player by league team and player ID
CREATE OR REPLACE PROCEDURE user_api.usp_drop_roster_player(
    p_league_team_id UUID,
    p_player_id      UUID
) AS $$
BEGIN
    DELETE FROM user_api.roster_players
    WHERE league_team_id = p_league_team_id
      AND player_id = p_player_id;
END;
$$ LANGUAGE plpgsql;

-- Add/replace a lineup slot in a transaction (used for full lineup replacement)
CREATE OR REPLACE FUNCTION user_api.usp_replace_lineup_player(
    p_league_team_id UUID,
    p_player_id      UUID,
    p_season_year    INT,
    p_week           INT,
    p_slot_position  VARCHAR(10)
) RETURNS UUID AS $$
DECLARE
    v_lineup_id UUID;
BEGIN
    -- Delete existing slot for this game
    DELETE FROM user_api.weekly_lineups
    WHERE league_team_id = p_league_team_id
      AND season_year = p_season_year
      AND week = p_week
      AND slot_position = p_slot_position;

    -- Insert new slot (no conflict handling required)
    INSERT INTO user_api.weekly_lineups
        (league_team_id, player_id, season_year, week, slot_position)
    VALUES (p_league_team_id, p_player_id, p_season_year, p_week, p_slot_position)
    RETURNING id INTO v_lineup_id;

    RETURN v_lineup_id;
END;
$$ LANGUAGE plpgsql;

-- Add all lineup slots at once (transaction is caller's responsibility, use with usp_replace_lineup_player for each slot)
CREATE OR REPLACE FUNCTION user_api.usp_add_lineup_players(
    p_league_team_id UUID,
    p_player_ids    UUID[],
    p_season_year    INT[],
    p_week           INT[],
    p_slot_positions VARCHAR[]
) RETURNS VOID AS $$
DECLARE
    i INTEGER;
BEGIN
    FOR i IN 1..CARDINALITY(p_player_ids) LOOP
        CALL user_api.usp_replace_lineup_player(
            p_league_team_id, p_player_ids[i], p_season_year[i], p_week[i], p_slot_positions[i]
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Search players by name/position/team with search operators
CREATE OR REPLACE FUNCTION user_api.fn_search_players(
    p_name       VARCHAR,
    p_position   VARCHAR,
    p_team_id    UUID
)
RETURNS TABLE (
    player_id   UUID,
    espn_id     VARCHAR,
    name        VARCHAR,
    position_code VARCHAR,
    team_abbr   VARCHAR,
    team_name   VARCHAR
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
    WHERE ($1::text IS NULL OR p.name ILIKE '%' || $1 || '%')
      AND ($2::text IS NULL OR p.position_code = $2)
      AND ($3::uuid IS NULL OR p.team_id = $3)
    ORDER BY p.name;
END;
$$ LANGUAGE plpgsql;

-- Get a single player by UUID
CREATE OR REPLACE FUNCTION user_api.fn_get_player(
    p_player_id UUID
)
RETURNS TABLE (
    player_id   UUID,
    espn_id     VARCHAR,
    name        VARCHAR,
    position_code VARCHAR,
    team_abbr   VARCHAR,
    team_name   VARCHAR
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
    WHERE p.id = p_player_id;
END;
$$ LANGUAGE plpgsql;

-- Remove team owner (for DELETE endpoint)
CREATE OR REPLACE PROCEDURE user_api.usp_remove_owner(
    p_league_team_id UUID,
    p_user_id        UUID
) AS $$
BEGIN
    DELETE FROM user_api.league_team_owners
    WHERE league_team_id = p_league_team_id
      AND user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Add favorite (player or team) with conflict handling
CREATE OR REPLACE PROCEDURE user_api.usp_add_favorite(
    p_user_id      UUID,
    p_kind         TEXT, -- 'player' or 'team'
    p_target_id    UUID,
    p_target_name  VARCHAR
) AS $$
BEGIN
    INSERT INTO user_api.favorites
        (user_id, kind, player_id, team_id, target_name, extra)
    VALUES
        (p_user_id, p_kind,
         CASE WHEN p_kind = 'player' THEN p_target_id ELSE NULL END,
         CASE WHEN p_kind = 'team' THEN p_target_id ELSE NULL END,
         p_target_name, NULL);
END;
$$ LANGUAGE plpgsql;

-- Remove favorite (player or team) by kind, user_id, and target_id
CREATE OR REPLACE PROCEDURE user_api.usp_remove_favorite(
    p_user_id      UUID,
    p_kind         TEXT, -- 'player' or 'team'
    p_target_id    UUID
) AS $$
BEGIN
    DELETE FROM user_api.favorites
    WHERE user_id = p_user_id
      AND CASE
            WHEN p_kind = 'player' THEN player_id = p_target_id
            WHEN p_kind = 'team' THEN team_id = p_target_id
            ELSE FALSE
          END;
END;
$$ LANGUAGE plpgsql;


-- Rename a league team (called by rename_team endpoint)
CREATE OR REPLACE FUNCTION user_api.usp_rename_team(
    p_new_name VARCHAR(100),
    p_league_team_id UUID,
    p_league_id UUID
) RETURNS UUID AS $$
DECLARE
    v_team_id UUID;
BEGIN
    -- First verify the team exists and belongs to the league
    SELECT id INTO v_team_id FROM user_api.league_teams
    WHERE id = p_league_team_id
      AND league_id = p_league_id;
    
    IF v_team_id IS NULL THEN
        RAISE EXCEPTION 'Team not found or league mismatch';
    END IF;
    
    -- Update name and return team_id (not uuid, the procedure returns UUID)
    UPDATE user_api.league_teams
    SET name = p_new_name, updated_at = NOW()
    WHERE id = v_team_id
    RETURNING id INTO v_team_id;
    
    RETURN v_team_id;
END;
$$ LANGUAGE plpgsql;

