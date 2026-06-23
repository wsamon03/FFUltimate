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
        <!-- Group header spanning row -->
        <tr v-if="statType === 'offense'">
          <th colspan="5" class="col-group-anchor"></th>
          <th colspan="7" class="col-group-label col-group-pass">PASSING</th>
          <th colspan="4" class="col-group-label col-group-rush">RUSHING</th>
          <th colspan="5" class="col-group-label col-group-rec">RECEIVING</th>
          <th colspan="2" class="col-group-label col-group-fum">FUMBLES</th>
        </tr>
        <tr v-else-if="statType === 'defense'">
          <th colspan="5" class="col-group-anchor"></th>
          <th colspan="4" class="col-group-label col-group-tkl">TACKLES</th>
          <th colspan="2" class="col-group-label col-group-cov">PASS RUSH</th>
          <th colspan="3" class="col-group-label col-group-to">COVERAGE</th>
        </tr>
        <tr v-else>
          <th colspan="5" class="col-group-anchor"></th>
          <th colspan="5" class="col-group-label col-group-kick">KICKING</th>
          <th colspan="6" class="col-group-label col-group-punt">PUNTING</th>
          <th colspan="8" class="col-group-label col-group-ret">RETURNS</th>
        </tr>
        <!-- Column header row -->
        <tr>
          <th class="fav-cell"></th>
          <th class="helmet-cell"></th>
          <th class="sortable-header" @click="setSortColumn('name')">
            Player <span v-if="sortColumn === 'name'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <th class="sortable-header" @click="setSortColumn('position_code')">
            Pos <span v-if="sortColumn === 'position_code'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <template v-if="statType === 'offense'">
            <th class="sortable-header col-pass col-divider" title="Completions" @click="setSortColumn('pass_comp')">
              CMP <span v-if="sortColumn === 'pass_comp'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-pass" title="Pass Attempts" @click="setSortColumn('pass_att')">
              ATT <span v-if="sortColumn === 'pass_att'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-pass" title="Pass Yards" @click="setSortColumn('pass_yds')">
              YDS <span v-if="sortColumn === 'pass_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-pass" title="Pass TDs" @click="setSortColumn('pass_td')">
              TD <span v-if="sortColumn === 'pass_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-pass" title="Interceptions thrown" @click="setSortColumn('pass_int')">
              INT <span v-if="sortColumn === 'pass_int'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-pass" title="QBR" @click="setSortColumn('pass_qbr')">
              QBR <span v-if="sortColumn === 'pass_qbr'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-pass" title="Passer Rating" @click="setSortColumn('pass_rating')">
              RTG <span v-if="sortColumn === 'pass_rating'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rush col-divider" title="Rush Attempts" @click="setSortColumn('rush_att')">
              ATT <span v-if="sortColumn === 'rush_att'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rush" title="Rush Yards" @click="setSortColumn('rush_yds')">
              YDS <span v-if="sortColumn === 'rush_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rush" title="Rush TDs" @click="setSortColumn('rush_td')">
              TD <span v-if="sortColumn === 'rush_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rush" title="Longest Rush" @click="setSortColumn('rush_long')">
              LONG <span v-if="sortColumn === 'rush_long'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rec col-divider" title="Receptions" @click="setSortColumn('rec_receptions')">
              REC <span v-if="sortColumn === 'rec_receptions'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rec" title="Targets" @click="setSortColumn('rec_targets')">
              TGT <span v-if="sortColumn === 'rec_targets'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rec" title="Receiving Yards" @click="setSortColumn('rec_yds')">
              YDS <span v-if="sortColumn === 'rec_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rec" title="Receiving TDs" @click="setSortColumn('rec_td')">
              TD <span v-if="sortColumn === 'rec_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-rec" title="Longest Reception" @click="setSortColumn('rec_long')">
              LONG <span v-if="sortColumn === 'rec_long'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-fum col-divider" title="Fumbles" @click="setSortColumn('fum_total')">
              FUM <span v-if="sortColumn === 'fum_total'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-fum" title="Fumbles Lost" @click="setSortColumn('fum_lost')">
              LOST <span v-if="sortColumn === 'fum_lost'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </template>
          <template v-else-if="statType === 'defense'">
            <th class="sortable-header col-tkl col-divider" title="Solo Tackles" @click="setSortColumn('def_solo')">
              SOLO <span v-if="sortColumn === 'def_solo'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-tkl" title="Assisted Tackles" @click="setSortColumn('def_ast')">
              AST <span v-if="sortColumn === 'def_ast'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-tkl" title="Sacks" @click="setSortColumn('def_sacks')">
              SACKS <span v-if="sortColumn === 'def_sacks'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-tkl" title="Tackles for Loss" @click="setSortColumn('def_tfl')">
              TFL <span v-if="sortColumn === 'def_tfl'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-cov col-divider" title="Passes Defensed" @click="setSortColumn('def_pd')">
              PD <span v-if="sortColumn === 'def_pd'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-cov" title="QB Hits" @click="setSortColumn('def_qb_hits')">
              QB HIT <span v-if="sortColumn === 'def_qb_hits'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-to col-divider" title="Interceptions" @click="setSortColumn('def_int')">
              INT <span v-if="sortColumn === 'def_int'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-to" title="Interception Return Yards" @click="setSortColumn('def_int_yds')">
              INT YDS <span v-if="sortColumn === 'def_int_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-to" title="Defensive TDs" @click="setSortColumn('def_td')">
              DEF TD <span v-if="sortColumn === 'def_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </template>
          <template v-else>
            <th class="sortable-header col-kick col-divider" title="Field Goals Made" @click="setSortColumn('k_fg_make')">
              FGM <span v-if="sortColumn === 'k_fg_make'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-kick" title="Field Goal Attempts" @click="setSortColumn('k_fg_att')">
              FGA <span v-if="sortColumn === 'k_fg_att'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-kick" title="Longest Field Goal" @click="setSortColumn('k_fg_long')">
              FG LONG <span v-if="sortColumn === 'k_fg_long'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-kick" title="Extra Points Made" @click="setSortColumn('k_xp_make')">
              XPM <span v-if="sortColumn === 'k_xp_make'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-kick" title="Extra Point Attempts" @click="setSortColumn('k_xp_att')">
              XPA <span v-if="sortColumn === 'k_xp_att'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-punt col-divider" title="Punts" @click="setSortColumn('p_no')">
              PUNTS <span v-if="sortColumn === 'p_no'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-punt" title="Punt Yards" @click="setSortColumn('p_yds')">
              P YDS <span v-if="sortColumn === 'p_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-punt" title="Inside 20" @click="setSortColumn('p_in20')">
              IN20 <span v-if="sortColumn === 'p_in20'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-punt" title="Touchbacks" @click="setSortColumn('p_tb')">
              TB <span v-if="sortColumn === 'p_tb'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-punt" title="Blocked Punts" @click="setSortColumn('p_blk')">
              BLK <span v-if="sortColumn === 'p_blk'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-punt" title="Longest Punt" @click="setSortColumn('p_long')">
              LONG <span v-if="sortColumn === 'p_long'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-ret col-divider" title="Kick Returns" @click="setSortColumn('ret_kick_no')">
              KR <span v-if="sortColumn === 'ret_kick_no'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-ret" title="Kick Return Yards" @click="setSortColumn('ret_kick_yds')">
              KR YDS <span v-if="sortColumn === 'ret_kick_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-ret" title="Kick Return TDs" @click="setSortColumn('ret_kick_td')">
              KR TD <span v-if="sortColumn === 'ret_kick_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-ret" title="Longest Kick Return" @click="setSortColumn('ret_kick_long')">
              KR LONG <span v-if="sortColumn === 'ret_kick_long'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-ret" title="Punt Returns" @click="setSortColumn('ret_punt_no')">
              PR <span v-if="sortColumn === 'ret_punt_no'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-ret" title="Punt Return Yards" @click="setSortColumn('ret_punt_yds')">
              PR YDS <span v-if="sortColumn === 'ret_punt_yds'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-ret" title="Punt Return TDs" @click="setSortColumn('ret_punt_td')">
              PR TD <span v-if="sortColumn === 'ret_punt_td'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="sortable-header col-ret" title="Longest Punt Return" @click="setSortColumn('ret_punt_long')">
              PR LONG <span v-if="sortColumn === 'ret_punt_long'" class="sort-arrow">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
          </template>
        </tr>
      </template>
      <tr v-for="p in pagedPlayers" :key="p.player_id">
        <td class="fav-cell">
          <FavoriteStar
            :is-favorited="favorites.has(p.player_id)"
            :loading="togglingFav === p.player_id"
            @toggle="toggleFav(p)"
          />
        </td>
        <td class="helmet-cell">
          <template v-if="p.team_abbr">
            <TeamHelmet :abbr="p.team_abbr" :size="24" />
          </template>
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
        <template v-if="statType === 'offense'">
          <td class="col-pass col-divider">{{ p.pass_comp }}</td>
          <td class="col-pass">{{ p.pass_att }}</td>
          <td class="col-pass">{{ p.pass_yds }}</td>
          <td class="col-pass">{{ p.pass_td }}</td>
          <td class="col-pass">{{ p.pass_int }}</td>
          <td class="col-pass">{{ typeof p.pass_qbr === 'number' ? p.pass_qbr.toFixed(1) : p.pass_qbr }}</td>
          <td class="col-pass">{{ typeof p.pass_rating === 'number' ? p.pass_rating.toFixed(1) : p.pass_rating }}</td>
          <td class="col-rush col-divider">{{ p.rush_att }}</td>
          <td class="col-rush">{{ p.rush_yds }}</td>
          <td class="col-rush">{{ p.rush_td }}</td>
          <td class="col-rush">{{ p.rush_long }}</td>
          <td class="col-rec col-divider">{{ p.rec_receptions }}</td>
          <td class="col-rec">{{ p.rec_targets }}</td>
          <td class="col-rec">{{ p.rec_yds }}</td>
          <td class="col-rec">{{ p.rec_td }}</td>
          <td class="col-rec">{{ p.rec_long }}</td>
          <td class="col-fum col-divider">{{ p.fum_total }}</td>
          <td class="col-fum">{{ p.fum_lost }}</td>
        </template>
        <template v-else-if="statType === 'defense'">
          <td class="col-tkl col-divider">{{ p.def_solo }}</td>
          <td class="col-tkl">{{ p.def_ast }}</td>
          <td class="col-tkl">{{ p.def_sacks }}</td>
          <td class="col-tkl">{{ p.def_tfl }}</td>
          <td class="col-cov col-divider">{{ p.def_pd }}</td>
          <td class="col-cov">{{ p.def_qb_hits }}</td>
          <td class="col-to col-divider">{{ p.def_int }}</td>
          <td class="col-to">{{ p.def_int_yds }}</td>
          <td class="col-to">{{ p.def_td }}</td>
        </template>
        <template v-else>
          <td class="col-kick col-divider">{{ p.k_fg_make }}</td>
          <td class="col-kick">{{ p.k_fg_att }}</td>
          <td class="col-kick">{{ p.k_fg_long }}</td>
          <td class="col-kick">{{ p.k_xp_make }}</td>
          <td class="col-kick">{{ p.k_xp_att }}</td>
          <td class="col-punt col-divider">{{ p.p_no }}</td>
          <td class="col-punt">{{ p.p_yds }}</td>
          <td class="col-punt">{{ p.p_in20 }}</td>
          <td class="col-punt">{{ p.p_tb }}</td>
          <td class="col-punt">{{ p.p_blk }}</td>
          <td class="col-punt">{{ p.p_long }}</td>
          <td class="col-ret col-divider">{{ p.ret_kick_no }}</td>
          <td class="col-ret">{{ p.ret_kick_yds }}</td>
          <td class="col-ret">{{ p.ret_kick_td }}</td>
          <td class="col-ret">{{ p.ret_kick_long }}</td>
          <td class="col-ret">{{ p.ret_punt_no }}</td>
          <td class="col-ret">{{ p.ret_punt_yds }}</td>
          <td class="col-ret">{{ p.ret_punt_td }}</td>
          <td class="col-ret">{{ p.ret_punt_long }}</td>
        </template>
      </tr>
    </AppTable>

    <AppPagination
      :total="sortedPlayers.length"
      :page="currentPage"
      :per-page="perPage"
      @update:page="currentPage = $event"
      @update:per-page="perPage = $event; currentPage = 1"
    />
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
import AppPagination from '@/components/ui/AppPagination.vue'

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
const currentPage = ref(1)
const perPage = ref(10)

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

const pagedPlayers = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return sortedPlayers.value.slice(start, start + perPage.value)
})

function setSortColumn(col: string) {
  if (sortColumn.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = col
    // Default to asc for text/array columns, desc for numeric
    const sample = players.value[0]?.[col]
    sortDir.value = (typeof sample === 'string' || Array.isArray(sample)) ? 'asc' : 'desc'
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
  currentPage.value = 1
})

watch([position, year, statType, sortColumn, sortDir], () => {
  currentPage.value = 1
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
