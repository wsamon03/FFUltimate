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
    name: str           # player name or team abbr
    full_name: str      # player name or team full_name
    position_code: str | None  # for players only
    team_code: str | None      # player's NFL team abbr
    abbr: str | None    # for teams only
    added_at: datetime
