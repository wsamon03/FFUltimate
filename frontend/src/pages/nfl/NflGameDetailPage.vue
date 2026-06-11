<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <AppSpinner v-if="loading" fullPage />

    <template v-else-if="game">
      <!-- Breadcrumb context -->
      <p class="text-xs uppercase tracking-wide font-semibold" style="color: var(--color-text-secondary)">
        NFL Game
      </p>

      <!-- Score hero -->
      <AppCard>
        <div class="flex items-center justify-between text-xs mb-4" style="color: var(--color-text-secondary)">
          <span>{{ formatDate(game.game_date) }} · Week {{ game.week }}, {{ game.season_year }}</span>
          <AppBadge :color="statusColor">{{ game.status_code || 'TBD' }}</AppBadge>
        </div>

        <div class="flex items-center justify-around py-4">
          <div class="text-center">
            <div class="text-2xl font-bold" style="color: var(--color-text-primary)">{{ game.away_team_abbr }}</div>
            <div class="text-5xl font-bold mt-2" style="color: var(--color-text-primary)">
              {{ game.away_score ?? '—' }}
            </div>
            <div class="text-xs mt-1" style="color: var(--color-text-secondary)">Away</div>
          </div>

          <div class="text-2xl font-bold" style="color: var(--color-text-secondary)">@</div>

          <div class="text-center">
            <div class="text-2xl font-bold" style="color: var(--color-text-primary)">{{ game.home_team_abbr }}</div>
            <div class="text-5xl font-bold mt-2" style="color: var(--color-text-primary)">
              {{ game.home_score ?? '—' }}
            </div>
            <div class="text-xs mt-1" style="color: var(--color-text-secondary)">Home</div>
          </div>
        </div>
      </AppCard>

      <!-- Leaderboard -->
      <LeaderboardTable :game-id="gameId" />
    </template>

    <AppEmptyState v-else title="Game not found" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getGame } from '@/api/stats'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import LeaderboardTable from '@/components/nfl/LeaderboardTable.vue'

const route = useRoute()
const gameId = route.params.id as string

const loading = ref(true)
const game = ref<any>(null)

const statusColor = computed(() => {
  const s = (game.value?.status_code || '').toLowerCase()
  if (s === 'final' || s === 'ft') return 'gray'
  if (s === 'live' || s === 'in progress') return 'green'
  return 'blue'
})

function formatDate(d?: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString(undefined, { weekday: 'short', month: 'long', day: 'numeric', year: 'numeric' })
}

onMounted(async () => {
  try { game.value = await getGame(gameId).catch(e => { console.error('Failed to load game:', e); return null }) } catch(e) { 
    console.error('API failed to load game:', e.response?.data || e.message)
  } finally { loading.value = false }
})
</script>
