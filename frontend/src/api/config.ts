import apiClient from './client'
import axios from 'axios'

export interface Theme {
  id: number
  name: string
  display_name: string
  primary_color: string
  primary_hover: string
  bg_color: string
  card_color: string
  card_hover: string
  border_color: string
  text_primary: string
  text_secondary: string
  font_family: string
  is_default: boolean
}

export interface AppBranding {
  app_name: string
  tagline: string
  logo_url: string | null
}

export interface AppConfig extends AppBranding {
  themes: Theme[]
  active_theme_id: number | null
}

export async function getBranding(): Promise<AppBranding> {
  // Public endpoint — no auth required
  const { data } = await axios.get('/api/config/branding')
  return data
}

export async function getAppConfig(): Promise<AppConfig> {
  const { data } = await apiClient.get('/api/config/app')
  return data
}

export async function setUserTheme(themeId: number): Promise<void> {
  await apiClient.put('/api/config/theme', { theme_id: themeId })
}
