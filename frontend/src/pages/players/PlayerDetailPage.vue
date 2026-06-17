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

      <!-- Stat tabs and type selector -->
      <div class="space-y-4">
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

        <!-- Stat type selector (for defense/special teams) -->
        <div class="flex rounded-lg overflow-hidden border" style="border-color: var(--color-border)">
          <button
            v-for="type in statTypes"
            :key="type.value"
            class="px-4 py-2 text-sm font-medium transition-colors"
            :style="statTypeMode === type.value
              ? 'background: var(--color-primary); color: #fff'
              : 'background: var(--color-card); color: var(--color-text-secondary)'"
            @click="statTypeMode = type.value"
          >
            {{ type.label }}
          </button>
        </div>
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
            <!-- Offense stats -->
            <template v-if="statTypeMode === 'offense'">
              <th>Comp</th><th>Att</th><th>Pass Yds</th><th>Pass TD</th><th>INT</th>
              <th>Rush Att</th><th>Rush Yds</th><th>Rush TD</th>
              <th>Rec</th><th>Tgts</th><th>Rec Yds</th><th>Rec TD</th>
            </template>
            <!-- Defense stats -->
            <template v-else-if="statTypeMode === 'defense'">
              <th>Solo</th><th>Ast</th><th>Sacks</th><th>TFL</th><th>PD</th><th>QB Hits</th><th>INT</th><th>TD</th>
            </template>
            <!-- Special teams stats -->
            <template v-else-if="statTypeMode === 'special'">
              <th>FGM</th><th>FGA</th><th>XPM</th><th>XPA</th>
              <th>Punts</th><th>Yds</th><th>In 20</th><th>TB</th><th>Blk</th><th>Long</th>
              <th>Kick Ret</th><th>Kick Yds</th><th>Kick TD</th>
              <th>Punt Ret</th><th>Punt Yds</th><th>Punt TD</th>
            </template>
          </tr>
        </template>
        <PlayerStatRow
          v-for="(row, i) in filteredStats"
          :key="i"
          :row="row"
          :show-week="showWeek"
          :stat-type="statTypeMode"
        />
      </AppTable>
    </template>

    <AppEmptyState v-else title="Player not found" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
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
const statTypeMode = ref('offense')

const statTypes = [
  { value: 'offense', label: 'Offense' },
  { value: 'defense', label: 'Defense' },
  { value: 'special', label: 'Special Teams' },
]

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

watch(activeTab, async (tab) => {
  loadingStats.value = true
  try {
    allStats.value = tab === 'Fantasy'
      ? await getFantasyStats(playerId)
      : await getPlayerStats(playerId)
  } finally {
    loadingStats.value = false
  }
})

const showWeek = computed(() =>
  currentFilter.value.mode === 'by_week' || currentFilter.value.mode === 'range',
)

const positionGroup = computed(() => {
  const pos = player.value?.position ?? ''
  if (pos === 'QB') return 'QB'
  if (pos === 'RB') return 'RB'
  if (pos === 'WR' || pos === 'TE') return 'WR'
  if (['DL', 'LB', 'CB', 'S'].includes(pos)) return 'DEF'
  if (pos === 'K') return 'K'
  if (pos === 'P') return 'P'
  return 'OFF'
})

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
