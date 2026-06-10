<template>
  <AppTable>
    <template #head>
      <tr>
        <th>Player</th>
        <th>Position</th>
        <th>Slot</th>
        <th></th>
      </tr>
    </template>
    <tr v-if="roster.length === 0">
      <td colspan="4" class="text-center py-8" style="color: var(--color-text-secondary)">No players on roster</td>
    </tr>
    <tr v-for="row in roster" :key="row.player_id">
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
import AppTable from '@/components/ui/AppTable.vue'
import PositionBadge from '@/components/common/PositionBadge.vue'

defineProps<{ roster: any[]; canEdit?: boolean }>()
defineEmits<{ drop: [playerId: string] }>()
</script>
