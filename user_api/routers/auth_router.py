import logging
from datetime import timedelta, timezone, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

import asyncpg

from user_api.config import settings
from user_api.dependencies import UserContext, get_current_user, get_pool
from user_api.models.auth import TokenResponse, UserProfile
from user_api.services import jwt_service, oauth_service, user_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str, expires_days: int) -> None:
    is_localhost = "localhost" in settings.FRONTEND_URL or "127.0.0.1" in settings.FRONTEND_URL
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=not is_localhost,
        samesite="lax" if is_localhost else "strict",
        max_age=expires_days * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    is_localhost = "localhost" in settings.FRONTEND_URL or "127.0.0.1" in settings.FRONTEND_URL
    response.delete_cookie(
        key=_REFRESH_COOKIE,
        httponly=True,
        secure=not is_localhost,
        samesite="lax" if is_localhost else "strict"
    )


# ---------------------------------------------------------------------------
# Login — redirect to OAuth provider
# ---------------------------------------------------------------------------

@router.get("/login")
async def login(provider: str):
    if provider not in ("google", "microsoft"):
        raise HTTPException(status_code=400, detail="provider must be 'google' or 'microsoft'")
    try:
        redirect_url, _ = oauth_service.build_authorization_url(provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse(url=redirect_url)


# ---------------------------------------------------------------------------
# Callback — exchange code for tokens, issue JWT + refresh cookie
# ---------------------------------------------------------------------------

@router.get("/callback")
async def callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    pool: asyncpg.Pool = Depends(get_pool),
):
    try:
        user_info = await oauth_service.exchange_code(state=state, code=code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    async with pool.acquire() as conn:
        user_id = await user_service.upsert_user(
            conn,
            provider=user_info["provider"],
            provider_sub=user_info["sub"],
            email=user_info["email"],
            display_name=user_info.get("display_name"),
            avatar_url=user_info.get("avatar_url"),
        )

        raw_refresh = user_service.generate_refresh_token()
        await user_service.store_refresh_token(
            conn,
            user_id=user_id,
            raw_token=raw_refresh,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )

    access_token = jwt_service.issue_access_token(
        user_id=user_id,
        email=user_info["email"],
        provider=user_info["provider"],
    )

    redirect_url = f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token}"
    redirect_response = RedirectResponse(url=redirect_url, status_code=302)
    _set_refresh_cookie(redirect_response, raw_refresh, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return redirect_response


# ---------------------------------------------------------------------------
# Refresh — rotate refresh token, issue new access JWT
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    pool: asyncpg.Pool = Depends(get_pool),
):
    raw_refresh = request.cookies.get(_REFRESH_COOKIE)
    if not raw_refresh:
        raise HTTPException(status_code=401, detail="No refresh token cookie")

    async with pool.acquire() as conn:
        user_id = await user_service.validate_refresh_token(conn, raw_refresh)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Rotate: revoke old, issue new
        await user_service.revoke_refresh_token(conn, raw_refresh)
        new_raw = user_service.generate_refresh_token()
        await user_service.store_refresh_token(
            conn,
            user_id=user_id,
            raw_token=new_raw,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )

        user_row = await user_service.get_user_by_id(conn, user_id)
        if not user_row:
            raise HTTPException(status_code=401, detail="User not found")

    access_token = jwt_service.issue_access_token(
        user_id=user_id,
        email=user_row["email"],
        provider=user_row["provider"],
    )

    _set_refresh_cookie(response, new_raw, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return TokenResponse(access_token=access_token)


# ---------------------------------------------------------------------------
# Logout — revoke refresh token, clear cookie
# ---------------------------------------------------------------------------

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    raw_refresh = request.cookies.get(_REFRESH_COOKIE)
    if raw_refresh:
        async with pool.acquire() as conn:
            await user_service.revoke_refresh_token(conn, raw_refresh)
    _clear_refresh_cookie(response)


# ---------------------------------------------------------------------------
# Me — return current user profile
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserProfile)
async def me(
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        row = await user_service.get_user_by_id(conn, current_user.user_id)
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(
        id=row["id"],
        provider=row["provider"],
        email=row["email"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
    )
