import apiClient from './client'

export async function listFavorites() {
  const { data } = await apiClient.get('/api/favorites')
  return data
}

export async function addPlayerFavorite(playerId: string) {
  const { data } = await apiClient.post('/api/favorites/players', { player_id: playerId })
  return data
}

export async function removePlayerFavorite(playerId: string) {
  await apiClient.delete(`/api/favorites/players/${playerId}`)
}

export async function addTeamFavorite(teamId: string) {
  const { data } = await apiClient.post('/api/favorites/teams', { team_id: teamId })
  return data
}

export async function removeTeamFavorite(teamId: string) {
  await apiClient.delete(`/api/favorites/teams/${teamId}`)
}
