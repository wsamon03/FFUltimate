<template>
  <div class="avail-panel">
    <!-- Position tabs + search -->
    <div class="toolbar">
      <div class="pos-tabs">
        <button
          v-for="pos in POSITIONS"
          :key="pos"
          class="pos-tab"
          :class="{ active: activePosition === pos }"
          @click="setPosition(pos)"
        >{{ pos }}</button>
      </div>
      <input
        v-model="searchText"
        class="search-input"
        type="text"
        placeholder="Search players…"
      />
    </div>

    <!-- Stats table -->
    <div class="table-wrap">
      <div v-if="loading" class="state-msg">Loading…</div>
      <div v-else-if="!pagedPlayers.length" class="state-msg">No players found.</div>

      <table v-else class="stats-table">
        <thead>
          <tr>
            <th class="col-actions col-sticky-actions"></th>
            <th
              v-for="col in columns"
              :key="col.key"
              class="col-header"
              :class="[
                `align-${col.align ?? 'left'}`,
                { 'sort-active': sortColumn === col.key },
                col.key === 'name' ? 'col-sticky-name' : '',
              ]"
              @click="setSortColumn(col.key)"
            >
              {{ col.label }}
              <span v-if="sortColumn === col.key" class="sort-arrow">
                {{ sortDir === 'asc' ? '↑' : '↓' }}
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="player in pagedPlayers"
            :key="player.player_id"
            class="player-row"
          >
            <td class="col-actions col-sticky-actions">
              <button
                class="btn-queue"
                title="Add to queue"
                @click="emit('queue', player)"
              >+</button>
              <button
                class="btn-pick"
                :disabled="!canPick"
                @click="emit('pick', player)"
              >Draft</button>
            </td>
            <td class="col-name col-sticky-name">
              <span class="pos-badge" :style="{ background: posColor(player.position_code) }">
                {{ player.position_code ?? '?' }}
              </span>
              <span class="player-name">{{ player.name }}</span>
            </td>
            <td class="align-center">{{ player.team_abbr ?? '—' }}</td>
            <td
              v-for="col in statColumns"
              :key="col.key"
              :class="`align-${col.align ?? 'right'}`"
            >
              {{ formatStat(player[col.key]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AppPagination
      v-if="!loading && sortedPlayers.length > 0"
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
import { getAvailablePlayers } from '@/api/leagues'
import { getPlayerSeasonStats } from '@/api/stats'
import AppPagination from '@/components/ui/AppPagination.vue'

const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DST']

const POS_COLORS: Record<string, string> = {
  QB: '#ef4444', RB: '#22c55e', WR: '#3b82f6', TE: '#f59e0b',
  K: '#8b5cf6', DST: '#06b6d4', DEF: '#06b6d4',
}

interface Column {
  label: string
  key: string
  align?: 'left' | 'right' | 'center'
}

const STAT_COLUMNS: Record<string, Column[]> = {
  ALL:  [
    { label: 'Pass Yds', key: 'pass_yds', align: 'right' },
    { label: 'Rush Yds', key: 'rush_yds', align: 'right' },
    { label: 'Rec Yds',  key: 'rec_yds',  align: 'right' },
    { label: 'Rec TD',   key: 'rec_td',   align: 'right' },
  ],
  QB:   [
    { label: 'Comp',     key: 'pass_comp',   align: 'right' },
    { label: 'Att',      key: 'pass_att',    align: 'right' },
    { label: 'Yds',      key: 'pass_yds',    align: 'right' },
    { label: 'TD',       key: 'pass_td',     align: 'right' },
    { label: 'INT',      key: 'pass_int',    align: 'right' },
    { label: 'Rush Yds', key: 'rush_yds',    align: 'right' },
  ],
  RB:   [
    { label: 'Car',      key: 'rush_att',    align: 'right' },
    { label: 'Rush Yds', key: 'rush_yds',    align: 'right' },
    { label: 'Rush TD',  key: 'rush_td',     align: 'right' },
    { label: 'Rec',      key: 'rec_receptions', align: 'right' },
    { label: 'Rec Yds',  key: 'rec_yds',     align: 'right' },
    { label: 'Rec TD',   key: 'rec_td',      align: 'right' },
  ],
  WR:   [
    { label: 'Rec',      key: 'rec_receptions', align: 'right' },
    { label: 'Tgt',      key: 'rec_targets', align: 'right' },
    { label: 'Rec Yds',  key: 'rec_yds',     align: 'right' },
    { label: 'Rec TD',   key: 'rec_td',      align: 'right' },
    { label: 'Rush Yds', key: 'rush_yds',    align: 'right' },
  ],
  TE:   [
    { label: 'Rec',      key: 'rec_receptions', align: 'right' },
    { label: 'Tgt',      key: 'rec_targets', align: 'right' },
    { label: 'Rec Yds',  key: 'rec_yds',     align: 'right' },
    { label: 'Rec TD',   key: 'rec_td',      align: 'right' },
  ],
  K:    [
    { label: 'FGM',      key: 'k_fg_make',   align: 'right' },
    { label: 'FGA',      key: 'k_fg_att',    align: 'right' },
    { label: 'FG Long',  key: 'k_fg_long',   align: 'right' },
    { label: 'XPM',      key: 'k_xp_make',   align: 'right' },
  ],
  DST:  [
    { label: 'Solo',     key: 'def_solo',    align: 'right' },
    { label: 'Ast',      key: 'def_ast',     align: 'right' },
    { label: 'Sacks',    key: 'def_sacks',   align: 'right' },
    { label: 'INT',      key: 'def_int',     align: 'right' },
    { label: 'TD',       key: 'def_td',      align: 'right' },
  ],
}

const props = defineProps<{
  leagueId: string
  draftYear: number
  draftedIds: Set<string>
  canPick: boolean
}>()

const emit = defineEmits<{
  (e: 'pick', player: any): void
  (e: 'queue', player: any): void
}>()

const players = ref<any[]>([])
const loading = ref(false)
const activePosition = ref('ALL')
const searchText = ref('')
const sortColumn = ref<string>('name')
const sortDir = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)
const perPage = ref(20)
let _debounceTimer: ReturnType<typeof setTimeout> | null = null

const statColumns = computed(() => STAT_COLUMNS[activePosition.value] ?? STAT_COLUMNS.ALL)

const columns = computed<Column[]>(() => [
  { label: 'Player', key: 'name', align: 'left' },
  { label: 'Team',   key: 'team_abbr', align: 'center' },
  ...statColumns.value,
])

const filteredPlayers = computed(() => {
  let list = players.value.filter(p => !props.draftedIds.has(p.player_id))
  if (activePosition.value !== 'ALL') {
    list = list.filter(p => p.position_code === activePosition.value)
  }
  const q = searchText.value.trim().toLowerCase()
  if (q) {
    list = list.filter(p => (p.name ?? '').toLowerCase().includes(q))
  }
  return list
})

const sortedPlayers = computed(() => {
  const list = [...filteredPlayers.value]
  const col = sortColumn.value
  list.sort((a, b) => {
    const av = a[col], bv = b[col]
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (typeof av === 'number' && typeof bv === 'number')
      return sortDir.value === 'asc' ? av - bv : bv - av
    return sortDir.value === 'asc'
      ? String(av).toLowerCase().localeCompare(String(bv).toLowerCase())
      : String(bv).toLowerCase().localeCompare(String(av).toLowerCase())
  })
  return list
})

const pagedPlayers = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  return sortedPlayers.value.slice(start, start + perPage.value)
})

function setSortColumn(key: string) {
  if (sortColumn.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = key
    sortDir.value = key === 'name' || key === 'team_abbr' ? 'asc' : 'desc'
  }
  currentPage.value = 1
}

function setPosition(pos: string) {
  activePosition.value = pos
  currentPage.value = 1
  sortColumn.value = 'name'
  sortDir.value = 'asc'
}

function posColor(pos?: string | null): string {
  return POS_COLORS[pos ?? ''] ?? '#64748b'
}

function formatStat(val: any): string {
  if (val == null) return '—'
  if (typeof val === 'number') return val === 0 ? '0' : val.toLocaleString()
  return String(val)
}

async function load() {
  loading.value = true
  try {
    const [availList, statsRows] = await Promise.all([
      getAvailablePlayers(props.leagueId, props.draftYear, { limit: 2000, offset: 0 }),
      getPlayerSeasonStats(props.draftYear - 1).catch(() => []),
    ])
    const statsMap = new Map<string, any>()
    for (const row of statsRows) {
      if (row.player_id) statsMap.set(row.player_id, row)
    }
    players.value = availList.map((p: any) => ({
      ...p,
      ...(statsMap.get(p.player_id) ?? {}),
    }))
  } finally {
    loading.value = false
  }
}

watch(searchText, () => {
  if (_debounceTimer) clearTimeout(_debounceTimer)
  _debounceTimer = setTimeout(() => { currentPage.value = 1 }, 300)
})

watch(() => props.draftedIds.size, () => load())

onMounted(() => load())
</script>

<style scoped>
.avail-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.5rem;
  flex-shrink: 0;
  flex-wrap: wrap;
  border-bottom: 1px solid var(--color-border, #334155);
}
.pos-tabs { display: flex; gap: 0.2rem; flex-wrap: wrap; }
.pos-tab {
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid var(--color-border, #334155);
  background: var(--color-surface-alt, #1e293b);
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  font-size: 0.73rem;
  font-weight: 600;
  transition: background 0.12s;
}
.pos-tab.active,
.pos-tab:hover {
  background: var(--color-primary, #6366f1);
  border-color: var(--color-primary, #6366f1);
  color: #fff;
}
.search-input {
  margin-left: auto;
  width: 160px;
  padding: 0.3rem 0.5rem;
  background: var(--color-surface-alt, #1e293b);
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.3rem;
  color: var(--color-text, #e2e8f0);
  font-size: 0.82rem;
  outline: none;
}
.search-input:focus { border-color: var(--color-primary, #6366f1); }
.table-wrap {
  flex: 1;
  overflow: auto;
  position: relative;
}
.state-msg {
  padding: 1rem;
  color: var(--color-text-muted, #94a3b8);
  font-size: 0.85rem;
}
.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
.stats-table thead {
  position: sticky;
  top: 0;
  background: var(--color-surface, #0f172a);
  z-index: 1;
}
.col-header {
  padding: 0.4rem 0.5rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, #94a3b8);
  border-bottom: 1px solid var(--color-border, #334155);
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
}
.col-header:hover { color: var(--color-text, #e2e8f0); }
.col-header.sort-active { color: var(--color-primary, #6366f1); }
.sort-arrow { margin-left: 0.2rem; font-size: 0.65rem; }
.col-actions {
  padding: 0.2rem 0.4rem;
  white-space: nowrap;
  border-bottom: 1px solid var(--color-border, #334155);
}
/* Frozen columns — stick to left edge on horizontal scroll */
.col-sticky-actions {
  position: sticky;
  left: 0;
  z-index: 2;
  width: 100px;
  min-width: 100px;
  background: var(--color-surface, #0f172a);
}
.col-sticky-name {
  position: sticky;
  left: 100px;
  z-index: 2;
  background: var(--color-surface, #0f172a);
}
/* In thead, raise z-index so frozen headers sit above frozen body cells */
thead .col-sticky-actions,
thead .col-sticky-name {
  z-index: 3;
}
/* Body frozen cells use table-row background; sync with row hover */
tbody .col-sticky-actions,
tbody .col-sticky-name {
  background: var(--color-bg, #0a0f1e);
}
tbody .player-row:hover .col-sticky-actions,
tbody .player-row:hover .col-sticky-name {
  background: var(--color-surface-alt, #1e293b);
}
.align-left  { text-align: left; }
.align-right { text-align: right; }
.align-center { text-align: center; }
.player-row {
  border-bottom: 1px solid var(--color-border, #334155);
  transition: background 0.1s;
}
.player-row:hover { background: var(--color-surface-alt, #1e293b); }
.stats-table td {
  padding: 0.35rem 0.5rem;
  color: var(--color-text, #e2e8f0);
  white-space: nowrap;
}
.col-name {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 140px;
}
.pos-badge {
  display: inline-block;
  padding: 0.05rem 0.3rem;
  border-radius: 0.2rem;
  font-size: 0.65rem;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.player-name {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}
.btn-queue {
  padding: 0.15rem 0.4rem;
  border-radius: 0.2rem;
  border: 1px solid var(--color-border, #334155);
  background: transparent;
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  font-size: 0.8rem;
  margin-right: 0.25rem;
}
.btn-queue:hover { background: var(--color-surface, #0f172a); }
.btn-pick {
  padding: 0.15rem 0.45rem;
  border-radius: 0.2rem;
  background: var(--color-primary, #6366f1);
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
}
.btn-pick:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
