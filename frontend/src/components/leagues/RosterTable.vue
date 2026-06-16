<template>
  <AppTable>
    <template #head>
      <tr>
        <th class="sortable-header" @click="setSortColumn('full_name')">
          Player <span v-if="sortColumn === 'full_name'" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
        </th>
        <th class="sortable-header" @click="setSortColumn('position')">
          Position <span v-if="sortColumn === 'position'" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
        </th>
        <th class="sortable-header" @click="setSortColumn('slot_position')">
          Slot <span v-if="sortColumn === 'slot_position'" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
        </th>
        <th></th>
      </tr>
    </template>
    <tr v-if="sortedRoster.length === 0">
      <td colspan="4" class="text-center py-8" style="color: var(--color-text-secondary)">No players on roster</td>
    </tr>
    <tr v-for="row in sortedRoster" :key="row.player_id">
      <td>
        <RouterLink :to="`/players/${row.player_id}`" class="font-medium hover:underline"
          style="color: var(--color-primary)">
          {{ row.full_name || row.player_name || row.player_id }}
        </RouterLink>
      </td>
      <td><PositionBadge :position="row.position || '—'" /></td>
      <td style="color: var(--color-text-secondary)">{{ row.slot_position || 'BN' }}</td>
      <td>
        <button
          v-if="canEdit"
          class="text-xs px-2 py-1 rounded transition-colors hover:bg-red-500/20"
          style="color: var(--color-text-secondary)"
          @click="$emit('drop', row.player_id)"
        >
          Drop
        </button>
      </td>
    </tr>
  </AppTable>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AppTable from '@/components/ui/AppTable.vue'
import PositionBadge from '@/components/common/PositionBadge.vue'

const props = defineProps<{ roster: any[]; canEdit?: boolean }>()
defineEmits<{ drop: [playerId: string] }>()

const sortColumn = ref<string | null>('full_name')
const sortDir = ref<'asc' | 'desc'>('asc')

const sortedRoster = computed(() => {
  if (!sortColumn.value) {
    return props.roster
  }

  const sorted = [...props.roster]
  sorted.sort((a, b) => {
    const aVal = a[sortColumn.value!]
    const bVal = b[sortColumn.value!]

    if (aVal == null && bVal == null) return 0
    if (aVal == null) return 1
    if (bVal == null) return -1

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
    sortDir.value = 'asc'
  }
}
</script>

<style scoped>
.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.sortable-header:hover {
  color: var(--color-primary) !important;
}
</style>
