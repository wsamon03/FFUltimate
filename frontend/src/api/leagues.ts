import apiClient from './client'

export interface LeagueCreateBody {
  name: string
  description?: string | null
  league_type_id?: number
  available_scope_id?: number
  season_year?: number | null
  max_teams?: number
}

// Leagues
export async function listLeagues() {
  const { data } = await apiClient.get('/api/leagues')
  return data
}

export const getLeagues = listLeagues

export async function createLeague(body: LeagueCreateBody) {
  const { data } = await apiClient.post('/api/leagues', body)
  return data
}

export async function getLeague(leagueId: string) {
  const { data } = await apiClient.get(`/api/leagues/${leagueId}`)
  return data
}

// Teams
export async function listTeams(leagueId: string) {
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/teams`)
  return data
}

export const getLeagueTeams = listTeams

export async function createTeam(leagueId: string, name: string) {
  const { data } = await apiClient.post(`/api/leagues/${leagueId}/teams`, { name })
  return data
}

export async function getTeam(leagueId: string, teamId: string) {
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/teams/${teamId}`)
  return data
}

export const getTeamDetail = getTeam

export async function renameTeam(leagueId: string, teamId: string, name: string) {
  const { data } = await apiClient.patch(`/api/leagues/${leagueId}/teams/${teamId}`, { name })
  return data
}

// Owners
export async function listOwners(leagueId: string, teamId: string) {
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/teams/${teamId}/owners`)
  return data
}

export async function addOwner(
  leagueId: string,
  teamId: string,
  body: {
    user_id: string
    is_commissioner: boolean
    user_display_name: string
    is_email_displayed: boolean
  },
) {
  const { data } = await apiClient.post(`/api/leagues/${leagueId}/teams/${teamId}/owners`, body)
  return data
}

export async function removeOwner(leagueId: string, teamId: string, userId: string) {
  await apiClient.delete(`/api/leagues/${leagueId}/teams/${teamId}/owners/${userId}`)
}

// Roster
export async function getRoster(leagueId: string, teamId: string) {
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/teams/${teamId}/roster`)
  return data
}

export const getTeamRoster = getRoster

export async function addRosterPlayer(
  leagueId: string,
  teamId: string,
  playerId: string,
  slotPosition: string,
) {
  const { data } = await apiClient.post(`/api/leagues/${leagueId}/teams/${teamId}/roster`, {
    player_id: playerId,
    slot_position: slotPosition,
  })
  return data
}

export async function dropRosterPlayer(leagueId: string, teamId: string, playerId: string) {
  await apiClient.delete(`/api/leagues/${leagueId}/teams/${teamId}/roster/${playerId}`)
}

// Lineup
// League Settings
export async function getLeagueSettings(leagueId: string, year?: number) {
  const params: Record<string, number> = {}
  if (year !== undefined) params.year = year
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/settings`, { params })
  return data
}

export async function updateLeagueSettings(leagueId: string, body: object, year?: number) {
  const params: Record<string, number> = {}
  if (year !== undefined) params.year = year
  const { data } = await apiClient.patch(`/api/leagues/${leagueId}/settings`, body, { params })
  return data
}

export async function getLineup(leagueId: string, teamId: string, season: number, week: number) {
  const { data } = await apiClient.get(
    `/api/leagues/${leagueId}/teams/${teamId}/lineup/${season}/${week}`,
  )
  return data
}

export const getTeamLineup = getLineup

export async function setLineup(
  leagueId: string,
  teamId: string,
  season: number,
  week: number,
  slots: Array<{ player_id: string; slot_position: string }>,
) {
  const { data } = await apiClient.put(
    `/api/leagues/${leagueId}/teams/${teamId}/lineup/${season}/${week}`,
    slots,
  )
  return data
}

export async function setTeamLineup(
  leagueId: string,
  teamId: string,
  week: number,
  slots: Array<{ player_id: string; slot_position: string }>,
) {
  const season = new Date().getFullYear()
  return setLineup(leagueId, teamId, season, week, slots)
}

// Team Branding
export async function updateTeamBranding(
  leagueId: string,
  teamId: string,
  body: {
    abbreviation?: string | null
    logo_url?: string | null
    slogan?: string | null
    primary_color?: string | null
    secondary_color_1?: string | null
    secondary_color_2?: string | null
  },
) {
  const { data } = await apiClient.patch(`/api/leagues/${leagueId}/teams/${teamId}/branding`, body)
  return data
}

// Standings
export async function getStandings(leagueId: string, year?: number) {
  const params: Record<string, number> = {}
  if (year !== undefined) params.year = year
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/standings`, { params })
  return data
}

// Matchups
export async function listMatchups(leagueId: string, year?: number, week?: number) {
  const params: Record<string, number> = {}
  if (year !== undefined) params.year = year
  if (week !== undefined) params.week = week
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/matchups`, { params })
  return data
}

export async function createMatchup(
  leagueId: string,
  body: {
    season_year: number
    week: number
    home_team_id: string
    away_team_id: string
    is_playoff?: boolean
  },
) {
  const { data } = await apiClient.post(`/api/leagues/${leagueId}/matchups`, body)
  return data
}

export async function updateMatchup(
  leagueId: string,
  matchupId: string,
  body: {
    home_score?: number | null
    away_score?: number | null
    home_projected?: number | null
    away_projected?: number | null
    status?: string | null
  },
) {
  const { data } = await apiClient.patch(`/api/leagues/${leagueId}/matchups/${matchupId}`, body)
  return data
}

// Team Season Stats
export async function getTeamSeasonStats(leagueId: string, teamId: string, year?: number) {
  const params: Record<string, number> = {}
  if (year !== undefined) params.year = year
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/teams/${teamId}/season-stats`, { params })
  return data
}

export async function upsertTeamSeasonStats(
  leagueId: string,
  teamId: string,
  body: {
    waiver_position?: number | null
    waiver_budget_start?: number | null
    waiver_budget_used?: number | null
    total_moves?: number | null
    playoff_seed?: number | null
    is_eliminated?: boolean | null
    playoff_result?: string | null
  },
  year?: number,
) {
  const params: Record<string, number> = {}
  if (year !== undefined) params.year = year
  const { data } = await apiClient.put(
    `/api/leagues/${leagueId}/teams/${teamId}/season-stats`,
    body,
    { params },
  )
  return data
}

// Transactions
export async function listTransactions(leagueId: string, year?: number, teamId?: string) {
  const params: Record<string, string | number> = {}
  if (year !== undefined) params.year = year
  if (teamId !== undefined) params.team_id = teamId
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/transactions`, { params })
  return data
}

export async function logTransaction(
  leagueId: string,
  body: {
    league_team_id: string
    transaction_type: string
    player_id?: string | null
    related_team_id?: string | null
    waiver_bid?: number | null
    week?: number | null
    season_year: number
    status?: string
  },
) {
  const { data } = await apiClient.post(`/api/leagues/${leagueId}/transactions`, body)
  return data
}

// Draft Picks
export async function listDraftPicks(leagueId: string, draftYear?: number) {
  const params: Record<string, number> = {}
  if (draftYear !== undefined) params.draft_year = draftYear
  const { data } = await apiClient.get(`/api/leagues/${leagueId}/draft`, { params })
  return data
}

export async function recordDraftPick(
  leagueId: string,
  body: {
    draft_year: number
    pick_number: number
    round_number: number
    pick_in_round: number
    league_team_id: string
    player_id?: string | null
    bid_amount?: number | null
    nominated_by?: string | null
  },
) {
  const { data } = await apiClient.post(`/api/leagues/${leagueId}/draft`, body)
  return data
}
