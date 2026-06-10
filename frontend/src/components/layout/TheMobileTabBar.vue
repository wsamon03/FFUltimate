<template>
  <nav
    class="fixed bottom-0 inset-x-0 z-30 flex border-t"
    style="background: var(--color-card); border-color: var(--color-border)"
  >
    <RouterLink
      v-for="item in tabs"
      :key="item.to"
      :to="item.to"
      class="flex-1 flex flex-col items-center justify-center py-2 gap-0.5 text-xs transition-colors"
      :style="isActive(item.to)
        ? 'color: var(--color-primary)'
        : 'color: var(--color-text-secondary)'"
    >
      <component :is="item.icon" :size="20" />
      {{ item.label }}
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { LayoutDashboard, Trophy, Flag, Star } from '@lucide/vue'

const route = useRoute()

const tabs = [
  { to: '/dashboard', label: 'Home',      icon: LayoutDashboard },
  { to: '/leagues',   label: 'Leagues',   icon: Trophy },
  { to: '/nfl',       label: 'NFL',       icon: Flag },
  { to: '/favorites', label: 'Favorites', icon: Star },
]

const isActive = (to: string) => route.path === to || route.path.startsWith(to + '/')
</script>
