<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <AppSpinner v-if="loading" fullPage />

    <template v-else-if="player">
      <!-- Header -->
      <div class="flex items-start justify-between gap-4">
        <div class="flex items-center gap-4">
          <div>
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">
                {{ player.full_name || player.name }}
              </h1>
              <FavoriteStar
                :is-favorited="isFavorited"
                :loading="togglingFav"
                :size="22"
                @toggle="toggleFav"
              />
            </div>
            <div class="flex items-center gap-2 mt-1">
              <PositionBadge :position="player.position || '—'" />
              <span class="text-sm" style="color: var(--color-text-secondary)">
                {{ player.team_code || player.team || 'Free Agent' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Stat tabs -->
      <div class="flex gap-1 border-b" style="border-color: var(--color-border)">
        <button
          v-for="tab in ['Stats', 'Fantasy']"
          :key="tab"
          class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
          :style="activeTab === tab
            ? `border-color: var(--color-primary); color: var(--color-primary)`
            : `border-color: transparent; color: var(--color-text-secondary)`"
          @click="activeTab = tab"
        >
          {{ tab }}
        </button>
      </div>

      <!-- StatToggleBar -->
      <StatToggleBar @change="onFilterChange" />

      <!-- Stats table -->
      <AppSpinner v-if="loadingStats" />

      <AppEmptyState v-else-if="filteredStats.length === 0" title="No stats for this period" />

      <AppTable v-else>
        <template #head>
          <tr>
            <th>Season</th>
            <th v-if="showWeek">Week</th>
            <th>Pass Yds</th>
            <th>Pass TD</th>
            <th>Rush Yds</th>
            <th>Rush TD</th>
            <th>Rec Yds</th>
            <th>Rec</th>
            <th>Rec TD</th>
          </tr>
        </template>
        <PlayerStatRow
          v-for="(row, i) in filteredStats"
          :key="i"
          :row="row"
          :show-week="showWeek"
        />
      </AppTable>
    </template>

    <AppEmptyState v-else title="Player not found" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getPlayer } from '@/api/players'
import { getPlayerStats, getFantasyStats } from '@/api/stats'
import { listFavorites, addPlayerFavorite, removePlayerFavorite } from '@/api/favorites'
import type { StatFilter } from '@/components/players/StatToggleBar.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import FavoriteStar from '@/components/common/FavoriteStar.vue'
import PositionBadge from '@/components/common/PositionBadge.vue'
import StatToggleBar from '@/components/players/StatToggleBar.vue'
import PlayerStatRow from '@/components/players/PlayerStatRow.vue'

const route = useRoute()
const playerId = route.params.id as string

const loading = ref(true)
const loadingStats = ref(false)
const player = ref<any>(null)
const allStats = ref<any[]>([])
const isFavorited = ref(false)
const togglingFav = ref(false)
const activeTab = ref('Stats')
const currentFilter = ref<StatFilter>({ mode: 'career' })

onMounted(async () => {
  try {
    const [p, favData, stats] = await Promise.all([
      getPlayer(playerId),
      listFavorites(),
      getPlayerStats(playerId),
    ])
    player.value = p
    allStats.value = stats
    isFavorited.value = (favData.players || []).some((x: any) => x.id === playerId)
  } finally {
    loading.value = false
  }
})

async function onFilterChange(filter: StatFilter) {
  currentFilter.value = filter
  if (activeTab.value === 'Fantasy') {
    loadingStats.value = true
    try { allStats.value = await getFantasyStats(playerId) }
    finally { loadingStats.value = false }
  }
}

const showWeek = computed(() =>
  currentFilter.value.mode === 'by_week' || currentFilter.value.mode === 'range',
)

const filteredStats = computed(() => {
  const f = currentFilter.value
  let rows = allStats.value

  if (f.mode === 'career') return rows

  if (f.mode === 'full_season' || f.mode === 'by_year') {
    return rows.filter(r => r.season_year === f.startYear || r.season === f.startYear)
  }

  if (f.mode === 'by_week') {
    return rows.filter(r =>
      (r.season_year === f.startYear || r.season === f.startYear) && r.week === f.startWeek,
    )
  }

  if (f.mode === 'range') {
    return rows.filter(r => {
      const sy = r.season_year ?? r.season
      const wk = r.week ?? 0
      const afterStart = sy > (f.startYear ?? 0) || (sy === f.startYear && wk >= (f.startWeek ?? 1))
      const beforeEnd  = sy < (f.endYear ?? 9999) || (sy === f.endYear && wk <= (f.endWeek ?? 22))
      return afterStart && beforeEnd
    })
  }

  return rows
})

async function toggleFav() {
  togglingFav.value = true
  try {
    if (isFavorited.value) {
      await removePlayerFavorite(playerId)
      isFavorited.value = false
    } else {
      await addPlayerFavorite(playerId)
      isFavorited.value = true
    }
  } finally {
    togglingFav.value = false
  }
}
</script>
