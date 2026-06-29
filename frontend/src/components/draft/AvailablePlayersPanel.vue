<template>
  <div class="avail-panel">
    <!-- Toolbar: position tabs + search -->
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

    <!-- Stat type toggle -->
    <div class="stat-type-bar">
      <button
        v-for="st in STAT_TYPES"
        :key="st.value"
        class="stat-type-btn"
        :class="{ active: statType === st.value }"
        @click="statType = st.value"
      >{{ st.label }}</button>
    </div>

    <!-- Stats table -->
    <div class="table-wrap">
      <div v-if="loading" class="state-msg">Loading…</div>
      <div v-else-if="!pagedPlayers.length" class="state-msg">No players found.</div>

      <table v-else class="stats-table">
        <thead>
          <!-- Group header row -->
          <tr class="group-row">
            <th rowspan="2" class="col-sticky-actions th-actions"></th>
            <th rowspan="2" class="col-sticky-name th-player">Player</th>
            <th rowspan="2" class="th-team">Team</th>
            <th
              v-for="group in activeGroups"
              :key="group.label"
              :colspan="group.columns.length"
              class="group-label"
              :class="`group-${group.color}`"
            >{{ group.label }}</th>
          </tr>
          <!-- Column header row -->
          <tr class="col-row">
            <th
              v-for="col in flatStatColumns"
              :key="col.key"
              class="col-header align-right"
              :class="[
                `col-${col.color}`,
                { 'col-divider': col.isFirst, 'sort-active': sortColumn === col.key },
              ]"
              :title="col.title"
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
              <button class="btn-queue" title="Add to queue" @click="emit('queue', player)">+</button>
              <button class="btn-pick" :disabled="!canPick" @click="emit('pick', player)">Draft</button>
            </td>
            <td class="col-name col-sticky-name">
              <span class="pos-badge" :style="{ background: posColor(player.position_code) }">
                {{ player.position_code ?? '?' }}
              </span>
              <button class="player-name-btn" @click="cardPlayerId = player.player_id">{{ player.name }}</button>
            </td>
            <td class="align-center td-team">{{ player.team_abbr ?? '—' }}</td>
            <td
              v-for="col in flatStatColumns"
              :key="col.key"
              :class="[`align-right`, `col-${col.color}`, { 'col-divider': col.isFirst }]"
            >{{ formatStat(player[col.key], col.key) }}</td>
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

  <PlayerCardModal
    :visible="cardPlayerId !== null"
    :player-id="cardPlayerId"
    @close="cardPlayerId = null"
  />
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { getAvailablePlayers } from '@/api/leagues'
import { getPlayerSeasonStats } from '@/api/stats'
import AppPagination from '@/components/ui/AppPagination.vue'
import PlayerCardModal from './PlayerCardModal.vue'

const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DST']

const STAT_TYPES = [
  { value: 'offense',  label: 'Offense' },
  { value: 'defense',  label: 'Defense' },
  { value: 'special',  label: 'Special Teams' },
]

const POS_COLORS: Record<string, string> = {
  QB: '#ef4444', RB: '#22c55e', WR: '#3b82f6', TE: '#f59e0b',
  K: '#8b5cf6', DST: '#06b6d4', DEF: '#06b6d4',
}

// Auto stat-type per position
const POS_DEFAULT_STAT: Record<string, string> = {
  K: 'special', DST: 'defense', DEF: 'defense',
}

interface StatCol {
  label: string
  key: string
  title: string
  color: string
  isFirst: boolean
}

interface StatGroup {
  label: string
  color: string
  columns: Omit<StatCol, 'color' | 'isFirst'>[]
}

const STAT_GROUPS: Record<string, StatGroup[]> = {
  offense: [
    {
      label: 'PASSING', color: 'pass',
      columns: [
        { label: 'CMP',  key: 'pass_comp',   title: 'Completions' },
        { label: 'ATT',  key: 'pass_att',    title: 'Pass Attempts' },
        { label: 'YDS',  key: 'pass_yds',    title: 'Pass Yards' },
        { label: 'TD',   key: 'pass_td',     title: 'Passing TDs' },
        { label: 'INT',  key: 'pass_int',    title: 'Interceptions Thrown' },
        { label: 'QBR',  key: 'pass_qbr',   title: 'QBR' },
        { label: 'RTG',  key: 'pass_rating', title: 'Passer Rating' },
      ],
    },
    {
      label: 'RUSHING', color: 'rush',
      columns: [
        { label: 'ATT',  key: 'rush_att',  title: 'Rush Attempts' },
        { label: 'YDS',  key: 'rush_yds',  title: 'Rush Yards' },
        { label: 'TD',   key: 'rush_td',   title: 'Rush TDs' },
        { label: 'LONG', key: 'rush_long', title: 'Longest Rush' },
      ],
    },
    {
      label: 'RECEIVING', color: 'rec',
      columns: [
        { label: 'REC',  key: 'rec_receptions', title: 'Receptions' },
        { label: 'TGT',  key: 'rec_targets',    title: 'Targets' },
        { label: 'YDS',  key: 'rec_yds',        title: 'Receiving Yards' },
        { label: 'TD',   key: 'rec_td',         title: 'Receiving TDs' },
        { label: 'LONG', key: 'rec_long',        title: 'Longest Reception' },
      ],
    },
    {
      label: 'FUMBLES', color: 'fum',
      columns: [
        { label: 'FUM',  key: 'fum_total', title: 'Fumbles' },
        { label: 'LOST', key: 'fum_lost',  title: 'Fumbles Lost' },
      ],
    },
  ],
  defense: [
    {
      label: 'TACKLES', color: 'tkl',
      columns: [
        { label: 'SOLO',  key: 'def_solo',  title: 'Solo Tackles' },
        { label: 'AST',   key: 'def_ast',   title: 'Assisted Tackles' },
        { label: 'SACKS', key: 'def_sacks', title: 'Sacks' },
        { label: 'TFL',   key: 'def_tfl',   title: 'Tackles for Loss' },
      ],
    },
    {
      label: 'PASS RUSH', color: 'cov',
      columns: [
        { label: 'PD',     key: 'def_pd',      title: 'Passes Defensed' },
        { label: 'QB HIT', key: 'def_qb_hits', title: 'QB Hits' },
      ],
    },
    {
      label: 'COVERAGE', color: 'to',
      columns: [
        { label: 'INT',     key: 'def_int',     title: 'Interceptions' },
        { label: 'INT YDS', key: 'def_int_yds', title: 'INT Return Yards' },
        { label: 'DEF TD',  key: 'def_td',      title: 'Defensive TDs' },
      ],
    },
  ],
  special: [
    {
      label: 'KICKING', color: 'kick',
      columns: [
        { label: 'FGM',     key: 'k_fg_make', title: 'Field Goals Made' },
        { label: 'FGA',     key: 'k_fg_att',  title: 'Field Goal Attempts' },
        { label: 'FG LONG', key: 'k_fg_long', title: 'Longest Field Goal' },
        { label: 'XPM',     key: 'k_xp_make', title: 'Extra Points Made' },
        { label: 'XPA',     key: 'k_xp_att',  title: 'Extra Point Attempts' },
      ],
    },
    {
      label: 'PUNTING', color: 'punt',
      columns: [
        { label: 'PUNTS', key: 'p_no',   title: 'Punts' },
        { label: 'P YDS', key: 'p_yds',  title: 'Punt Yards' },
        { label: 'IN20',  key: 'p_in20', title: 'Inside 20' },
        { label: 'TB',    key: 'p_tb',   title: 'Touchbacks' },
        { label: 'BLK',   key: 'p_blk',  title: 'Blocked Punts' },
        { label: 'LONG',  key: 'p_long', title: 'Longest Punt' },
      ],
    },
    {
      label: 'RETURNS', color: 'ret',
      columns: [
        { label: 'KR',      key: 'ret_kick_no',   title: 'Kick Returns' },
        { label: 'KR YDS',  key: 'ret_kick_yds',  title: 'Kick Return Yards' },
        { label: 'KR TD',   key: 'ret_kick_td',   title: 'Kick Return TDs' },
        { label: 'KR LONG', key: 'ret_kick_long',  title: 'Longest KR' },
        { label: 'PR',      key: 'ret_punt_no',   title: 'Punt Returns' },
        { label: 'PR YDS',  key: 'ret_punt_yds',  title: 'Punt Return Yards' },
        { label: 'PR TD',   key: 'ret_punt_td',   title: 'Punt Return TDs' },
        { label: 'PR LONG', key: 'ret_punt_long',  title: 'Longest PR' },
      ],
    },
  ],
}

const DECIMAL_KEYS = new Set(['pass_qbr', 'pass_rating'])

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
const statType = ref('offense')
const cardPlayerId = ref<string | null>(null)
const searchText = ref('')
const sortColumn = ref<string>('name')
const sortDir = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)
const perPage = ref(20)
let _debounceTimer: ReturnType<typeof setTimeout> | null = null

const activeGroups = computed(() => STAT_GROUPS[statType.value] ?? STAT_GROUPS.offense)

const flatStatColumns = computed<StatCol[]>(() =>
  activeGroups.value.flatMap(group =>
    group.columns.map((col, ci) => ({
      ...col,
      color: group.color,
      isFirst: ci === 0,
    }))
  )
)

const filteredPlayers = computed(() => {
  let list = players.value.filter(p => !props.draftedIds.has(p.player_id))
  if (activePosition.value !== 'ALL') {
    list = list.filter(p => p.position_code === activePosition.value)
  }
  const q = searchText.value.trim().toLowerCase()
  if (q) list = list.filter(p => (p.name ?? '').toLowerCase().includes(q))
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
    sortDir.value = (key === 'name' || key === 'team_abbr') ? 'asc' : 'desc'
  }
  currentPage.value = 1
}

function setPosition(pos: string) {
  activePosition.value = pos
  currentPage.value = 1
  sortColumn.value = 'name'
  sortDir.value = 'asc'
  // Auto-switch stat type to match the position's primary stat group
  const defaultStat = POS_DEFAULT_STAT[pos]
  if (defaultStat) statType.value = defaultStat
  else if (statType.value !== 'offense') statType.value = 'offense'
}

function posColor(pos?: string | null): string {
  return POS_COLORS[pos ?? ''] ?? '#64748b'
}

function formatStat(val: any, key: string): string {
  if (val == null) return '—'
  if (typeof val === 'number') {
    if (val === 0) return '0'
    if (DECIMAL_KEYS.has(key)) return val.toFixed(1)
    return val.toLocaleString()
  }
  return String(val)
}

// Reset sort to name when stat type changes (old sort key may not exist in new group)
watch(statType, () => {
  sortColumn.value = 'name'
  sortDir.value = 'asc'
  currentPage.value = 1
})

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

/* Toolbars */
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

.stat-type-bar {
  display: flex;
  gap: 0;
  padding: 0.3rem 0.5rem;
  flex-shrink: 0;
  border-bottom: 1px solid var(--color-border, #334155);
}
.stat-type-btn {
  padding: 0.2rem 0.75rem;
  border: 1px solid var(--color-border, #334155);
  background: var(--color-surface-alt, #1e293b);
  color: var(--color-text-muted, #94a3b8);
  cursor: pointer;
  font-size: 0.72rem;
  font-weight: 600;
  transition: background 0.12s;
}
.stat-type-btn:first-child { border-radius: 0.25rem 0 0 0.25rem; }
.stat-type-btn:last-child  { border-radius: 0 0.25rem 0.25rem 0; margin-left: -1px; }
.stat-type-btn:not(:first-child):not(:last-child) { margin-left: -1px; }
.stat-type-btn.active {
  background: var(--color-primary, #6366f1);
  border-color: var(--color-primary, #6366f1);
  color: #fff;
  z-index: 1;
}
.stat-type-btn:hover:not(.active) { color: var(--color-text, #e2e8f0); }

/* Table */
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
  z-index: 4;
}

/* Group header row */
.group-label {
  text-align: center;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 0.25rem 0.4rem;
  border-bottom: 1px solid var(--color-border, #334155);
  white-space: nowrap;
}
.group-pass { background: color-mix(in srgb, #3b82f6 18%, var(--color-surface, #0f172a)); color: #93c5fd; }
.group-rush { background: color-mix(in srgb, #22c55e 18%, var(--color-surface, #0f172a)); color: #86efac; }
.group-rec  { background: color-mix(in srgb, #06b6d4 18%, var(--color-surface, #0f172a)); color: #67e8f9; }
.group-fum  { background: color-mix(in srgb, #ef4444 18%, var(--color-surface, #0f172a)); color: #fca5a5; }
.group-tkl  { background: color-mix(in srgb, #f59e0b 18%, var(--color-surface, #0f172a)); color: #fcd34d; }
.group-cov  { background: color-mix(in srgb, #8b5cf6 18%, var(--color-surface, #0f172a)); color: #c4b5fd; }
.group-to   { background: color-mix(in srgb, #06b6d4 18%, var(--color-surface, #0f172a)); color: #67e8f9; }
.group-kick { background: color-mix(in srgb, #6366f1 18%, var(--color-surface, #0f172a)); color: #a5b4fc; }
.group-punt { background: color-mix(in srgb, #64748b 18%, var(--color-surface, #0f172a)); color: #cbd5e1; }
.group-ret  { background: color-mix(in srgb, #f97316 18%, var(--color-surface, #0f172a)); color: #fdba74; }

/* Fixed header cells that span both header rows */
.th-actions {
  background: var(--color-surface, #0f172a);
  border-bottom: 1px solid var(--color-border, #334155);
  z-index: 5;
}
.th-player {
  background: var(--color-surface, #0f172a);
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, #94a3b8);
  padding: 0.4rem 0.5rem;
  border-bottom: 1px solid var(--color-border, #334155);
  z-index: 5;
}
.th-team {
  background: var(--color-surface, #0f172a);
  text-align: center;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, #94a3b8);
  padding: 0.4rem 0.5rem;
  border-bottom: 1px solid var(--color-border, #334155);
  white-space: nowrap;
}

/* Stat column headers */
.col-header {
  padding: 0.35rem 0.5rem;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, #94a3b8);
  border-bottom: 1px solid var(--color-border, #334155);
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
  background: var(--color-surface, #0f172a);
}
.col-header:hover { color: var(--color-text, #e2e8f0); }
.col-header.sort-active { color: var(--color-primary, #6366f1); }
.sort-arrow { margin-left: 0.2rem; font-size: 0.65rem; }

/* Column color accents */
.col-pass { color: #93c5fd; }
.col-rush { color: #86efac; }
.col-rec  { color: #67e8f9; }
.col-fum  { color: #fca5a5; }
.col-tkl  { color: #fcd34d; }
.col-cov  { color: #c4b5fd; }
.col-to   { color: #67e8f9; }
.col-kick { color: #a5b4fc; }
.col-punt { color: #cbd5e1; }
.col-ret  { color: #fdba74; }

/* Data cells override color for readability */
tbody .col-pass,
tbody .col-rush,
tbody .col-rec,
tbody .col-fum,
tbody .col-tkl,
tbody .col-cov,
tbody .col-to,
tbody .col-kick,
tbody .col-punt,
tbody .col-ret { color: var(--color-text, #e2e8f0); }

/* Group divider lines */
.col-divider { border-left: 1px solid var(--color-border, #334155); }

/* Frozen columns */
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
thead .col-sticky-actions,
thead .col-sticky-name { z-index: 5; }
tbody .col-sticky-actions,
tbody .col-sticky-name { background: var(--color-bg, #0a0f1e); }
tbody .player-row:hover .col-sticky-actions,
tbody .player-row:hover .col-sticky-name { background: var(--color-surface-alt, #1e293b); }

/* Actions column */
.col-actions {
  padding: 0.2rem 0.4rem;
  white-space: nowrap;
  border-bottom: 1px solid var(--color-border, #334155);
}

/* Alignment helpers */
.align-left   { text-align: left; }
.align-right  { text-align: right; }
.align-center { text-align: center; }

/* Player rows */
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
.td-team { text-align: center; }
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
.player-name-btn {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
  background: none;
  border: none;
  padding: 0;
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  font-size: inherit;
  text-align: left;
}
.player-name-btn:hover {
  color: var(--color-primary, #6366f1);
  text-decoration: underline;
}

/* Action buttons */
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
