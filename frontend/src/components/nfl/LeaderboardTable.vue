<template>
  <div class="space-y-4">
    <!-- Category tabs -->
    <div class="flex gap-1 border-b" style="border-color: var(--color-border)">
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
]

const colMap: Record<string, { key: string; label: string }[]> = {
  passing:   [{ key: 'pass_yards', label: 'Yards' }, { key: 'pass_tds', label: 'TDs' }, { key: 'interceptions', label: 'INT' }],
  rushing:   [{ key: 'rush_yards', label: 'Yards' }, { key: 'rush_tds', label: 'TDs' }, { key: 'rush_attempts', label: 'ATT' }],
  receiving: [{ key: 'rec_yards', label: 'Yards' }, { key: 'rec_tds', label: 'TDs' }, { key: 'receptions', label: 'REC' }],
}

const activeCategory = ref('passing')
const loading = ref(false)
const rows = ref<any[]>([])
const sortColumn = ref<string | null>(null)
const sortDir = ref<'asc' | 'desc'>('desc')

const activeCols = computed(() => colMap[activeCategory.value] ?? [])

const sortedRows = computed(() => {
  if (!sortColumn.value) {
    return rows.value
  }

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
    rows.value = await getLeaderboard(props.gameId, activeCategory.value as 'passing' | 'rushing' | 'receiving')
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
