<template>
  <RouterView v-if="booted" />
  <div v-else class="min-h-screen flex items-center justify-center" style="background:var(--color-bg)">
    <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const booted = ref(false)
const authStore = useAuthStore()
const themeStore = useThemeStore()

onMounted(async () => {
  // Boot theme first (applies CSS vars) then auth
  await themeStore.bootPublic()
  await authStore.boot()
  if (authStore.token) {
    await themeStore.bootAuthenticated()
  }
  booted.value = true
})
</script>
