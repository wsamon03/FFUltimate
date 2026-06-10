<template>
  <div class="max-w-2xl mx-auto space-y-8">
    <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">Profile</h1>

    <!-- User info -->
    <AppCard>
      <div class="flex items-center gap-5">
        <div class="w-16 h-16 rounded-full overflow-hidden flex items-center justify-center text-xl font-bold text-white shrink-0"
          style="background: var(--color-primary)">
          <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" class="w-full h-full object-cover" />
          <span v-else>{{ initials }}</span>
        </div>
        <div>
          <div class="text-lg font-semibold" style="color: var(--color-text-primary)">
            {{ authStore.user?.display_name || 'Unknown' }}
          </div>
          <div class="text-sm" style="color: var(--color-text-secondary)">{{ authStore.user?.email }}</div>
          <AppBadge color="blue" class="mt-1">{{ authStore.user?.provider }}</AppBadge>
        </div>
      </div>
    </AppCard>

    <!-- Theme selector -->
    <section>
      <h2 class="text-lg font-semibold mb-4" style="color: var(--color-text-primary)">Appearance</h2>
      <div v-if="themeStore.themes.length === 0" class="text-sm" style="color: var(--color-text-secondary)">
        Loading themes…
      </div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          v-for="theme in themeStore.themes"
          :key="theme.id"
          class="relative flex flex-col items-start p-4 rounded-xl border-2 text-left transition-all"
          :style="themeStore.activeThemeId === theme.id
            ? `border-color: var(--color-primary); background: var(--color-card)`
            : `border-color: var(--color-border); background: var(--color-card)`"
          @click="selectTheme(theme.id)"
        >
          <!-- Color swatch -->
          <div class="flex gap-1.5 mb-3">
            <div class="w-5 h-5 rounded-full" :style="`background: ${theme.primary_color}`" />
            <div class="w-5 h-5 rounded-full" :style="`background: ${theme.bg_color}`" />
            <div class="w-5 h-5 rounded-full border" :style="`background: ${theme.card_color}; border-color: ${theme.border_color}`" />
          </div>
          <div class="font-medium text-sm" style="color: var(--color-text-primary)">{{ theme.display_name }}</div>
          <!-- Active check -->
          <div v-if="themeStore.activeThemeId === theme.id"
            class="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center"
            style="background: var(--color-primary)">
            <Check :size="12" color="white" />
          </div>
        </button>
      </div>
    </section>

    <!-- Logout -->
    <div class="pt-2">
      <AppButton variant="danger" :loading="loggingOut" @click="logout">Sign out</AppButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Check } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { postLogout } from '@/api/auth'
import AppCard from '@/components/ui/AppCard.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppButton from '@/components/ui/AppButton.vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const loggingOut = ref(false)

const initials = computed(() => {
  const name = authStore.user?.display_name || ''
  return name.split(' ').map(p => p[0]).join('').substring(0, 2).toUpperCase() || 'U'
})

async function selectTheme(id: number) {
  await themeStore.selectTheme(id)
}

async function logout() {
  loggingOut.value = true
  try { await postLogout() } catch {}
  authStore.logout()
  router.replace('/login')
}
</script>
