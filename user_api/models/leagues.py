from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Leagues
# ---------------------------------------------------------------------------

class LeagueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    league_type_id: int = 1
    available_scope_id: int = 1
    season_year: int | None = None  # None = server uses current year
    max_teams: int = Field(12, ge=2, le=64)


class LeagueResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_by: UUID
    created_at: datetime
    team_count: int = 0
    league_type_id: int
    league_type_name: str
    available_scope_id: int
    available_scope_name: str
    season_year: int
    max_teams: int


# ---------------------------------------------------------------------------
# League Settings — per-section read/update models
# ---------------------------------------------------------------------------

class LeagueScoringSettings(BaseModel):
    fractional_scoring: bool = True
    median_game: bool = False


class LeagueRosterConfig(BaseModel):
    qb: int = 1
    rb: int = 2
    wr: int = 2
    te: int = 1
    flex: int = 1
    superflex: int = 0
    k: int = 1
    dst: int = 1
    bench: int = 6
    ir: int = 1
    idp_dl: int = 0
    idp_dt: int = 0
    idp_edge: int = 0
    idp_lb: int = 0
    idp_ilb: int = 0
    idp_db: int = 0
    idp_cb: int = 0
    idp_s: int = 0


class LeagueDraftSettings(BaseModel):
    draft_type_id: int = 1
    draft_date: datetime | None = None
    seconds_per_pick: int = 90
    autopick_enabled: bool = True
    third_round_reversal: bool = False


class LeagueWaiverSettings(BaseModel):
    waiver_type_id: int = 3
    faab_budget: int = 100
    waiver_days: int = 2
    waiver_process_day: str = "wednesday"
    max_acquisitions: int | None = None


class LeagueTradeSettings(BaseModel):
    deadline_week: int | None = None
    review_days: int = 2
    veto_votes_required: int = 4
    allow_future_picks: bool = False


class LeaguePlayoffSettings(BaseModel):
    playoff_teams: int = 6
    start_week: int = 15
    end_week: int = 17
    consolation_bracket: bool = False
    seeding_id: int = 1


class LeagueKeeperSettings(BaseModel):
    keeper_count: int = 0
    cost_type_id: int = 1
    taxi_squad_size: int = 0


class LeagueSettingsResponse(BaseModel):
    league_year: int
    scoring: LeagueScoringSettings
    roster: LeagueRosterConfig
    draft: LeagueDraftSettings
    waivers: LeagueWaiverSettings
    trades: LeagueTradeSettings
    playoffs: LeaguePlayoffSettings
    keeper: LeagueKeeperSettings


class LeagueSettingsUpdate(BaseModel):
    scoring: LeagueScoringSettings | None = None
    roster: LeagueRosterConfig | None = None
    draft: LeagueDraftSettings | None = None
    waivers: LeagueWaiverSettings | None = None
    trades: LeagueTradeSettings | None = None
    playoffs: LeaguePlayoffSettings | None = None
    keeper: LeagueKeeperSettings | None = None


# ---------------------------------------------------------------------------
# League Teams
# ---------------------------------------------------------------------------

class LeagueTeamCreate(BaseModel):
    name: str = Field("My Team", min_length=1, max_length=100)


class LeagueTeamRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class TeamBrandingUpdate(BaseModel):
    abbreviation: str | None = Field(None, max_length=5)
    logo_url: str | None = None
    slogan: str | None = Field(None, max_length=200)
    primary_color: str | None = Field(None, max_length=7)
    secondary_color_1: str | None = Field(None, max_length=7)
    secondary_color_2: str | None = Field(None, max_length=7)


class LeagueTeamResponse(BaseModel):
    id: UUID
    league_id: UUID
    name: str
    abbreviation: str | None = None
    logo_url: str | None = None
    slogan: str | None = None
    primary_color: str | None = None
    secondary_color_1: str | None = None
    secondary_color_2: str | None = None
    created_by_id: UUID
    created_at: datetime
    owner_count: int = 0


# ---------------------------------------------------------------------------
# Matchups
# ---------------------------------------------------------------------------

class MatchupCreate(BaseModel):
    season_year: int
    week: int = Field(..., ge=1, le=22)
    home_team_id: UUID
    away_team_id: UUID
    is_playoff: bool = False


class MatchupUpdate(BaseModel):
    home_score: float | None = None
    away_score: float | None = None
    home_projected: float | None = None
    away_projected: float | None = None
    status: str | None = Field(None, pattern="^(scheduled|in_progress|final)$")


class MatchupResponse(BaseModel):
    id: UUID
    league_id: UUID
    season_year: int
    week: int
    home_team_id: UUID
    away_team_id: UUID
    home_score: float | None = None
    away_score: float | None = None
    home_projected: float | None = None
    away_projected: float | None = None
    is_playoff: bool
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Standings
# ---------------------------------------------------------------------------

class StandingsEntry(BaseModel):
    team_id: UUID
    team_name: str
    abbreviation: str | None = None
    primary_color: str | None = None
    wins: int
    losses: int
    ties: int
    win_pct: float
    wins_vs_median: int
    points_for: float
    points_against: float
    points_diff: float
    games_behind: float
    streak_type: str | None = None
    streak_count: int
    score_high: float
    score_low: float
    score_avg: float
    score_std_dev: float
    all_play_wins: int
    all_play_losses: int
    playoff_seed: int | None = None
    is_eliminated: bool
    playoff_result: str | None = None


# ---------------------------------------------------------------------------
# Team Season Stats
# ---------------------------------------------------------------------------

class TeamSeasonStatsResponse(BaseModel):
    league_team_id: UUID
    season_year: int
    waiver_position: int | None = None
    waiver_budget_start: int | None = None
    waiver_budget_used: int = 0
    waiver_budget_remaining: int | None = None
    total_moves: int = 0
    playoff_seed: int | None = None
    is_eliminated: bool = False
    playoff_result: str | None = None


class TeamSeasonStatsUpdate(BaseModel):
    waiver_position: int | None = None
    waiver_budget_start: int | None = None
    waiver_budget_used: int | None = None
    total_moves: int | None = None
    playoff_seed: int | None = None
    is_eliminated: bool | None = None
    playoff_result: str | None = Field(None, max_length=30)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

class TransactionCreate(BaseModel):
    league_team_id: UUID
    transaction_type: str = Field(..., pattern="^(add|drop|waiver|trade|ir_activate|ir_deactivate)$")
    player_id: UUID | None = None
    related_team_id: UUID | None = None
    waiver_bid: int | None = None
    week: int | None = None
    season_year: int
    status: str = Field("approved", pattern="^(pending|approved|vetoed|failed)$")


class TransactionResponse(BaseModel):
    id: UUID
    league_id: UUID
    league_team_id: UUID
    transaction_type: str
    player_id: UUID | None = None
    related_team_id: UUID | None = None
    waiver_bid: int | None = None
    week: int | None = None
    season_year: int
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Draft Picks
# ---------------------------------------------------------------------------

class DraftPickCreate(BaseModel):
    draft_year: int
    pick_number: int
    round_number: int
    pick_in_round: int
    league_team_id: UUID
    player_id: UUID | None = None
    bid_amount: int | None = None
    nominated_by: UUID | None = None


class DraftPickResponse(BaseModel):
    id: UUID
    league_id: UUID
    draft_year: int
    pick_number: int
    round_number: int
    pick_in_round: int
    league_team_id: UUID
    player_id: UUID | None = None
    bid_amount: int | None = None
    nominated_by: UUID | None = None
    drafted_at: datetime | None = None


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
