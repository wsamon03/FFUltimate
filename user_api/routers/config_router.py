"""App config — branding, themes, and user theme preference."""

import logging
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from user_api.dependencies import UserContext, get_current_user, get_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/config", tags=["config"])

_APP_NAME = "Fantasy Football"
_TAGLINE = "Your league. Your rules."


class BrandingResponse(BaseModel):
    app_name: str
    tagline: str
    logo_url: Optional[str]


class ThemeResponse(BaseModel):
    id: int
    name: str
    display_name: str
    primary_color: str
    primary_hover: str
    bg_color: str
    card_color: str
    card_hover: str
    border_color: str
    text_primary: str
    text_secondary: str
    font_family: str
    is_default: bool


class AppConfigResponse(BrandingResponse):
    themes: list[ThemeResponse]
    active_theme_id: Optional[int]


class SetThemeBody(BaseModel):
    theme_id: int


@router.get("/branding", response_model=BrandingResponse)
async def get_branding():
    return BrandingResponse(app_name=_APP_NAME, tagline=_TAGLINE, logo_url=None)


@router.get("/app", response_model=AppConfigResponse)
async def get_app_config(
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        theme_rows = await conn.fetch(
            "SELECT * FROM user_api.themes ORDER BY id"
        )
        user_row = await conn.fetchrow(
            "SELECT active_theme_id FROM user_api.users WHERE id = $1",
            current_user.user_id,
        )

    active_theme_id: Optional[int] = user_row["active_theme_id"] if user_row else None
    if active_theme_id is None:
        for r in theme_rows:
            if r["is_default"]:
                active_theme_id = r["id"]
                break

    return AppConfigResponse(
        app_name=_APP_NAME,
        tagline=_TAGLINE,
        logo_url=None,
        themes=[ThemeResponse(**dict(r)) for r in theme_rows],
        active_theme_id=active_theme_id,
    )


@router.put("/theme")
async def set_user_theme(
    body: SetThemeBody,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT id FROM user_api.themes WHERE id = $1", body.theme_id
        )
        if not exists:
            raise HTTPException(status_code=404, detail="Theme not found")
        await conn.execute(
            "UPDATE user_api.users SET active_theme_id = $1 WHERE id = $2",
            body.theme_id,
            current_user.user_id,
        )
    return {"status": "ok"}
