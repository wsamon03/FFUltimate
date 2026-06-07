from dataclasses import dataclass
from uuid import UUID

import asyncpg
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from user_api.config import settings

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=True)


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


@dataclass
class UserContext:
    user_id: UUID
    email: str
    provider: str


async def get_current_user(
    token: str = Depends(_oauth2_scheme),
) -> UserContext:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id_str: str | None = payload.get("sub")
        email: str | None = payload.get("email")
        provider: str | None = payload.get("provider")
        if not user_id_str or not email or not provider:
            raise credentials_error
    except JWTError:
        raise credentials_error

    return UserContext(
        user_id=UUID(user_id_str),
        email=email,
        provider=provider,
    )
