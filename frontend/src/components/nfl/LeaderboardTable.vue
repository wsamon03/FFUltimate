<template>
  <div class="space-y-4">
    <!-- Category tabs -->
    <div class="flex flex-wrap gap-1 border-b" style="border-color: var(--color-border)">
      <button
        v-for="cat in categories"
        :key="cat.value"
        class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
        :style="activeCategory === cat.value
          ? `border-color: var(--color-primary); color: var(--color-primary)`
          : `border-color: transparent; color: var(--color-text-secondary)`"
        @click="selectCategory(cat.value)"
      >
        {{ cat.label }}
      </button>
    </div>

    <AppSpinner v-if="loading" />

    <AppEmptyState v-else-if="rows.length === 0" title="No stats available" />

    <AppTable v-else>
      <template #head>
        <tr>
          <th class="sortable-header" @click="setSortColumn(null)">
            # <span v-if="sortColumn === null" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <th></th>
          <th class="sortable-header" @click="setSortColumn('player_name')">
            Player <span v-if="sortColumn === 'player_name'" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
          <th v-for="col in activeCols" :key="col.key" class="sortable-header" @click="setSortColumn(col.key)">
            {{ col.label }} <span v-if="sortColumn === col.key" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
        </tr>
      </template>
      <tr v-for="(row, i) in sortedRows" :key="row.player_id">
        <td class="rank-cell" style="color: var(--color-text-secondary)">{{ i + 1 }}</td>
        <td class="helmet-cell">
          <TeamHelmet v-if="row.team_nm" :abbr="row.team_nm" :size="24" />
          <span v-else style="color: var(--color-text-secondary)">—</span>
        </td>
        <td>
          <RouterLink :to="`/players/${row.player_id}`" class="font-medium hover:underline"
            style="color: var(--color-primary)">
            {{ row.player_name || row.player_id }}
          </RouterLink>
        </td>
        <td v-for="col in activeCols" :key="col.key" style="color: var(--color-text-primary)">
          {{ row[col.key] ?? '—' }}
        </td>
      </tr>
      <template v-if="teamTotals.length > 0">
        <tr
          v-for="t in teamTotals"
          :key="`total-${t.team_nm}`"
          style="border-top: 2px solid var(--color-border); font-weight: bold"
        >
          <td class="rank-cell" style="color: var(--color-text-secondary)">—</td>
          <td class="helmet-cell">
            <TeamHelmet v-if="t.team_nm" :abbr="t.team_nm" :size="24" />
          </td>
          <td style="color: var(--color-text-primary)">{{ t.team_nm }} Total</td>
          <td
            v-for="col in activeCols"
            :key="col.key"
            style="color: var(--color-text-primary)"
          >{{ t[col.key] ?? '—' }}</td>
        </tr>
      </template>
    </AppTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getLeaderboard } from '@/api/stats'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import TeamHelmet from '@/components/common/TeamHelmet.vue'

const props = defineProps<{ gameId: string }>()

const categories = [
  { value: 'passing',   label: 'Passing' },
  { value: 'rushing',   label: 'Rushing' },
  { value: 'receiving', label: 'Receiving' },
  { value: 'defense',   label: 'Defense' },
  { value: 'fumbles',   label: 'Fumbles' },
  { value: 'kicking',   label: 'Kicking' },
  { value: 'returns',   label: 'Returns' },
]

const colMap: Record<string, { key: string; label: string }[]> = {
  passing: [
    { key: 'pass_comp',   label: 'CMP' },
    { key: 'pass_att',    label: 'ATT' },
    { key: 'pass_yds',    label: 'YDS' },
    { key: 'pass_td',     label: 'TD' },
    { key: 'pass_int',    label: 'INT' },
    { key: 'pass_sacked', label: 'SCK' },
    { key: 'pass_qbr',    label: 'QBR' },
    { key: 'pass_rating', label: 'RTG' },
  ],
  rushing: [
    { key: 'rush_att',  label: 'ATT' },
    { key: 'rush_yds',  label: 'YDS' },
    { key: 'rush_td',   label: 'TD' },
    { key: 'rush_long', label: 'LNG' },
  ],
  receiving: [
    { key: 'rec_receptions', label: 'REC' },
    { key: 'rec_targets',    label: 'TGT' },
    { key: 'rec_yds',        label: 'YDS' },
    { key: 'rec_td',         label: 'TD' },
    { key: 'rec_long',       label: 'LNG' },
  ],
  defense: [
    { key: 'def_solo',    label: 'SOLO' },
    { key: 'def_ast',     label: 'AST' },
    { key: 'def_sacks',   label: 'SCK' },
    { key: 'def_tfl',     label: 'TFL' },
    { key: 'def_pd',      label: 'PD' },
    { key: 'def_qb_hits', label: 'QB HIT' },
    { key: 'def_int',     label: 'INT' },
    { key: 'def_int_yds', label: 'INT YDS' },
    { key: 'def_td',      label: 'TD' },
  ],
  fumbles: [
    { key: 'fum_total', label: 'FUM' },
    { key: 'fum_lost',  label: 'LOST' },
    { key: 'fum_rec',   label: 'REC' },
  ],
  kicking: [
    { key: 'k_fg_make', label: 'FGM' },
    { key: 'k_fg_att',  label: 'FGA' },
    { key: 'k_fg_long', label: 'LNG' },
    { key: 'k_xp_make', label: 'XPM' },
    { key: 'k_xp_att',  label: 'XPA' },
    { key: 'p_no',      label: 'PUNTS' },
    { key: 'p_yds',     label: 'P YDS' },
    { key: 'p_long',    label: 'P LNG' },
    { key: 'p_in20',    label: 'IN20' },
    { key: 'p_tb',      label: 'TB' },
    { key: 'p_blk',     label: 'BLK' },
  ],
  returns: [
    { key: 'ret_kick_no',   label: 'KR NO' },
    { key: 'ret_kick_yds',  label: 'KR YDS' },
    { key: 'ret_kick_td',   label: 'KR TD' },
    { key: 'ret_kick_long', label: 'KR LNG' },
    { key: 'ret_punt_no',   label: 'PR NO' },
    { key: 'ret_punt_yds',  label: 'PR YDS' },
    { key: 'ret_punt_td',   label: 'PR TD' },
    { key: 'ret_punt_long', label: 'PR LNG' },
  ],
}

const activeCategory = ref('passing')
const loading = ref(false)
const rows = ref<any[]>([])
const sortColumn = ref<string | null>(null)
const sortDir = ref<'asc' | 'desc'>('desc')

const activeCols = computed(() => colMap[activeCategory.value] ?? [])

const teamTotals = computed(() => {
  const groups: Record<string, any> = {}
  for (const row of rows.value) {
    const t = row.team_nm
    if (!t) continue
    if (!groups[t]) groups[t] = { team_nm: t }
    for (const col of activeCols.value) {
      groups[t][col.key] = (groups[t][col.key] || 0) + (row[col.key] || 0)
    }
  }
  return Object.values(groups)
})

const sortedRows = computed(() => {
  if (!sortColumn.value) return rows.value

  const sorted = [...rows.value]
  sorted.sort((a, b) => {
    const aVal = a[sortColumn.value!]
    const bVal = b[sortColumn.value!]

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

  return sorted
})

function setSortColumn(col: string | null) {
  if (sortColumn.value === col) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = col
    sortDir.value = 'desc'
  }
}

async function selectCategory(cat: string) {
  activeCategory.value = cat
  sortColumn.value = null
  sortDir.value = 'desc'
  await load()
}

async function load() {
  loading.value = true
  try {
    rows.value = await getLeaderboard(props.gameId, activeCategory.value as any)
  } finally {
    loading.value = false
  }
}

watch(() => props.gameId, load, { immediate: true })
</script>

<style scoped>
.rank-cell {
  white-space: nowrap;
  flex-shrink: 0;
  text-align: center;
  padding: 8px 6px;
}

.helmet-cell {
  white-space: nowrap;
  flex-shrink: 0;
  text-align: center;
  padding: 8px 6px;
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.sortable-header:hover {
  color: var(--color-primary) !important;
}
</style>
