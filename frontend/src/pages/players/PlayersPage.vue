<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">Players</h1>

    <!-- Search + filters -->
    <div class="flex flex-wrap gap-3 items-end">
      <div class="flex-1 min-w-56">
        <SearchInput v-model="query" placeholder="Search players…" />
      </div>
      <select
        v-model="position"
        class="text-sm rounded-lg px-3 py-2 border focus:outline-none"
        style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary)"
      >
        <option value="">All Positions</option>
        <option v-for="pos in positions" :key="pos" :value="pos">{{ pos }}</option>
      </select>
      <input
        v-model.number="year"
        type="number"
        min="2020"
        :max="2026"
        class="text-sm rounded-lg px-3 py-2 border focus:outline-none w-24"
        style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary)"
      />
      <div class="flex rounded-lg overflow-hidden border" style="border-color: var(--color-border)">
        <button
          v-for="type in statTypes"
          :key="type.value"
          class="px-4 py-2 text-sm font-medium transition-colors"
          :style="statType === type.value
            ? 'background: var(--color-primary); color: #fff'
            : 'background: var(--color-card); color: var(--color-text-secondary)'"
          @click="statType = type.value"
        >
          {{ type.label }}
        </button>
      </div>
    </div>

    <AppSpinner v-if="loading" fullPage />

    <AppEmptyState
      v-else-if="sortedPlayers.length === 0"
      title="No players found"
      message="No stats available for the selected filters."
    />

    <AppTable v-else>
      <template #head>
        <tr>
          <th class="fav-cell"></th>
          <th class="helmet-cell"></th>
          <th class="sortable-header" @click="setSortColumn('name')">
            Player <span v-if="sortColumn === 'name'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <th class="sortable-header" @click="setSortColumn('position_code')">
            Pos <span v-if="sortColumn === 'position_code'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <th class="sortable-header" @click="setSortColumn('team_abbr')">
            Team <span v-if="sortColumn === 'team_abbr'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <template v-if="statType === 'offense'">
            <th class="sortable-header" title="Completions" @click="setSortColumn('pass_comp')">
              CMP <span v-if="sortColumn === 'pass_comp'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Pass Attempts" @click="setSortColumn('pass_att')">
              ATT <span v-if="sortColumn === 'pass_att'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Pass Yards" @click="setSortColumn('pass_yds')">
              YDS <span v-if="sortColumn === 'pass_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Pass TDs" @click="setSortColumn('pass_td')">
              TD <span v-if="sortColumn === 'pass_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Interceptions thrown" @click="setSortColumn('pass_int')">
              INT <span v-if="sortColumn === 'pass_int'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Rush Attempts" @click="setSortColumn('rush_att')">
              ATT <span v-if="sortColumn === 'rush_att'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Rush Yards" @click="setSortColumn('rush_yds')">
              YDS <span v-if="sortColumn === 'rush_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Rush TDs" @click="setSortColumn('rush_td')">
              TD <span v-if="sortColumn === 'rush_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Receptions" @click="setSortColumn('rec_receptions')">
              REC <span v-if="sortColumn === 'rec_receptions'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Targets" @click="setSortColumn('rec_targets')">
              TGT <span v-if="sortColumn === 'rec_targets'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Receiving Yards" @click="setSortColumn('rec_yds')">
              YDS <span v-if="sortColumn === 'rec_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Receiving TDs" @click="setSortColumn('rec_td')">
              TD <span v-if="sortColumn === 'rec_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </template>
          <template v-else-if="statType === 'defense'">
            <th class="sortable-header" title="Solo Tackles" @click="setSortColumn('def_solo')">
              SOLO <span v-if="sortColumn === 'def_solo'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Assisted Tackles" @click="setSortColumn('def_ast')">
              AST <span v-if="sortColumn === 'def_ast'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Sacks" @click="setSortColumn('def_sacks')">
              SACKS <span v-if="sortColumn === 'def_sacks'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Tackles for Loss" @click="setSortColumn('def_tfl')">
              TFL <span v-if="sortColumn === 'def_tfl'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Passes Defensed" @click="setSortColumn('def_pd')">
              PD <span v-if="sortColumn === 'def_pd'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="QB Hits" @click="setSortColumn('def_qb_hits')">
              QB HIT <span v-if="sortColumn === 'def_qb_hits'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Defensive TDs" @click="setSortColumn('def_td')">
              DEF TD <span v-if="sortColumn === 'def_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Interceptions" @click="setSortColumn('def_int')">
              INT <span v-if="sortColumn === 'def_int'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </template>
          <template v-else>
            <th class="sortable-header" title="Field Goals Made" @click="setSortColumn('k_fg_make')">
              FGM <span v-if="sortColumn === 'k_fg_make'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Field Goal Attempts" @click="setSortColumn('k_fg_att')">
              FGA <span v-if="sortColumn === 'k_fg_att'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Extra Points Made" @click="setSortColumn('k_xp_make')">
              XPM <span v-if="sortColumn === 'k_xp_make'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Extra Point Attempts" @click="setSortColumn('k_xp_att')">
              XPA <span v-if="sortColumn === 'k_xp_att'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Punts" @click="setSortColumn('p_no')">
              PUNTS <span v-if="sortColumn === 'p_no'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Punt Yards" @click="setSortColumn('p_yds')">
              P YDS <span v-if="sortColumn === 'p_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Inside 20" @click="setSortColumn('p_in20')">
              IN20 <span v-if="sortColumn === 'p_in20'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Touchbacks" @click="setSortColumn('p_tb')">
              TB <span v-if="sortColumn === 'p_tb'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Blocked Punts" @click="setSortColumn('p_blk')">
              BLK <span v-if="sortColumn === 'p_blk'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Longest Punt" @click="setSortColumn('p_long')">
              LONG <span v-if="sortColumn === 'p_long'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Kick Returns" @click="setSortColumn('ret_kick_no')">
              KR <span v-if="sortColumn === 'ret_kick_no'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Kick Return Yards" @click="setSortColumn('ret_kick_yds')">
              KR YDS <span v-if="sortColumn === 'ret_kick_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Kick Return TDs" @click="setSortColumn('ret_kick_td')">
              KR TD <span v-if="sortColumn === 'ret_kick_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Punt Returns" @click="setSortColumn('ret_punt_no')">
              PR <span v-if="sortColumn === 'ret_punt_no'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Punt Return Yards" @click="setSortColumn('ret_punt_yds')">
              PR YDS <span v-if="sortColumn === 'ret_punt_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header" title="Punt Return TDs" @click="setSortColumn('ret_punt_td')">
              PR TD <span v-if="sortColumn === 'ret_punt_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </template>
        </tr>
      </template>
      <tr v-for="p in sortedPlayers" :key="p.player_id">
        <td class="fav-cell">
          <FavoriteStar
            :is-favorited="favorites.has(p.player_id)"
            :loading="togglingFav === p.player_id"
            @toggle="toggleFav(p)"
          />
        </td>
        <td class="helmet-cell">
          <TeamHelmet v-if="p.team_abbr" :abbr="p.team_abbr" :size="24" />
          <span v-else style="color: var(--color-text-secondary)">—</span>
        </td>
        <td>
          <RouterLink
            :to="`/players/${p.player_id}`"
            class="font-medium hover:underline"
            style="color: var(--color-primary)"
          >
            {{ p.name }}
          </RouterLink>
        </td>
        <td>
          <PositionBadge v-if="p.position_code" :position="p.position_code" />
          <span v-else style="color: var(--color-text-secondary)">—</span>
        </td>
        <td style="color: var(--color-text-secondary); font-size: 0.875rem">{{ p.team_abbr || '—' }}</td>
        <template v-if="statType === 'offense'">
          <td>{{ p.pass_comp }}</td>
          <td>{{ p.pass_att }}</td>
          <td>{{ p.pass_yds }}</td>
          <td>{{ p.pass_td }}</td>
          <td>{{ p.pass_int }}</td>
          <td>{{ p.rush_att }}</td>
          <td>{{ p.rush_yds }}</td>
          <td>{{ p.rush_td }}</td>
          <td>{{ p.rec_receptions }}</td>
          <td>{{ p.rec_targets }}</td>
          <td>{{ p.rec_yds }}</td>
          <td>{{ p.rec_td }}</td>
        </template>
        <template v-else-if="statType === 'defense'">
          <td>{{ p.def_solo }}</td>
          <td>{{ p.def_ast }}</td>
          <td>{{ p.def_sacks }}</td>
          <td>{{ p.def_tfl }}</td>
          <td>{{ p.def_pd }}</td>
          <td>{{ p.def_qb_hits }}</td>
          <td>{{ p.def_td }}</td>
          <td>{{ p.def_int }}</td>
        </template>
        <template v-else>
          <td>{{ p.k_fg_make }}</td>
          <td>{{ p.k_fg_att }}</td>
          <td>{{ p.k_xp_make }}</td>
          <td>{{ p.k_xp_att }}</td>
          <td>{{ p.p_no }}</td>
          <td>{{ p.p_yds }}</td>
          <td>{{ p.p_in20 }}</td>
          <td>{{ p.p_tb }}</td>
          <td>{{ p.p_blk }}</td>
          <td>{{ p.p_long }}</td>
          <td>{{ p.ret_kick_no }}</td>
          <td>{{ p.ret_kick_yds }}</td>
          <td>{{ p.ret_kick_td }}</td>
          <td>{{ p.ret_punt_no }}</td>
          <td>{{ p.ret_punt_yds }}</td>
          <td>{{ p.ret_punt_td }}</td>
        </template>
      </tr>
    </AppTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { getPlayerSeasonStats, getPlayerPositions } from '@/api/stats'
import { listFavorites, addPlayerFavorite, removePlayerFavorite } from '@/api/favorites'
import SearchInput from '@/components/common/SearchInput.vue'
import PositionBadge from '@/components/common/PositionBadge.vue'
import FavoriteStar from '@/components/common/FavoriteStar.vue'
import TeamHelmet from '@/components/common/TeamHelmet.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'

const statTypes = [
  { value: 'offense', label: 'Offense' },
  { value: 'defense', label: 'Defense' },
  { value: 'special', label: 'Special Teams' },
]

const query = ref('')
const position = ref('')
const year = ref(2025)
const statType = ref('offense')
const loading = ref(false)
const players = ref<any[]>([])
const positions = ref<string[]>([])
const favorites = ref<Set<string>>(new Set())
const togglingFav = ref<string | null>(null)
const sortColumn = ref<string | null>(null)
const sortDir = ref<'asc' | 'desc'>('desc')

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const sortedPlayers = computed(() => {
  const list = [...players.value]

  if (sortColumn.value) {
    const col = sortColumn.value
    list.sort((a, b) => {
      const aVal = a[col]
      const bVal = b[col]
      if (aVal == null && bVal == null) return 0
      if (aVal == null) return 1
      if (bVal == null) return -1
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir.value === 'asc' ? aVal - bVal : bVal - aVal
      }
      const aStr = String(aVal).toLowerCase()
      const bStr = String(bVal).toLowerCase()
      return sortDir.value === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr)
    })
    return list
  }

  // Default sorts when no column selected
  if (statType.value === 'defense') {
    return list.sort((a, b) => {
      const aScore = (a.def_solo ?? 0) + (a.def_ast ?? 0) + (a.def_sacks ?? 0) * 2
      const bScore = (b.def_solo ?? 0) + (b.def_ast ?? 0) + (b.def_sacks ?? 0) * 2
      return bScore - aScore
    })
  }
  if (statType.value === 'special') {
    return list.sort((a, b) => {
      const aScore = (a.p_yds ?? 0) + (a.k_fg_make ?? 0) * 50 + (a.ret_kick_yds ?? 0) + (a.ret_punt_yds ?? 0)
      const bScore = (b.p_yds ?? 0) + (b.k_fg_make ?? 0) * 50 + (b.ret_kick_yds ?? 0) + (b.ret_punt_yds ?? 0)
      return bScore - aScore
    })
  }
  return list // Offense: API already returns sorted by total yards desc
})

function setSortColumn(col: string) {
  if (sortColumn.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = col
    // Default to asc for text columns, desc for numeric
    const sample = players.value[0]?.[col]
    sortDir.value = typeof sample === 'string' ? 'asc' : 'desc'
  }
}

async function loadStats() {
  loading.value = true
  try {
    players.value = await getPlayerSeasonStats(
      year.value,
      query.value || undefined,
      position.value || undefined,
    )
  } finally {
    loading.value = false
  }
}

async function loadFavorites() {
  const data = await listFavorites()
  favorites.value = new Set(
    data
      .filter((f: any) => f.kind === 'player')
      .map((f: any) => f.target_id)
  )
}

watch(query, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadStats, 300)
})

watch([position, year], loadStats)

watch(statType, () => {
  sortColumn.value = null
  sortDir.value = 'desc'
})

async function toggleFav(player: any) {
  togglingFav.value = player.player_id
  try {
    if (favorites.value.has(player.player_id)) {
      await removePlayerFavorite(player.player_id)
      favorites.value.delete(player.player_id)
    } else {
      await addPlayerFavorite(player.player_id)
      favorites.value.add(player.player_id)
    }
    favorites.value = new Set(favorites.value)
  } finally {
    togglingFav.value = null
  }
}

onMounted(async () => {
  await Promise.all([
    loadStats(),
    loadFavorites(),
    getPlayerPositions().then((p) => { positions.value = p }),
  ])
})
</script>

<style scoped>
.fav-cell {
  white-space: nowrap;
  flex-shrink: 0;
  text-align: center;
  padding: 8px 6px;
  width: 36px;
}
.helmet-cell {
  white-space: nowrap;
  flex-shrink: 0;
  text-align: center;
  padding: 8px 6px;
  width: 36px;
}
.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}
.sortable-header:hover {
  color: var(--color-primary) !important;
}
.sort-arrow {
  margin-left: 2px;
  opacity: 0.8;
}
</style>
