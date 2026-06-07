from uuid import UUID

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    id: UUID
    provider: str
    email: str
    display_name: str | None
    avatar_url: str | None
