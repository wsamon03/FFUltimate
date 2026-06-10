<template>
  <div class="flex flex-col items-center justify-center gap-4">
    <AppSpinner size="lg" />
    <p class="text-sm" style="color: var(--color-text-secondary)">
      {{ error || 'Signing you in…' }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { getMe } from '@/api/auth'
import AppSpinner from '@/components/ui/AppSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const error = ref<string | null>(null)

onMounted(async () => {
  const params = new URLSearchParams(window.location.search)
  const token = params.get('access_token')

  if (!token) {
    error.value = 'No access token received. Redirecting to login…'
    setTimeout(() => router.replace('/login'), 2000)
    return
  }

  // Store token in memory and strip from URL immediately
  authStore.setToken(token)
  window.history.replaceState({}, '', '/auth/callback')

  try {
    const user = await getMe()
    authStore.user = user
    await themeStore.bootAuthenticated()
    router.replace('/dashboard')
  } catch (e) {
    error.value = 'Sign-in failed. Redirecting to login…'
    authStore.logout()
    setTimeout(() => router.replace('/login'), 2000)
  }
})
</script>
