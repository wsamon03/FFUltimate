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

-- All leagues a user participates in (as an owner of any team).
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
    JOIN user_api.league_teams lt ON lt.league_id = l.id
    JOIN user_api.league_team_owners lto ON lto.league_team_id = lt.id
    WHERE lto.user_id = p_user_id
      AND lto.is_active = TRUE
    GROUP BY l.id, l.name, l.created_by, l.created_at;
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
    target_name   VARCHAR,
    extra         VARCHAR,    -- position_code for players, abbr for teams
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
        p.position_code,
        f.added_at
    FROM user_api.favorites f
    JOIN public.players p ON p.id = f.player_id
    WHERE f.user_id = p_user_id AND f.player_id IS NOT NULL

    UNION ALL

    -- Favorited NFL teams
    SELECT
        f.id,
        'team'::TEXT,
        t.id,
        t.full_name,
        t.abbr,
        f.added_at
    FROM user_api.favorites f
    JOIN public.teams t ON t.id = f.team_id
    WHERE f.user_id = p_user_id AND f.team_id IS NOT NULL

    ORDER BY added_at DESC;
END;
$$ LANGUAGE plpgsql;
