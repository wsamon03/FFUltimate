import apiClient from './client'

export async function searchPlayers(name?: string, position?: string) {
  const { data } = await apiClient.get('/api/players', { params: { name, position } })
  return data
}

export async function getPlayer(playerId: string) {
  const { data } = await apiClient.get(`/api/players/${playerId}`)
  return data
}
