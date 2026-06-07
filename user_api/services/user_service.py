import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import asyncpg

from user_api.config import settings


async def upsert_user(
    conn: asyncpg.Connection,
    provider: str,
    provider_sub: str,
    email: str,
    display_name: str | None,
    avatar_url: str | None,
) -> UUID:
    user_id = await conn.fetchval(
        "SELECT user_api.usp_upsert_user($1, $2, $3, $4, $5)",
        provider,
        provider_sub,
        email,
        display_name,
        avatar_url,
    )
    return UUID(str(user_id))


def generate_refresh_token() -> str:
    return secrets.token_hex(32)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )


async def store_refresh_token(
    conn: asyncpg.Connection,
    user_id: UUID,
    raw_token: str,
    user_agent: str | None,
    ip_address: str | None,
) -> None:
    token_hash = hash_token(raw_token)
    expires_at = refresh_token_expiry()
    await conn.execute(
        "CALL user_api.usp_store_refresh_token($1, $2, $3, $4, $5)",
        user_id,
        token_hash,
        expires_at,
        user_agent,
        ip_address,
    )


async def revoke_refresh_token(conn: asyncpg.Connection, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    await conn.execute(
        "CALL user_api.usp_revoke_refresh_token($1)",
        token_hash,
    )


async def validate_refresh_token(
    conn: asyncpg.Connection, raw_token: str
) -> UUID | None:
    token_hash = hash_token(raw_token)
    row = await conn.fetchrow(
        """
        SELECT user_id, expires_at
        FROM user_api.refresh_tokens
        WHERE token_hash = $1 AND revoked = FALSE
        """,
        token_hash,
    )
    if not row:
        return None
    if row["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(tz=timezone.utc):
        return None
    return UUID(str(row["user_id"]))


async def get_user_by_id(conn: asyncpg.Connection, user_id: UUID) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT id, provider, email, display_name, avatar_url FROM user_api.users WHERE id = $1 AND is_active = TRUE",
        user_id,
    )
