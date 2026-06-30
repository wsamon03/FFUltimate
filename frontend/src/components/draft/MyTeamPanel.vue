<template>
  <div class="my-team-panel">
    <div class="view-toggle">
      <button :class="['toggle-btn', { active: viewMode === 'round' }]" @click="viewMode = 'round'">Round</button>
      <button :class="['toggle-btn', { active: viewMode === 'position' }]" @click="viewMode = 'position'">Position</button>
      <button :class="['toggle-btn', { active: viewMode === 'starters' }]" @click="viewMode = 'starters'">Starters</button>
    </div>

    <div class="picks-scroll">
      <!-- ROUND VIEW -->
      <template v-if="viewMode === 'round'">
        <div v-if="!myPicks.length" class="empty-msg">No picks yet.</div>
        <div v-for="pick in myPicks" :key="pick.pick_number" class="pick-row">
          <span class="round-label">R{{ pick.round_number }}</span>
          <PlayerDraftCard :player="{ name: pick.player_name, position_code: pick.position_code, team_abbr: pick.team_abbr }" />
        </div>
      </template>

      <!-- POSITION VIEW -->
      <template v-else-if="viewMode === 'position'">
        <div v-if="!myPicks.length" class="empty-msg">No picks yet.</div>
        <template v-for="group in byPosition" :key="group.position">
          <div class="pos-section-header" :style="{ borderLeftColor: posColor(group.position) }">
            <span class="pos-section-badge" :style="{ background: posColor(group.position) }">{{ group.position }}</span>
          </div>
          <div v-for="pick in group.picks" :key="pick.pick_number" class="pick-row pick-indented">
            <PlayerDraftCard :player="{ name: pick.player_name, position_code: pick.position_code, team_abbr: pick.team_abbr }" :show-position="false" />
          </div>
        </template>
      </template>

      <!-- STARTERS VIEW -->
      <template v-else-if="viewMode === 'starters'">
        <div v-if="loadingSettings" class="empty-msg">Loading…</div>
        <template v-else>
          <div v-if="!myPicks.length" class="empty-msg">No picks yet.</div>
          <template v-else>
            <div v-for="(slot, idx) in starterSlots" :key="idx" class="pick-row starter-row">
              <span class="slot-badge" :style="slotBadgeStyle(slot.positions)">{{ slot.label }}</span>
              <template v-if="slot.player">
                <PlayerDraftCard :player="{ name: slot.player.player_name, position_code: slot.player.position_code, team_abbr: slot.player.team_abbr }" :show-position="false" />
              </template>
              <span v-else class="empty-slot">—</span>
            </div>

            <template v-if="benchPicks.length">
              <div class="bench-header">BENCH</div>
              <div
                v-for="pick in benchPicks"
                :key="pick.pick_number"
                class="pick-row bench-row"
                :style="{ background: posColor(pick.position_code) }"
              >
                <PlayerDraftCard
                  :player="{ name: pick.player_name, position_code: pick.position_code, team_abbr: pick.team_abbr }"
                  :show-position="false"
                  :meta-text="`${pick.position_code ?? '?'} · ${pick.team_abbr ?? '—'}`"
                />
              </div>
            </template>
          </template>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getLeagueSettings } from '@/api/leagues'
import PlayerDraftCard from './PlayerDraftCard.vue'

const POS_COLORS: Record<string, string> = {
  QB: '#ef4444', RB: '#22c55e', WR: '#3b82f6', TE: '#f59e0b',
  K: '#8b5cf6', DST: '#06b6d4', DEF: '#06b6d4',
}
function posColor(pos?: string | null): string {
  return POS_COLORS[pos ?? ''] ?? '#64748b'
}

const SLOT_DEFS = [
  { key: 'qb',        label: 'QB',   positions: ['QB'] },
  { key: 'rb',        label: 'RB',   positions: ['RB'] },
  { key: 'wr',        label: 'WR',   positions: ['WR'] },
  { key: 'te',        label: 'TE',   positions: ['TE'] },
  { key: 'flex',      label: 'FLEX', positions: ['RB', 'WR', 'TE'] },
  { key: 'superflex', label: 'SFLX', positions: ['QB', 'RB', 'WR', 'TE'] },
  { key: 'k',         label: 'K',    positions: ['K'] },
  { key: 'dst',       label: 'DST',  positions: ['DST', 'DEF'] },
  { key: 'idp_dl',    label: 'DL',   positions: ['DL', 'DE', 'DT', 'NT'] },
  { key: 'idp_dt',    label: 'DT',   positions: ['DT', 'NT'] },
  { key: 'idp_edge',  label: 'EDGE', positions: ['DE', 'OLB'] },
  { key: 'idp_lb',    label: 'LB',   positions: ['LB', 'ILB', 'OLB', 'MLB'] },
  { key: 'idp_ilb',   label: 'ILB',  positions: ['ILB', 'MLB'] },
  { key: 'idp_db',    label: 'DB',   positions: ['DB', 'CB', 'S', 'SS', 'FS'] },
  { key: 'idp_cb',    label: 'CB',   positions: ['CB'] },
  { key: 'idp_s',     label: 'S',    positions: ['S', 'SS', 'FS'] },
]

const POS_ORDER = ['QB', 'RB', 'WR', 'TE', 'K', 'DST', 'DEF']

function slotBadgeStyle(positions: string[]): Record<string, string> {
  if (positions.length === 1) return { background: posColor(positions[0]) }
  const c1 = posColor(positions[0])
  const c2 = posColor(positions[1])
  return { background: `linear-gradient(90deg, ${c1} 50%, ${c2} 50%)` }
}

const props = defineProps<{
  picks: any[]
  teamId: string
  leagueId: string
}>()

const viewMode = ref<'round' | 'position' | 'starters'>('round')
const rosterConfig = ref<any>(null)
const loadingSettings = ref(false)

const myPicks = computed(() =>
  props.picks
    .filter((p: any) => p.league_team_id === props.teamId && !!p.player_id)
    .sort((a: any, b: any) => a.pick_number - b.pick_number),
)

const byPosition = computed(() => {
  const groups = new Map<string, any[]>()
  for (const pick of myPicks.value) {
    const pos = pick.position_code ?? 'UNK'
    if (!groups.has(pos)) groups.set(pos, [])
    groups.get(pos)!.push(pick)
  }
  return [...groups.entries()]
    .sort(([a], [b]) => {
      const ai = POS_ORDER.indexOf(a)
      const bi = POS_ORDER.indexOf(b)
      return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi)
    })
    .map(([position, picks]) => ({ position, picks }))
})

const starterSlots = computed(() => {
  const cfg = rosterConfig.value
  const slots: { label: string; positions: string[]; player: any | null }[] = []
  const used = new Set<string>()

  for (const def of SLOT_DEFS) {
    const count: number = cfg ? (cfg[def.key] ?? 0) : (def.positions.length === 1 && ['QB', 'RB', 'WR', 'TE', 'K', 'DST'].includes(def.label) ? 1 : 0)
    for (let i = 0; i < count; i++) {
      const player = myPicks.value.find(
        (p: any) => def.positions.includes(p.position_code ?? '') && !used.has(p.player_id)
      ) ?? null
      if (player) used.add(player.player_id)
      slots.push({ label: def.label, positions: def.positions, player })
    }
  }
  return slots
})

const benchPicks = computed(() => {
  const starterIds = new Set(
    starterSlots.value.filter(s => s.player !== null).map(s => s.player.player_id)
  )
  return myPicks.value.filter((p: any) => !starterIds.has(p.player_id))
})

onMounted(async () => {
  if (!props.leagueId) return
  loadingSettings.value = true
  try {
    const settings = await getLeagueSettings(props.leagueId)
    rosterConfig.value = settings?.roster ?? null
  } catch {
    // fall back to defaults built into SLOT_DEFS
  } finally {
    loadingSettings.value = false
  }
})
</script>

<style scoped>
.my-team-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.view-toggle {
  display: flex;
  gap: 0.2rem;
  padding: 0.3rem 0.4rem;
  flex-shrink: 0;
  border-bottom: 1px solid var(--color-border, #334155);
}
.toggle-btn {
  flex: 1;
  padding: 0.15rem 0;
  background: transparent;
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.2rem;
  color: var(--color-text-muted, #94a3b8);
  cursor: pointer;
  font-size: 0.68rem;
  font-weight: 600;
  transition: background 0.12s, color 0.12s;
}
.toggle-btn.active {
  background: var(--color-primary, #6366f1);
  border-color: var(--color-primary, #6366f1);
  color: #fff;
}
.toggle-btn:not(.active):hover {
  background: var(--color-surface-alt, #1e293b);
  color: var(--color-text, #e2e8f0);
}

.picks-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.25rem;
}

.empty-msg { font-size: 0.82rem; color: var(--color-text-muted, #94a3b8); padding: 0.25rem 0; }

.pick-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.4rem;
  background: var(--color-surface-alt, #1e293b);
  border-radius: 0.3rem;
  flex-shrink: 0;
}
.round-label { font-size: 0.62rem; color: var(--color-text-muted, #94a3b8); min-width: 1.5rem; flex-shrink: 0; }

/* Position view */
.pos-section-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.2rem 0.4rem;
  border-left: 3px solid transparent;
  margin-top: 0.15rem;
  flex-shrink: 0;
}
.pos-section-badge {
  display: inline-block;
  padding: 0.05rem 0.35rem;
  border-radius: 0.2rem;
  font-size: 0.65rem;
  font-weight: 700;
  color: #fff;
}
.pick-indented { margin-left: 0.5rem; }

/* Starters view */
.starter-row { gap: 0.4rem; }
.slot-badge {
  display: inline-block;
  padding: 0.05rem 0.3rem;
  border-radius: 0.2rem;
  font-size: 0.6rem;
  font-weight: 700;
  color: #fff;
  min-width: 2.4rem;
  text-align: center;
  flex-shrink: 0;
}
.empty-slot {
  font-size: 0.75rem;
  color: var(--color-text-muted, #94a3b8);
}
.bench-header {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  color: var(--color-text-muted, #94a3b8);
  padding: 0.25rem 0.4rem 0.1rem;
  flex-shrink: 0;
  margin-top: 0.2rem;
}
.bench-row :deep(.player-name) { color: #fff; }
.bench-row :deep(.player-meta) { color: rgba(255, 255, 255, 0.8); }
</style>
