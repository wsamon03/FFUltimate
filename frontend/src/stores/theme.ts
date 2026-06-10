import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Theme, AppBranding, AppConfig } from '@/api/config'
import { getBranding, getAppConfig, setUserTheme } from '@/api/config'

const DEFAULT_BRANDING: AppBranding = {
  app_name: 'Fantasy Football',
  tagline: 'Your league. Your rules.',
  logo_url: null,
}

export const useThemeStore = defineStore('theme', () => {
  const appName = ref(DEFAULT_BRANDING.app_name)
  const tagline = ref(DEFAULT_BRANDING.tagline)
  const logoUrl = ref<string | null>(null)
  const themes = ref<Theme[]>([])
  const activeThemeId = ref<number | null>(null)

  const activeTheme = computed(() =>
    themes.value.find((t) => t.id === activeThemeId.value) ?? null,
  )

  function applyTheme(theme: Theme) {
    const root = document.documentElement
    root.style.setProperty('--color-primary', theme.primary_color)
    root.style.setProperty('--color-primary-hover', theme.primary_hover)
    root.style.setProperty('--color-bg', theme.bg_color)
    root.style.setProperty('--color-card', theme.card_color)
    root.style.setProperty('--color-card-hover', theme.card_hover)
    root.style.setProperty('--color-border', theme.border_color)
    root.style.setProperty('--color-border-light', theme.border_color)
    root.style.setProperty('--color-text-primary', theme.text_primary)
    root.style.setProperty('--color-text-secondary', theme.text_secondary)
    root.style.setProperty('--font-family', theme.font_family)
  }

  // Called on App boot before auth — loads public branding only
  async function bootPublic() {
    try {
      const branding = await getBranding()
      appName.value = branding.app_name
      tagline.value = branding.tagline
      logoUrl.value = branding.logo_url
    } catch {
      // Use defaults
    }
  }

  // Called after auth — loads themes + user preference
  async function bootAuthenticated() {
    try {
      const config: AppConfig = await getAppConfig()
      appName.value = config.app_name
      tagline.value = config.tagline
      logoUrl.value = config.logo_url
      themes.value = config.themes
      activeThemeId.value = config.active_theme_id

      if (activeTheme.value) {
        applyTheme(activeTheme.value)
      }
    } catch {
      // Keep defaults
    }
  }

  async function selectTheme(themeId: number) {
    const theme = themes.value.find((t) => t.id === themeId)
    if (!theme) return
    activeThemeId.value = themeId
    applyTheme(theme)
    await setUserTheme(themeId)
  }

  return {
    appName,
    tagline,
    logoUrl,
    themes,
    activeThemeId,
    activeTheme,
    bootPublic,
    bootAuthenticated,
    selectTheme,
  }
})
