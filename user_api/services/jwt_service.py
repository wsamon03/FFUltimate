from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import jwt

from user_api.config import settings


def issue_access_token(user_id: UUID, email: str, provider: str) -> str:
    now = datetime.now(tz=timezone.utc)
    claims = {
        "sub": str(user_id),
        "email": email,
        "provider": provider,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
