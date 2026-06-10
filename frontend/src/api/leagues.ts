import apiClient from './client'

// Leagues
export async function listLeagues() {
  const { data } = await apiClient.get('/api/leagues')
  return data
}

export const getLeagues = listLeagues

export async function createLeague(name: string, description?: string) {
  const { data } = await apiClient.post('/api/leagues', { name, description })
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
