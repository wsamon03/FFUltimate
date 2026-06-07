from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FavoritePlayerAdd(BaseModel):
    player_id: UUID


class FavoriteTeamAdd(BaseModel):
    team_id: UUID


class FavoriteResponse(BaseModel):
    favorite_id: UUID
    kind: str           # 'player' or 'team'
    target_id: UUID
    target_name: str
    extra: str | None   # position_code for players, abbr for teams
    added_at: datetime
