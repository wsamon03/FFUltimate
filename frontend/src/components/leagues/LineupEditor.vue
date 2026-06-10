<template>
  <div class="space-y-3">
    <div
      v-for="slot in SLOTS"
      :key="slot.position"
      class="flex items-center gap-3 p-3 rounded-lg border"
      style="border-color: var(--color-border); background: var(--color-card)"
    >
      <div class="w-12 shrink-0">
        <PositionBadge :position="slot.position" />
      </div>
      <select
        :value="lineup[slot.position]"
        class="flex-1 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
        style="
          background: var(--color-bg);
          border-color: var(--color-border);
          color: var(--color-text-primary);
          --tw-ring-color: var(--color-primary);
        "
        @change="onSlotChange(slot.position, ($event.target as HTMLSelectElement).value)"
      >
        <option value="">— Empty —</option>
        <option
          v-for="p in eligiblePlayers(slot.position)"
          :key="p.player_id"
          :value="p.player_id"
        >
          {{ p.full_name || p.player_name || p.player_id }}
        </option>
      </select>
    </div>

    <AppButton class="mt-2" :loading="saving" @click="$emit('save', lineup)">
      Save Lineup
    </AppButton>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import PositionBadge from '@/components/common/PositionBadge.vue'
import AppButton from '@/components/ui/AppButton.vue'

const SLOTS = [
  { position: 'QB' },
  { position: 'RB1' },
  { position: 'RB2' },
  { position: 'WR1' },
  { position: 'WR2' },
  { position: 'TE' },
  { position: 'FLEX' },
  { position: 'K' },
  { position: 'DEF' },
  { position: 'BN1' },
  { position: 'BN2' },
  { position: 'BN3' },
  { position: 'BN4' },
  { position: 'BN5' },
  { position: 'BN6' },
]

const props = defineProps<{ roster: any[]; initialLineup?: Record<string, string>; saving?: boolean }>()
defineEmits<{ save: [lineup: Record<string, string>] }>()

const lineup = reactive<Record<string, string>>(
  Object.fromEntries(SLOTS.map(s => [s.position, props.initialLineup?.[s.position] ?? ''])),
)

const FLEX_POSITIONS = new Set(['RB', 'WR', 'TE'])
const SLOT_TO_POSITIONS: Record<string, Set<string>> = {
  QB: new Set(['QB']),
  RB1: new Set(['RB']),
  RB2: new Set(['RB']),
  WR1: new Set(['WR']),
  WR2: new Set(['WR']),
  TE: new Set(['TE']),
  FLEX: FLEX_POSITIONS,
  K: new Set(['K']),
  DEF: new Set(['DEF', 'D/ST']),
}

function eligiblePlayers(slotPosition: string) {
  const allowed = SLOT_TO_POSITIONS[slotPosition]
  if (!allowed) return props.roster // bench: all players eligible
  return props.roster.filter(p => allowed.has(p.position?.toUpperCase() ?? ''))
}

function onSlotChange(slotPosition: string, playerId: string) {
  lineup[slotPosition] = playerId
}
</script>
