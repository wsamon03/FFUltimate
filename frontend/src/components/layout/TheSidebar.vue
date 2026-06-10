<template>
  <aside
    class="flex flex-col w-64 min-h-screen border-r py-4"
    style="background: var(--color-card); border-color: var(--color-border)"
  >
    <!-- Branding -->
    <div class="px-5 mb-6">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
          style="background: var(--color-primary)">
          FF
        </div>
        <div>
          <div class="font-semibold text-sm leading-tight" style="color: var(--color-text-primary)">
            {{ themeStore.appName }}
          </div>
          <div class="text-xs opacity-60" style="color: var(--color-text-secondary)">
            {{ themeStore.tagline }}
          </div>
        </div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-3 space-y-1">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="isActive(item.to)
          ? 'text-white'
          : 'hover:bg-surface-hover'"
        :style="isActive(item.to)
          ? 'background: var(--color-primary); color: white'
          : 'color: var(--color-text-secondary)'"
        @click="emit('close')"
      >
        <component :is="item.icon" :size="18" />
        {{ item.label }}
      </RouterLink>
    </nav>

    <!-- User footer -->
    <div class="px-4 pt-4 mt-4 border-t" style="border-color: var(--color-border)">
      <RouterLink to="/profile" class="flex items-center gap-3" @click="emit('close')">
        <div class="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center text-xs font-medium text-white"
          style="background: var(--color-primary)">
          <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" class="w-full h-full object-cover" />
          <span v-else>{{ initials }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium truncate" style="color: var(--color-text-primary)">
            {{ authStore.user?.display_name || 'My Account' }}
          </div>
          <div class="text-xs truncate" style="color: var(--color-text-secondary)">
            {{ authStore.user?.email }}
          </div>
        </div>
      </RouterLink>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { LayoutDashboard, Trophy, Flag, Users, Star, User } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const emit = defineEmits<{ close: [] }>()

const authStore = useAuthStore()
const themeStore = useThemeStore()
const route = useRoute()

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/leagues',   label: 'Leagues',   icon: Trophy },
  { to: '/nfl',       label: 'NFL',        icon: Flag },
  { to: '/players',   label: 'Players',   icon: Users },
  { to: '/favorites', label: 'Favorites', icon: Star },
  { to: '/profile',   label: 'Profile',   icon: User },
]

const isActive = (to: string) => route.path === to || route.path.startsWith(to + '/')

const initials = computed(() => {
  const name = authStore.user?.display_name || ''
  return name.split(' ').map(p => p[0]).join('').substring(0, 2).toUpperCase() || 'U'
})
</script>
