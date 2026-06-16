<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">NFL Games</h1>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 items-end">
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Season</label>
        <input
          v-model.number="filters.season"
          type="number" min="2000" :max="currentYear"
          class="w-24 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
          style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Week</label>
        <input
          v-model.number="filters.week"
          type="number" min="0" max="22"
          class="w-20 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
          style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
        />
      </div>
      <AppButton size="sm" @click="loadGames">Apply</AppButton>
    </div>

    <AppSpinner v-if="loading" fullPage />

    <AppEmptyState v-else-if="games.length === 0" title="No games found" message="Try adjusting the filters." />

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <NflGameCard v-for="game in games" :key="game.id" :game="game" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getGames } from '@/api/stats'
import AppButton from '@/components/ui/AppButton.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import NflGameCard from '@/components/nfl/NflGameCard.vue'

const route = useRoute()
const currentYear = new Date().getFullYear()

const filters = ref({
  season: Number(route.query.season) || 2025,
  week:   Number(route.query.week)   || 1,
  team:   route.query.team as string || '',
})

const loading = ref(false)
const games = ref<any[]>([])

async function loadGames() {
  loading.value = true
  try {
    const allGames = await getGames(filters.value.season, filters.value.week)
    
    // If a team is selected, filter client-side by matching the abbreviated code or team ID
    if (filters.value.team) {
      const teamFilter = filters.value.team.toLowerCase()
      games.value = allGames.filter(g => {
        const homeAbbr = (g.home_team_abbr || '')
        const awayAbbr = (g.away_team_abbr || '')
        const homeId = (g.home_team_id || '').toLowerCase()
        const awayId = (g.away_team_id || '').toLowerCase()
        
        // Exact match on abbreviations first
        if (homeAbbr.toLowerCase() === teamFilter || awayAbbr.toLowerCase() === teamFilter) {
          return true
        }
        // Fallback to exact ID match if abbr is missing
        return homeId === teamFilter || awayId === teamFilter
      })
    } else {
      games.value = allGames
    }
  } catch (err) {
    console.error('Failed to load NFL games:', err)
    games.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadGames)
</script>
