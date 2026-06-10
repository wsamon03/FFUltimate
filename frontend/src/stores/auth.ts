import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserProfile } from '@/api/auth'
import { getMe, postRefresh, postLogout } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<UserProfile | null>(null)

  async function boot() {
    try {
      const { access_token } = await postRefresh()
      token.value = access_token
      user.value = await getMe()
    } catch {
      // Not logged in
    }
  }

  function setToken(raw: string) {
    token.value = raw
  }

  async function logout() {
    try {
      if (token.value) await postLogout()
    } catch {
      // Ignore logout errors
    } finally {
      token.value = null
      user.value = null
    }
  }

  return { token, user, boot, setToken, logout }
})
