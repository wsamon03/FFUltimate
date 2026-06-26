<template>
  <div class="draft-board-wrap">
    <div v-if="!order.length" class="empty-msg">Draft order not set yet.</div>
    <div v-else class="board-scroll">
      <!-- Header row: team names -->
      <div class="board-grid" :style="gridStyle">
        <div class="cell cell-round-label"></div>
        <div v-for="entry in order" :key="entry.slot_position" class="cell cell-header">
          {{ shortName(entry.team_name) }}
        </div>

        <!-- Pick rows by round -->
        <template v-for="round in totalRounds" :key="round">
          <div class="cell cell-round-label">R{{ round }}</div>
          <div
            v-for="slot in order.length"
            :key="slot"
            class="cell cell-pick"
            :class="{
              'is-current': pickMap.get(pickNumber(round, slot))?.pick_number === currentPick,
              'is-my-team': pickMap.get(pickNumber(round, slot))?.league_team_id === myTeamId,
              'is-filled': !!pickMap.get(pickNumber(round, slot))?.player_id,
            }"
          >
            <template v-if="pickMap.get(pickNumber(round, slot))?.player_id">
              <span class="pick-pos">{{ pickMap.get(pickNumber(round, slot))?.position_code }}</span>
              <span class="pick-name">{{ shortPlayerName(pickMap.get(pickNumber(round, slot))?.player_name) }}</span>
            </template>
            <template v-else>
              <span class="pick-num">{{ pickNumber(round, slot) }}</span>
            </template>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  order: any[]
  picks: any[]
  currentPick: number
  myTeamId: string
}>()

const totalRounds = computed(() => {
  if (!props.picks.length) return 15
  return Math.max(...props.picks.map((p: any) => p.round_number))
})

const gridStyle = computed(() => ({
  gridTemplateColumns: `3rem repeat(${props.order.length}, minmax(80px, 1fr))`,
}))

const pickMap = computed(() => {
  const m = new Map<number, any>()
  for (const p of props.picks) m.set(p.pick_number, p)
  return m
})

function pickNumber(round: number, slot: number): number {
  const n = props.order.length
  const isEven = round % 2 === 0
  const posInRound = isEven ? n - slot + 1 : slot
  return (round - 1) * n + posInRound
}

function shortName(name: string): string {
  return name?.length > 10 ? name.substring(0, 9) + '…' : (name ?? '?')
}

function shortPlayerName(name?: string | null): string {
  if (!name) return ''
  const trimmed = name.trim()
  if (!trimmed) return ''
  const parts = trimmed.split(' ').filter(Boolean)
  if (parts.length < 2) return trimmed.substring(0, 12)
  return `${parts[0][0]}. ${parts.slice(1).join(' ')}`.substring(0, 12)
}
</script>

<style scoped>
.draft-board-wrap { height: 100%; overflow: hidden; display: flex; flex-direction: column; }
.empty-msg { padding: 1rem; color: var(--color-text-muted, #94a3b8); }
.board-scroll { overflow: auto; flex: 1; }
.board-grid {
  display: grid;
  gap: 2px;
  padding-bottom: 0.5rem;
}
.cell {
  padding: 0.25rem 0.3rem;
  font-size: 0.7rem;
  border-radius: 0.2rem;
  background: var(--color-surface-alt, #1e293b);
  min-height: 2.4rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}
.cell-round-label {
  background: transparent;
  font-weight: 700;
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.65rem;
  align-items: center;
}
.cell-header {
  font-weight: 700;
  font-size: 0.7rem;
  text-align: center;
  background: var(--color-surface, #0f172a);
  align-items: center;
}
.cell-pick.is-current {
  border: 2px solid var(--color-primary, #6366f1);
}
.cell-pick.is-my-team {
  background: color-mix(in srgb, var(--color-primary, #6366f1) 15%, var(--color-surface-alt, #1e293b));
}
.cell-pick.is-filled { background: var(--color-surface, #0f172a); }
.pick-pos { font-size: 0.6rem; font-weight: 700; color: var(--color-text-muted, #94a3b8); }
.pick-name { font-size: 0.7rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pick-num { color: var(--color-text-muted, #94a3b8); font-size: 0.65rem; text-align: center; width: 100%; }
</style>
