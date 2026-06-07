from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Leagues
# ---------------------------------------------------------------------------

class LeagueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)


class LeagueResponse(BaseModel):
    id: UUID
    name: str
    created_by: UUID
    created_at: datetime
    team_count: int = 0


# ---------------------------------------------------------------------------
# League Teams
# ---------------------------------------------------------------------------

class LeagueTeamCreate(BaseModel):
    name: str = Field("My Team", min_length=1, max_length=100)


class LeagueTeamRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class LeagueTeamResponse(BaseModel):
    id: UUID
    league_id: UUID
    name: str
    created_by_id: UUID
    created_at: datetime
    owner_count: int = 0


# ---------------------------------------------------------------------------
# League Team Owners
# ---------------------------------------------------------------------------

class OwnerAdd(BaseModel):
    user_id: UUID
    is_commissioner: bool = False
    user_display_name: str | None = Field(None, max_length=100)
    is_email_displayed: bool = False


class OwnerUpdate(BaseModel):
    is_commissioner: bool | None = None
    user_display_name: str | None = Field(None, max_length=100)
    is_email_displayed: bool | None = None


class OwnerResponse(BaseModel):
    user_id: UUID
    email: str
    display_name: str | None
    avatar_url: str | None
    is_commissioner: bool
    is_active: bool
    user_display_name: str | None
    is_email_displayed: bool
    joined_at: datetime


# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

class RosterPlayerAdd(BaseModel):
    player_id: UUID
    slot_position: str | None = Field(None, max_length=10)


class RosterPlayerResponse(BaseModel):
    roster_player_id: UUID
    player_id: UUID
    player_name: str
    position_code: str | None
    nfl_team_abbr: str | None
    nfl_team_name: str | None
    slot_position: str | None
    added_at: datetime


# ---------------------------------------------------------------------------
# Weekly Lineup
# ---------------------------------------------------------------------------

class LineupSlot(BaseModel):
    player_id: UUID
    slot_position: str = Field(..., max_length=10)


class LineupPlayerResponse(BaseModel):
    player_id: UUID
    player_name: str
    position_code: str | None
    nfl_team_abbr: str | None
    slot_position: str
    set_at: datetime
