import apiClient from './client'

export async function getTeams() {
  const { data } = await apiClient.get('/api/stats/teams')
  return data
}

export async function getGames(season?: number, week?: number) {
  const { data } = await apiClient.get('/api/stats/games', { params: { season, week } })
  return data
}

export async function getGame(gameId: string) {
  const { data } = await apiClient.get(`/api/stats/game/${gameId}`)
  return data
}

export async function getPlayerStats(playerId: string) {
  const { data } = await apiClient.get(`/api/stats/player/${playerId}`)
  return data
}

export async function getTeamStats(teamId: string) {
  const { data } = await apiClient.get(`/api/stats/team/${teamId}`)
  return data
}

export async function getLeaderboard(gameId: string, category: 'passing' | 'rushing' | 'receiving') {
  const { data } = await apiClient.get(`/api/stats/leaderboard/${gameId}`, { params: { category } })
  return data
}

export async function getFantasyStats(playerId: string) {
  const { data } = await apiClient.get(`/api/stats/fantasy/${playerId}`)
  return data
}

export async function getPlayerSeasonStats(year: number, name?: string, position?: string) {
  const { data } = await apiClient.get('/api/stats/player-season-stats', {
    params: {
      year,
      name: name || undefined,
      position: position || undefined,
    },
  })
  return data
}

export async function getPlayerPositions() {
  const { data } = await apiClient.get('/api/stats/player-positions')
  return data
}
