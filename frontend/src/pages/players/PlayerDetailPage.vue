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

      <!-- Stats / Fantasy tab bar -->
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

        <!-- View mode selector + Stat type selector (Stats tab only) -->
        <template v-if="activeTab === 'Stats'">
          <div class="flex justify-between items-end gap-3">
            <!-- View mode buttons (left) -->
            <div class="flex flex-wrap gap-1">
              <button
                v-for="m in VIEW_MODES"
                :key="m.value"
                class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                :style="viewMode === m.value
                  ? 'background: var(--color-primary); color: white'
                  : 'background: var(--color-card); color: var(--color-text-secondary); border: 1px solid var(--color-border)'"
                @click="viewMode = m.value"
              >{{ m.label }}</button>
            </div>

            <!-- Stat type selector (right) -->
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

          <!-- Timeframe controls row -->
          <template v-if="viewMode === 'season'">
            <div class="flex gap-3 items-end">
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Season</label>
                <select
                  v-model.number="selectedSeason"
                  class="text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
                  style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
                >
                  <option v-for="yr in availableSeasons" :key="yr" :value="yr">{{ yr }}</option>
                </select>
              </div>
            </div>
          </template>
          <template v-else-if="viewMode === 'range'">
            <div class="flex flex-wrap gap-3 items-end">
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Start Year</label>
                <input
                  v-model.number="rangeStartYear"
                  type="number" min="2000" :max="currentYear"
                  class="w-24 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
                  style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
                />
              </div>
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Start Week</label>
                <input
                  v-model.number="rangeStartWeek"
                  type="number" min="1" max="22"
                  class="w-20 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
                  style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
                />
              </div>
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium" style="color: var(--color-text-secondary)">End Year</label>
                <input
                  v-model.number="rangeEndYear"
                  type="number" min="2000" :max="currentYear"
                  class="w-24 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
                  style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
                />
              </div>
              <div class="flex flex-col gap-1">
                <label class="text-xs font-medium" style="color: var(--color-text-secondary)">End Week</label>
                <input
                  v-model.number="rangeEndWeek"
                  type="number" min="1" max="22"
                  class="w-20 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
                  style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
                />
              </div>
            </div>
          </template>
        </template>

        <!-- Stat type selector for Fantasy tab (always visible on Fantasy) -->
        <template v-else>
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
        </template>
      </div>

      <!-- Stats table -->
      <AppSpinner v-if="loadingStats" />

      <AppEmptyState v-else-if="displayStats.length === 0" title="No stats for this period" />

      <AppTable v-else>
        <template #head>
          <tr>
            <!-- Stats tab: mode-specific leading headers -->
            <template v-if="activeTab === 'Stats'">
              <th
                v-if="viewMode === 'career'"
                class="cursor-pointer select-none whitespace-nowrap"
                style="color: var(--color-text-secondary)"
                @click="sortBy('season_year')"
              >Season {{ sortIcon('season_year') }}</th>

              <template v-else-if="viewMode === 'season'">
                <th
                  class="cursor-pointer select-none whitespace-nowrap"
                  style="color: var(--color-text-secondary)"
                  @click="sortBy('week')"
                >Wk {{ sortIcon('week') }}</th>
                <th style="color: var(--color-text-secondary)">Opponent</th>
              </template>

              <template v-else-if="viewMode === 'range'">
                <th
                  class="cursor-pointer select-none whitespace-nowrap"
                  style="color: var(--color-text-secondary)"
                  @click="sortBy('season_year')"
                >Season {{ sortIcon('season_year') }}</th>
                <th
                  class="cursor-pointer select-none whitespace-nowrap"
                  style="color: var(--color-text-secondary)"
                  @click="sortBy('week')"
                >Wk {{ sortIcon('week') }}</th>
                <th style="color: var(--color-text-secondary)">Opponent</th>
              </template>
            </template>

            <!-- Fantasy tab: season + week -->
            <template v-else>
              <th style="color: var(--color-text-secondary)">Season</th>
              <th style="color: var(--color-text-secondary)">Wk</th>
            </template>

            <!-- Offense stat headers -->
            <template v-if="statTypeMode === 'offense'">
              <th class="cursor-pointer select-none" @click="sortBy('pass_comp')">Comp {{ sortIcon('pass_comp') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('pass_att')">Att {{ sortIcon('pass_att') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('pass_yds')">Pass Yds {{ sortIcon('pass_yds') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('pass_td')">Pass TD {{ sortIcon('pass_td') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('pass_int')">INT {{ sortIcon('pass_int') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('rush_att')">Rush Att {{ sortIcon('rush_att') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('rush_yds')">Rush Yds {{ sortIcon('rush_yds') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('rush_td')">Rush TD {{ sortIcon('rush_td') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('rec_receptions')">Rec {{ sortIcon('rec_receptions') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('rec_targets')">Tgts {{ sortIcon('rec_targets') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('rec_yds')">Rec Yds {{ sortIcon('rec_yds') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('rec_td')">Rec TD {{ sortIcon('rec_td') }}</th>
            </template>

            <!-- Defense stat headers -->
            <template v-else-if="statTypeMode === 'defense'">
              <th class="cursor-pointer select-none" @click="sortBy('def_solo')">Solo {{ sortIcon('def_solo') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('def_ast')">Ast {{ sortIcon('def_ast') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('def_sacks')">Sacks {{ sortIcon('def_sacks') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('def_tfl')">TFL {{ sortIcon('def_tfl') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('def_pd')">PD {{ sortIcon('def_pd') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('def_qb_hits')">QB Hits {{ sortIcon('def_qb_hits') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('def_int')">INT {{ sortIcon('def_int') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('def_td')">TD {{ sortIcon('def_td') }}</th>
            </template>

            <!-- Special teams stat headers -->
            <template v-else-if="statTypeMode === 'special'">
              <th class="cursor-pointer select-none" @click="sortBy('k_fg_make')">FGM {{ sortIcon('k_fg_make') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('k_fg_att')">FGA {{ sortIcon('k_fg_att') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('k_xp_make')">XPM {{ sortIcon('k_xp_make') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('k_xp_att')">XPA {{ sortIcon('k_xp_att') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('p_no')">Punts {{ sortIcon('p_no') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('p_yds')">Yds {{ sortIcon('p_yds') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('p_in20')">In 20 {{ sortIcon('p_in20') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('p_tb')">TB {{ sortIcon('p_tb') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('p_blk')">Blk {{ sortIcon('p_blk') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('p_long')">Long {{ sortIcon('p_long') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('ret_kick_no')">Kick Ret {{ sortIcon('ret_kick_no') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('ret_kick_yds')">Kick Yds {{ sortIcon('ret_kick_yds') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('ret_kick_td')">Kick TD {{ sortIcon('ret_kick_td') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('ret_punt_no')">Punt Ret {{ sortIcon('ret_punt_no') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('ret_punt_yds')">Punt Yds {{ sortIcon('ret_punt_yds') }}</th>
              <th class="cursor-pointer select-none" @click="sortBy('ret_punt_td')">Punt TD {{ sortIcon('ret_punt_td') }}</th>
            </template>
          </tr>
        </template>

        <PlayerStatRow
          v-for="(row, i) in displayStats"
          :key="i"
          :row="row"
          :mode="activeTab === 'Stats' ? viewMode : 'fantasy'"
          :stat-type="statTypeMode"
          @season-click="goToSeason"
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
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import FavoriteStar from '@/components/common/FavoriteStar.vue'
import PositionBadge from '@/components/common/PositionBadge.vue'
import PlayerStatRow from '@/components/players/PlayerStatRow.vue'

type ViewMode = 'career' | 'season' | 'range'

const VIEW_MODES: { value: ViewMode; label: string }[] = [
  { value: 'career', label: 'Career' },
  { value: 'season', label: 'Season' },
  { value: 'range',  label: 'Range' },
]

const STAT_KEYS = [
  'pass_comp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'pass_sacked',
  'rush_att', 'rush_yds', 'rush_td',
  'rec_receptions', 'rec_targets', 'rec_yds', 'rec_td',
  'def_solo', 'def_ast', 'def_sacks', 'def_tfl', 'def_pd', 'def_qb_hits', 'def_td', 'def_int',
  'k_fg_make', 'k_fg_att', 'k_xp_make', 'k_xp_att',
  'p_no', 'p_yds', 'p_in20', 'p_tb', 'p_blk', 'p_long',
  'ret_kick_no', 'ret_kick_yds', 'ret_kick_td',
  'ret_punt_no', 'ret_punt_yds', 'ret_punt_td',
]

const currentYear = new Date().getFullYear()

const route = useRoute()
const playerId = route.params.id as string

const loading = ref(true)
const loadingStats = ref(false)
const player = ref<any>(null)
const allStats = ref<any[]>([])
const isFavorited = ref(false)
const togglingFav = ref(false)
const activeTab = ref('Stats')
const statTypeMode = ref('offense')

const statTypes = [
  { value: 'offense',  label: 'Offense' },
  { value: 'defense',  label: 'Defense' },
  { value: 'special',  label: 'Special Teams' },
]

// View mode state (Stats tab)
const viewMode       = ref<ViewMode>('career')
const selectedSeason = ref(currentYear)
const rangeStartYear = ref(currentYear)
const rangeStartWeek = ref(1)
const rangeEndYear   = ref(currentYear)
const rangeEndWeek   = ref(18)

// Sort state
const sortKey = ref<string | null>(null)
const sortDir = ref<'asc' | 'desc'>('desc')

onMounted(async () => {
  try {
    const [p, stats] = await Promise.all([
      getPlayer(playerId),
      getPlayerStats(playerId),
    ])
    player.value = p
    allStats.value = stats
    if (stats.length > 0) {
      const years = [...new Set(stats.map((r: any) => r.season_year as number))].filter(Boolean) as number[]
      if (years.length > 0) {
        selectedSeason.value = Math.max(...years)
        rangeStartYear.value = Math.min(...years)
        rangeEndYear.value   = Math.max(...years)
      }
    }
  } catch (e) {
    console.error('Failed to load player data:', e)
  } finally {
    loading.value = false
  }

  // Load favorites independently so auth failures don't block the page
  try {
    const favData = await listFavorites()
    isFavorited.value = (favData as any[]).filter((f: any) => f.kind === 'player').some((f: any) => f.target_id === playerId)
  } catch {
    // favorites unavailable (e.g. not logged in) — ignore
  }
})

watch(activeTab, async (tab) => {
  loadingStats.value = true
  sortKey.value = null
  try {
    allStats.value = tab === 'Fantasy'
      ? await getFantasyStats(playerId)
      : await getPlayerStats(playerId)
  } finally {
    loadingStats.value = false
  }
})

watch(viewMode, () => { sortKey.value = null })

const availableSeasons = computed(() => {
  const years = new Set(allStats.value.map((r: any) => r.season_year as number).filter(Boolean))
  return Array.from(years).sort((a, b) => b - a)
})

// Career: one aggregated row per season year
const careerStats = computed(() => {
  const byYear = new Map<number, Record<string, any>>()
  for (const row of allStats.value) {
    const yr = row.season_year as number
    if (!yr) continue
    if (!byYear.has(yr)) {
      const entry: Record<string, any> = { season_year: yr }
      STAT_KEYS.forEach(k => { entry[k] = 0 })
      byYear.set(yr, entry)
    }
    const agg = byYear.get(yr)!
    STAT_KEYS.forEach(k => { agg[k] = (agg[k] || 0) + (row[k] || 0) })
  }
  return Array.from(byYear.values()).sort((a, b) => b.season_year - a.season_year)
})

// Season: per-game rows for selected season, ordered by week
const seasonStats = computed(() =>
  allStats.value
    .filter(r => r.season_year === selectedSeason.value)
    .sort((a, b) => (a.week || 0) - (b.week || 0)),
)

// Range: per-game rows within year/week bounds
const rangeStats = computed(() =>
  allStats.value.filter(r => {
    const sy = (r.season_year as number) || 0
    const wk = (r.week as number) || 0
    const afterStart = sy > rangeStartYear.value || (sy === rangeStartYear.value && wk >= rangeStartWeek.value)
    const beforeEnd  = sy < rangeEndYear.value   || (sy === rangeEndYear.value   && wk <= rangeEndWeek.value)
    return afterStart && beforeEnd
  }),
)

const baseStats = computed(() => {
  if (activeTab.value === 'Fantasy') return allStats.value
  if (viewMode.value === 'career')   return careerStats.value
  if (viewMode.value === 'season')   return seasonStats.value
  return rangeStats.value
})

const displayStats = computed(() => {
  if (!sortKey.value) return baseStats.value
  const key = sortKey.value
  return [...baseStats.value].sort((a, b) => {
    const av = a[key] ?? 0
    const bv = b[key] ?? 0
    const diff = Number(av) - Number(bv)
    return sortDir.value === 'asc' ? diff : -diff
  })
})

function sortBy(key: string) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
}

function sortIcon(key: string): string {
  if (sortKey.value !== key) return '↕'
  return sortDir.value === 'asc' ? '↑' : '↓'
}

function goToSeason(year: number) {
  viewMode.value = 'season'
  selectedSeason.value = year
  sortKey.value = null
}

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
