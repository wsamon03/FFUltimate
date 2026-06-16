import apiClient from './client'

export interface UserProfile {
  id: string
  provider: string
  email: string
  display_name: string | null
  avatar_url: string | null
}

export async function getMe(): Promise<UserProfile> {
  const { data } = await apiClient.get('/auth/me')
  return data
}

export async function postRefresh(): Promise<{ access_token: string }> {
  const { data } = await apiClient.post('/auth/refresh')
  return data
}

export async function postLogout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

export async function registerLocal(
  email: string,
  password: string,
  displayName?: string,
): Promise<{ access_token: string }> {
  const { data } = await apiClient.post('/auth/register', {
    email,
    password,
    display_name: displayName ?? null,
  })
  return data
}

export async function loginLocal(
  email: string,
  password: string,
): Promise<{ access_token: string }> {
  const { data } = await apiClient.post('/auth/login', { email, password })
  return data
}
