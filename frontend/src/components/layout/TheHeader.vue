<template>
  <header
    class="h-14 flex items-center px-4 border-b shrink-0 lg:px-6"
    style="background: var(--color-card); border-color: var(--color-border)"
  >
    <!-- Mobile hamburger -->
    <button
      class="lg:hidden p-1.5 rounded-lg mr-3 transition-colors hover:bg-surface-hover"
      style="color: var(--color-text-secondary)"
      @click="ui.toggleSidebar()"
    >
      <Menu :size="20" />
    </button>

    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 flex-1 min-w-0">
      <RouterLink
        v-for="(crumb, i) in breadcrumbs"
        :key="crumb.path"
        :to="crumb.path"
        class="text-sm truncate transition-colors"
        :class="i === breadcrumbs.length - 1 ? 'font-semibold' : 'hover:underline'"
        :style="i === breadcrumbs.length - 1
          ? 'color: var(--color-text-primary)'
          : 'color: var(--color-text-secondary)'"
      >
        {{ crumb.label }}
      </RouterLink>
      <ChevronRight
        v-if="breadcrumbs.length > 1"
        v-for="(_, i) in breadcrumbs.slice(0, -1)"
        :key="'sep-' + i"
        :size="14"
        style="color: var(--color-text-secondary)"
      />
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Menu, ChevronRight } from '@lucide/vue'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const route = useRoute()

const labelMap: Record<string, string> = {
  dashboard: 'Dashboard',
  leagues: 'Leagues',
  nfl: 'NFL',
  games: 'Games',
  players: 'Players',
  favorites: 'Favorites',
  profile: 'Profile',
  teams: 'Teams',
}

const breadcrumbs = computed(() => {
  const segments = route.path.split('/').filter(Boolean)
  return segments.map((seg, i) => ({
    path: '/' + segments.slice(0, i + 1).join('/'),
    label: labelMap[seg] || seg,
  }))
})
</script>
