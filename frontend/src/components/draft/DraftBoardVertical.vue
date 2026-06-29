<template>
  <div class="board-vert">
    <div class="board-header">
      <span class="board-title">Draft Board</span>
      <div class="board-btns">
        <button v-if="userScrolledAway" class="btn-curr-pick" @click="goToCurrentPick">
          Current Pick
        </button>
        <button class="btn-full-board" @click="emit('showFullBoard')">Full Board</button>
      </div>
    </div>

    <div ref="scrollEl" class="picks-viewport" @scroll.passive="onScroll">
      <div
        v-for="pick in allPicks"
        :key="pick.pick_number"
        :ref="(el) => setPickEl(pick.pick_number, el)"
        class="pick-row"
        :class="{
          'is-current': pick.pick_number === currentPick,
          'is-my-team': pickTeamId(pick) === myTeamId,
          'is-filled': !!pick.player_id,
        }"
      >
        <span class="pick-num">#{{ pick.pick_number }}</span>
        <div class="pick-mid">
          <span class="pick-round">R{{ pick.round_number }}</span>
          <span class="pick-team">{{ shortName(pickTeamName(pick)) }}</span>
        </div>
        <span v-if="pick.player_id" class="pick-player">
          <span class="pick-pos" :style="{ background: posColor(pick.position_code) }">
            {{ pick.position_code }}
          </span>
          {{ shortPlayerName(pick.player_name) }}
        </span>
        <span v-else class="pick-open">open</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

const SCROLL_AWAY_THRESHOLD = 3
const PICK_ROW_HEIGHT = 44

const props = defineProps<{
  order: any[]
  picks: any[]
  currentPick: number
  myTeamId: string
}>()

const emit = defineEmits<{
  (e: 'showFullBoard'): void
}>()

const scrollEl = ref<HTMLElement | null>(null)
const pickEls = new Map<number, Element>()
const userScrolledAway = ref(false)

function setPickEl(pickNum: number, el: any) {
  if (el) pickEls.set(pickNum, el as Element)
}

const totalRounds = computed(() => {
  if (!props.picks.length) return 15
  return Math.max(...props.picks.map((p: any) => p.round_number))
})

const allPicks = computed(() => {
  const m = new Map<number, any>()
  for (const p of props.picks) m.set(p.pick_number, p)

  const n = props.order.length
  if (!n) return []

  const result: any[] = []
  const total = totalRounds.value * n

  for (let pickNum = 1; pickNum <= total; pickNum++) {
    if (m.has(pickNum)) {
      result.push(m.get(pickNum))
    } else {
      const round = Math.ceil(pickNum / n)
      const pickInRound = pickNum - (round - 1) * n
      const isEven = round % 2 === 0
      const slotPos = isEven ? n - pickInRound + 1 : pickInRound
      const orderEntry = props.order.find((o: any) => o.slot_position === slotPos)
      result.push({
        pick_number: pickNum,
        round_number: round,
        league_team_id: orderEntry?.league_team_id ?? null,
        team_name: orderEntry?.team_name ?? '?',
        player_id: null,
        player_name: null,
        position_code: null,
      })
    }
  }
  return result
})

function pickTeamId(pick: any): string {
  return pick.league_team_id ?? ''
}

function pickTeamName(pick: any): string {
  if (pick.team_name) return pick.team_name
  const orderEntry = props.order.find((o: any) => o.league_team_id === pick.league_team_id)
  return orderEntry?.team_name ?? '?'
}

function shortName(name: string): string {
  if (!name) return '?'
  return name.length > 12 ? name.substring(0, 11) + '…' : name
}

function shortPlayerName(name?: string | null): string {
  if (!name) return ''
  const trimmed = name.trim()
  if (!trimmed) return ''
  const parts = trimmed.split(' ').filter(Boolean)
  if (parts.length < 2) return trimmed.substring(0, 14)
  return `${parts[0][0]}. ${parts.slice(1).join(' ')}`.substring(0, 14)
}

const POS_COLORS: Record<string, string> = {
  QB: '#ef4444', RB: '#22c55e', WR: '#3b82f6', TE: '#f59e0b',
  K: '#8b5cf6', DST: '#06b6d4', DEF: '#06b6d4',
}
function posColor(pos?: string | null): string {
  return POS_COLORS[pos ?? ''] ?? '#64748b'
}

function scrollToCurrentPick() {
  nextTick(() => {
    const el = scrollEl.value
    if (!el) return
    const rowEl = pickEls.get(props.currentPick)
    if (!rowEl) return
    const rowOffset = (rowEl as HTMLElement).offsetTop
    const viewportH = el.clientHeight
    const targetScroll = rowOffset - viewportH / 2 + PICK_ROW_HEIGHT / 2
    el.scrollTo({ top: Math.max(0, targetScroll), behavior: 'smooth' })
  })
}

function goToCurrentPick() {
  userScrolledAway.value = false
  scrollToCurrentPick()
}

function onScroll() {
  const el = scrollEl.value
  if (!el) return
  const rowEl = pickEls.get(props.currentPick)
  if (!rowEl) return
  const currentRowOffset = (rowEl as HTMLElement).offsetTop
  const viewportCenter = el.scrollTop + el.clientHeight / 2
  const picksAway = Math.abs(viewportCenter - currentRowOffset) / PICK_ROW_HEIGHT
  if (picksAway > SCROLL_AWAY_THRESHOLD) {
    userScrolledAway.value = true
  }
}

watch(
  () => props.currentPick,
  () => {
    if (!userScrolledAway.value) scrollToCurrentPick()
  },
  { immediate: true },
)
</script>

<style scoped>
.board-vert {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}
.board-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.5rem;
  flex-shrink: 0;
  border-bottom: 1px solid var(--color-border, #334155);
}
.board-title {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #94a3b8);
}
.board-btns { display: flex; gap: 0.35rem; }
.btn-curr-pick,
.btn-full-board {
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid var(--color-border, #334155);
  background: var(--color-surface-alt, #1e293b);
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  font-size: 0.7rem;
  font-weight: 600;
}
.btn-curr-pick {
  background: var(--color-primary, #6366f1);
  border-color: var(--color-primary, #6366f1);
  color: #fff;
}
.btn-curr-pick:hover { opacity: 0.85; }
.btn-full-board:hover { background: var(--color-surface, #0f172a); }

.picks-viewport {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.pick-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.5rem;
  min-height: 44px;
  border-bottom: 1px solid var(--color-border, #334155);
  flex-shrink: 0;
  background: var(--color-surface-alt, #1e293b);
  font-size: 0.78rem;
  transition: background 0.1s;
}
.pick-row.is-current {
  border-left: 3px solid var(--color-primary, #6366f1);
  background: color-mix(in srgb, var(--color-primary, #6366f1) 12%, var(--color-surface-alt, #1e293b));
}
.pick-row.is-my-team {
  background: color-mix(in srgb, var(--color-primary, #6366f1) 8%, var(--color-surface-alt, #1e293b));
}
.pick-row.is-current.is-my-team {
  background: color-mix(in srgb, var(--color-primary, #6366f1) 18%, var(--color-surface-alt, #1e293b));
}
.pick-num {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--color-text-muted, #94a3b8);
  min-width: 1.8rem;
  flex-shrink: 0;
}
.pick-mid {
  display: flex;
  flex-direction: column;
  min-width: 3.5rem;
  flex-shrink: 0;
}
.pick-round { font-size: 0.65rem; color: var(--color-text-muted, #94a3b8); }
.pick-team { font-size: 0.72rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pick-player {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-width: 0;
  flex: 1;
  overflow: hidden;
}
.pick-pos {
  display: inline-block;
  padding: 0.05rem 0.3rem;
  border-radius: 0.2rem;
  font-size: 0.65rem;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.pick-open {
  font-size: 0.7rem;
  color: var(--color-text-muted, #94a3b8);
  font-style: italic;
  flex: 1;
}
</style>
