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
          <th>#</th>
          <th>Player</th>
          <th>Team</th>
          <th v-for="col in activeCols" :key="col.key">{{ col.label }}</th>
        </tr>
      </template>
      <tr v-for="(row, i) in rows" :key="row.player_id">
        <td style="color: var(--color-text-secondary)">{{ i + 1 }}</td>
        <td>
          <RouterLink :to="`/players/${row.player_id}`" class="font-medium hover:underline"
            style="color: var(--color-primary)">
            {{ row.player_name || row.player_id }}
          </RouterLink>
        </td>
        <td style="color: var(--color-text-secondary)">{{ row.team_nm || '—' }}</td>
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

const activeCols = computed(() => colMap[activeCategory.value] ?? [])

async function selectCategory(cat: string) {
  activeCategory.value = cat
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
