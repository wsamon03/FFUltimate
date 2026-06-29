<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="player-card-overlay"
      :style="{ left: pos.x + 'px', top: pos.y + 'px' }"
    >
      <!-- Draggable header -->
      <div class="card-header" @mousedown="startDrag">
        <div class="card-player-info">
          <span class="card-pos-badge" :style="{ background: posColor(player?.position) }">
            {{ player?.position || '?' }}
          </span>
          <span class="card-name">{{ player?.full_name || player?.name || '…' }}</span>
          <span class="card-team">{{ player?.team_code || player?.team || 'Free Agent' }}</span>
        </div>
        <button class="card-close" @mousedown.stop @click="emit('close')">✕</button>
      </div>

      <!-- Controls -->
      <div class="card-controls">
        <div class="view-mode-btns">
          <button
            v-for="m in VIEW_MODES"
            :key="m.value"
            class="view-btn"
            :class="{ active: viewMode === m.value }"
            @click="viewMode = m.value as 'career' | 'season' | 'range'"
          >{{ m.label }}</button>
        </div>
        <div class="stat-type-btns">
          <button
            v-for="st in STAT_TYPES"
            :key="st.value"
            class="stat-btn"
            :class="{ active: statType === st.value }"
            @click="statType = st.value"
          >{{ st.label }}</button>
        </div>
      </div>

      <!-- Season selector -->
      <div v-if="viewMode === 'season'" class="card-time-bar">
        <label class="bar-label">Season</label>
        <select v-model.number="selectedSeason" class="bar-select">
          <option v-for="yr in availableSeasons" :key="yr" :value="yr">{{ yr }}</option>
        </select>
      </div>

      <!-- Range controls -->
      <div v-else-if="viewMode === 'range'" class="card-time-bar">
        <label class="bar-label">From</label>
        <input v-model.number="rangeStartYear" type="number" min="2000" :max="currentYear" class="bar-year" />
        <label class="bar-label">Wk</label>
        <input v-model.number="rangeStartWeek" type="number" min="1" max="22" class="bar-week" />
        <label class="bar-label">To</label>
        <input v-model.number="rangeEndYear" type="number" min="2000" :max="currentYear" class="bar-year" />
        <label class="bar-label">Wk</label>
        <input v-model.number="rangeEndWeek" type="number" min="1" max="22" class="bar-week" />
      </div>

      <!-- Stats table -->
      <div class="card-table-wrap">
        <div v-if="loading" class="card-state">Loading…</div>
        <div v-else-if="!displayStats.length" class="card-state">No stats available.</div>
        <table v-else class="card-stats-table">
          <thead>
            <!-- Group header row -->
            <tr>
              <th :colspan="leadingColCount" class="col-anchor"></th>
              <template v-if="statType === 'offense'">
                <th colspan="7" class="col-group-label group-pass">PASSING</th>
                <th colspan="4" class="col-group-label group-rush">RUSHING</th>
                <th colspan="5" class="col-group-label group-rec">RECEIVING</th>
                <th colspan="2" class="col-group-label group-fum">FUMBLES</th>
              </template>
              <template v-else-if="statType === 'defense'">
                <th colspan="4" class="col-group-label group-tkl">TACKLES</th>
                <th colspan="2" class="col-group-label group-cov">PASS RUSH</th>
                <th colspan="3" class="col-group-label group-to">COVERAGE</th>
              </template>
              <template v-else>
                <th colspan="5" class="col-group-label group-kick">KICKING</th>
                <th colspan="6" class="col-group-label group-punt">PUNTING</th>
                <th colspan="8" class="col-group-label group-ret">RETURNS</th>
              </template>
            </tr>
            <!-- Column header row -->
            <tr>
              <!-- Career -->
              <template v-if="viewMode === 'career'">
                <th class="th-lead th-sortable" @click="sortBy('season_year')">Season {{ sortIcon('season_year') }}</th>
                <th class="th-lead">Teams</th>
              </template>
              <!-- Season -->
              <template v-else-if="viewMode === 'season'">
                <th class="th-lead th-sortable" @click="sortBy('week')">Wk {{ sortIcon('week') }}</th>
                <th class="th-lead">Team</th>
                <th class="th-lead">Opp</th>
              </template>
              <!-- Range -->
              <template v-else>
                <th class="th-lead th-sortable" @click="sortBy('season_year')">Season {{ sortIcon('season_year') }}</th>
                <th class="th-lead th-sortable" @click="sortBy('week')">Wk {{ sortIcon('week') }}</th>
                <th class="th-lead">Team</th>
                <th class="th-lead">Opp</th>
              </template>

              <!-- Offense stat headers -->
              <template v-if="statType === 'offense'">
                <th class="th-stat col-pass col-divider th-sortable" @click="sortBy('pass_comp')">Comp {{ sortIcon('pass_comp') }}</th>
                <th class="th-stat col-pass th-sortable" @click="sortBy('pass_att')">Att {{ sortIcon('pass_att') }}</th>
                <th class="th-stat col-pass th-sortable" @click="sortBy('pass_yds')">Pass Yds {{ sortIcon('pass_yds') }}</th>
                <th class="th-stat col-pass th-sortable" @click="sortBy('pass_td')">Pass TD {{ sortIcon('pass_td') }}</th>
                <th class="th-stat col-pass th-sortable" @click="sortBy('pass_int')">INT {{ sortIcon('pass_int') }}</th>
                <th class="th-stat col-pass th-sortable" @click="sortBy('pass_qbr')">QBR {{ sortIcon('pass_qbr') }}</th>
                <th class="th-stat col-pass th-sortable" @click="sortBy('pass_rating')">RTG {{ sortIcon('pass_rating') }}</th>
                <th class="th-stat col-rush col-divider th-sortable" @click="sortBy('rush_att')">Rush Att {{ sortIcon('rush_att') }}</th>
                <th class="th-stat col-rush th-sortable" @click="sortBy('rush_yds')">Rush Yds {{ sortIcon('rush_yds') }}</th>
                <th class="th-stat col-rush th-sortable" @click="sortBy('rush_td')">Rush TD {{ sortIcon('rush_td') }}</th>
                <th class="th-stat col-rush th-sortable" @click="sortBy('rush_long')">R.Long {{ sortIcon('rush_long') }}</th>
                <th class="th-stat col-rec col-divider th-sortable" @click="sortBy('rec_receptions')">Rec {{ sortIcon('rec_receptions') }}</th>
                <th class="th-stat col-rec th-sortable" @click="sortBy('rec_targets')">Tgts {{ sortIcon('rec_targets') }}</th>
                <th class="th-stat col-rec th-sortable" @click="sortBy('rec_yds')">Rec Yds {{ sortIcon('rec_yds') }}</th>
                <th class="th-stat col-rec th-sortable" @click="sortBy('rec_td')">Rec TD {{ sortIcon('rec_td') }}</th>
                <th class="th-stat col-rec th-sortable" @click="sortBy('rec_long')">Rec Long {{ sortIcon('rec_long') }}</th>
                <th class="th-stat col-fum col-divider th-sortable" @click="sortBy('fum_total')">Fum {{ sortIcon('fum_total') }}</th>
                <th class="th-stat col-fum th-sortable" @click="sortBy('fum_lost')">Lost {{ sortIcon('fum_lost') }}</th>
              </template>

              <!-- Defense stat headers -->
              <template v-else-if="statType === 'defense'">
                <th class="th-stat col-tkl col-divider th-sortable" @click="sortBy('def_solo')">Solo {{ sortIcon('def_solo') }}</th>
                <th class="th-stat col-tkl th-sortable" @click="sortBy('def_ast')">Ast {{ sortIcon('def_ast') }}</th>
                <th class="th-stat col-tkl th-sortable" @click="sortBy('def_sacks')">Sacks {{ sortIcon('def_sacks') }}</th>
                <th class="th-stat col-tkl th-sortable" @click="sortBy('def_tfl')">TFL {{ sortIcon('def_tfl') }}</th>
                <th class="th-stat col-cov col-divider th-sortable" @click="sortBy('def_pd')">PD {{ sortIcon('def_pd') }}</th>
                <th class="th-stat col-cov th-sortable" @click="sortBy('def_qb_hits')">QB Hits {{ sortIcon('def_qb_hits') }}</th>
                <th class="th-stat col-to col-divider th-sortable" @click="sortBy('def_int')">INT {{ sortIcon('def_int') }}</th>
                <th class="th-stat col-to th-sortable" @click="sortBy('def_int_yds')">INT Yds {{ sortIcon('def_int_yds') }}</th>
                <th class="th-stat col-to th-sortable" @click="sortBy('def_td')">TD {{ sortIcon('def_td') }}</th>
              </template>

              <!-- Special teams stat headers -->
              <template v-else>
                <th class="th-stat col-kick col-divider th-sortable" @click="sortBy('k_fg_make')">FGM {{ sortIcon('k_fg_make') }}</th>
                <th class="th-stat col-kick th-sortable" @click="sortBy('k_fg_att')">FGA {{ sortIcon('k_fg_att') }}</th>
                <th class="th-stat col-kick th-sortable" @click="sortBy('k_fg_long')">FG Long {{ sortIcon('k_fg_long') }}</th>
                <th class="th-stat col-kick th-sortable" @click="sortBy('k_xp_make')">XPM {{ sortIcon('k_xp_make') }}</th>
                <th class="th-stat col-kick th-sortable" @click="sortBy('k_xp_att')">XPA {{ sortIcon('k_xp_att') }}</th>
                <th class="th-stat col-punt col-divider th-sortable" @click="sortBy('p_no')">Punts {{ sortIcon('p_no') }}</th>
                <th class="th-stat col-punt th-sortable" @click="sortBy('p_yds')">Yds {{ sortIcon('p_yds') }}</th>
                <th class="th-stat col-punt th-sortable" @click="sortBy('p_in20')">In 20 {{ sortIcon('p_in20') }}</th>
                <th class="th-stat col-punt th-sortable" @click="sortBy('p_tb')">TB {{ sortIcon('p_tb') }}</th>
                <th class="th-stat col-punt th-sortable" @click="sortBy('p_blk')">Blk {{ sortIcon('p_blk') }}</th>
                <th class="th-stat col-punt th-sortable" @click="sortBy('p_long')">P.Long {{ sortIcon('p_long') }}</th>
                <th class="th-stat col-ret col-divider th-sortable" @click="sortBy('ret_kick_no')">Kick Ret {{ sortIcon('ret_kick_no') }}</th>
                <th class="th-stat col-ret th-sortable" @click="sortBy('ret_kick_yds')">Kick Yds {{ sortIcon('ret_kick_yds') }}</th>
                <th class="th-stat col-ret th-sortable" @click="sortBy('ret_kick_td')">Kick TD {{ sortIcon('ret_kick_td') }}</th>
                <th class="th-stat col-ret th-sortable" @click="sortBy('ret_kick_long')">Kick Long {{ sortIcon('ret_kick_long') }}</th>
                <th class="th-stat col-ret th-sortable" @click="sortBy('ret_punt_no')">Punt Ret {{ sortIcon('ret_punt_no') }}</th>
                <th class="th-stat col-ret th-sortable" @click="sortBy('ret_punt_yds')">Punt Yds {{ sortIcon('ret_punt_yds') }}</th>
                <th class="th-stat col-ret th-sortable" @click="sortBy('ret_punt_td')">Punt TD {{ sortIcon('ret_punt_td') }}</th>
                <th class="th-stat col-ret th-sortable" @click="sortBy('ret_punt_long')">Punt Long {{ sortIcon('ret_punt_long') }}</th>
              </template>
            </tr>
          </thead>
          <tbody>
            <PlayerStatRow
              v-for="(row, i) in displayStats"
              :key="i"
              :row="row"
              :mode="viewMode"
              :stat-type="statType"
            />
            <PlayerStatRow
              v-if="totalRow"
              :row="totalRow"
              mode="total"
              :leading-cols="totalRowLeadingCols"
              :stat-type="statType"
            />
          </tbody>
        </table>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getPlayer } from '@/api/players'
import { getPlayerStats } from '@/api/stats'
import PlayerStatRow from '@/components/players/PlayerStatRow.vue'

const POS_COLORS: Record<string, string> = {
  QB: '#ef4444', RB: '#22c55e', WR: '#3b82f6', TE: '#f59e0b',
  K: '#8b5cf6', DST: '#06b6d4', DEF: '#06b6d4',
}

const VIEW_MODES = [
  { value: 'career', label: 'Career' },
  { value: 'season', label: 'Season' },
  { value: 'range',  label: 'Range' },
]

const STAT_TYPES = [
  { value: 'offense',  label: 'Offense' },
  { value: 'defense',  label: 'Defense' },
  { value: 'special',  label: 'Special Teams' },
]

// SUM stats (accumulated)
const STAT_KEYS = [
  'pass_comp', 'pass_att', 'pass_yds', 'pass_td', 'pass_int', 'pass_sacked',
  'rush_att', 'rush_yds', 'rush_td',
  'rec_receptions', 'rec_targets', 'rec_yds', 'rec_td',
  'fum_total', 'fum_lost', 'fum_rec',
  'def_solo', 'def_ast', 'def_sacks', 'def_tfl', 'def_pd', 'def_qb_hits', 'def_td', 'def_int', 'def_int_yds',
  'k_fg_make', 'k_fg_att', 'k_xp_make', 'k_xp_att',
  'p_no', 'p_yds', 'p_in20', 'p_tb', 'p_blk', 'p_long',
  'ret_kick_no', 'ret_kick_yds', 'ret_kick_td',
  'ret_punt_no', 'ret_punt_yds', 'ret_punt_td',
]

// MAX stats (best single-game value)
const STAT_MAX_KEYS = [
  'pass_qbr', 'pass_rating',
  'rush_long', 'rec_long',
  'ret_kick_long', 'ret_punt_long', 'k_fg_long',
]

const currentYear = new Date().getFullYear()

const props = defineProps<{
  visible: boolean
  playerId: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const player = ref<any>(null)
const allStats = ref<any[]>([])
const loading = ref(false)

const viewMode = ref<'career' | 'season' | 'range'>('career')
const statType = ref('offense')
const selectedSeason = ref(currentYear)
const rangeStartYear = ref(currentYear)
const rangeStartWeek = ref(1)
const rangeEndYear   = ref(currentYear)
const rangeEndWeek   = ref(18)
const sortKey = ref<string | null>(null)
const sortDir = ref<'asc' | 'desc'>('desc')

// Drag state
const pos = ref({ x: Math.max(20, (window.innerWidth - 960) / 2), y: Math.max(20, (window.innerHeight - 560) / 2) })
let dragging = false
let dragStartX = 0
let dragStartY = 0
let dragOriginX = 0
let dragOriginY = 0

function startDrag(e: MouseEvent) {
  dragging = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragOriginX = pos.value.x
  dragOriginY = pos.value.y
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
  e.preventDefault()
}

function onDrag(e: MouseEvent) {
  if (!dragging) return
  pos.value = {
    x: Math.max(0, dragOriginX + e.clientX - dragStartX),
    y: Math.max(0, dragOriginY + e.clientY - dragStartY),
  }
}

function stopDrag() {
  dragging = false
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}

function posColor(pos?: string | null): string {
  return POS_COLORS[pos ?? ''] ?? '#64748b'
}

// Reset and load when playerId changes while visible
watch(() => [props.visible, props.playerId] as const, async ([visible, id]) => {
  if (!visible || !id) return
  loading.value = true
  player.value = null
  allStats.value = []
  viewMode.value = 'career'
  sortKey.value = null
  // Reset position to center when opening a new player
  pos.value = { x: Math.max(20, (window.innerWidth - 960) / 2), y: Math.max(20, (window.innerHeight - 560) / 2) }
  try {
    const [p, stats] = await Promise.all([getPlayer(id), getPlayerStats(id)])
    player.value = p
    allStats.value = stats
    if (stats.length > 0) {
      const years = [...new Set(stats.map((r: any) => r.season_year as number))].filter(Boolean) as number[]
      if (years.length) {
        selectedSeason.value = Math.max(...years)
        rangeStartYear.value = Math.min(...years)
        rangeEndYear.value   = Math.max(...years)
      }
    }
  } finally {
    loading.value = false
  }
}, { immediate: true })

watch(viewMode, () => { sortKey.value = null })

const availableSeasons = computed(() => {
  const years = new Set(allStats.value.map((r: any) => r.season_year as number).filter(Boolean))
  return Array.from(years).sort((a, b) => b - a)
})

const careerStats = computed(() => {
  const byYear = new Map<number, Record<string, any>>()
  for (const row of allStats.value) {
    const yr = row.season_year as number
    if (!yr) continue
    if (!byYear.has(yr)) {
      const entry: Record<string, any> = { season_year: yr, team_abbrs: [] }
      STAT_KEYS.forEach(k => { entry[k] = 0 })
      STAT_MAX_KEYS.forEach(k => { entry[k] = 0 })
      byYear.set(yr, entry)
    }
    const agg = byYear.get(yr)!
    STAT_KEYS.forEach(k => { agg[k] = (agg[k] || 0) + (row[k] || 0) })
    STAT_MAX_KEYS.forEach(k => { agg[k] = Math.max(agg[k] || 0, row[k] || 0) })
    if (row.player_team_abbr && !agg.team_abbrs.includes(row.player_team_abbr)) {
      agg.team_abbrs.push(row.player_team_abbr)
    }
  }
  return Array.from(byYear.values()).sort((a, b) => b.season_year - a.season_year)
})

const seasonStats = computed(() =>
  allStats.value
    .filter(r => r.season_year === selectedSeason.value)
    .sort((a, b) => (a.week || 0) - (b.week || 0)),
)

const rangeStats = computed(() =>
  allStats.value.filter(r => {
    const sy = (r.season_year as number) || 0
    const wk = (r.week as number) || 0
    const afterStart = sy > rangeStartYear.value || (sy === rangeStartYear.value && wk >= rangeStartWeek.value)
    const beforeEnd  = sy < rangeEndYear.value   || (sy === rangeEndYear.value   && wk <= rangeEndWeek.value)
    return afterStart && beforeEnd
  }),
)

const baseStats = computed(() => {
  if (viewMode.value === 'career') return careerStats.value
  if (viewMode.value === 'season') return seasonStats.value
  return rangeStats.value
})

const displayStats = computed(() => {
  if (!sortKey.value) return baseStats.value
  const key = sortKey.value
  return [...baseStats.value].sort((a, b) => {
    const av = a[key] ?? 0
    const bv = b[key] ?? 0
    const diff = Number(av) - Number(bv)
    return sortDir.value === 'asc' ? diff : -diff
  })
})

const totalRow = computed(() => {
  const rows = displayStats.value
  if (!rows.length) return null
  const total: Record<string, any> = {}
  STAT_KEYS.forEach(k => { total[k] = rows.reduce((s, r) => s + (r[k] || 0), 0) })
  STAT_MAX_KEYS.forEach(k => { total[k] = Math.max(0, ...rows.map(r => r[k] || 0)) })
  return total
})

const leadingColCount = computed(() => {
  if (viewMode.value === 'career') return 2
  if (viewMode.value === 'season') return 3
  return 4
})

const totalRowLeadingCols = computed(() => {
  if (viewMode.value === 'career') return 2
  if (viewMode.value === 'season') return 3
  return 4
})

function sortBy(key: string) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
}

function sortIcon(key: string): string {
  if (sortKey.value !== key) return '↕'
  return sortDir.value === 'asc' ? '↑' : '↓'
}
</script>

<style scoped>
.player-card-overlay {
  position: fixed;
  z-index: 300;
  width: min(960px, 90vw);
  height: min(580px, 80vh);
  background: var(--color-surface, #0f172a);
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.5rem;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface-alt, #1e293b);
  border-bottom: 1px solid var(--color-border, #334155);
  cursor: grab;
  flex-shrink: 0;
  user-select: none;
}
.card-header:active { cursor: grabbing; }
.card-player-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}
.card-pos-badge {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}
.card-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text, #e2e8f0);
  white-space: nowrap;
}
.card-team {
  font-size: 0.8rem;
  color: var(--color-text-muted, #94a3b8);
  white-space: nowrap;
}
.card-close {
  background: none;
  border: none;
  color: var(--color-text-muted, #94a3b8);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  flex-shrink: 0;
}
.card-close:hover { background: var(--color-surface, #0f172a); color: var(--color-text, #e2e8f0); }

/* Controls */
.card-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  border-bottom: 1px solid var(--color-border, #334155);
  flex-shrink: 0;
  flex-wrap: wrap;
}
.view-mode-btns { display: flex; gap: 0.25rem; }
.view-btn {
  padding: 0.2rem 0.6rem;
  border-radius: 0.3rem;
  border: 1px solid var(--color-border, #334155);
  background: var(--color-surface-alt, #1e293b);
  color: var(--color-text-muted, #94a3b8);
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  transition: background 0.1s;
}
.view-btn.active,
.view-btn:hover {
  background: var(--color-primary, #6366f1);
  border-color: var(--color-primary, #6366f1);
  color: #fff;
}
.stat-type-btns { display: flex; }
.stat-btn {
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--color-border, #334155);
  background: var(--color-surface-alt, #1e293b);
  color: var(--color-text-muted, #94a3b8);
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  transition: background 0.1s;
}
.stat-btn:first-child { border-radius: 0.3rem 0 0 0.3rem; }
.stat-btn:last-child  { border-radius: 0 0.3rem 0.3rem 0; margin-left: -1px; }
.stat-btn:not(:first-child):not(:last-child) { margin-left: -1px; }
.stat-btn.active {
  background: var(--color-primary, #6366f1);
  border-color: var(--color-primary, #6366f1);
  color: #fff;
  z-index: 1;
}
.stat-btn:hover:not(.active) { color: var(--color-text, #e2e8f0); }

/* Time bar */
.card-time-bar {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.75rem;
  border-bottom: 1px solid var(--color-border, #334155);
  flex-shrink: 0;
}
.bar-label {
  font-size: 0.72rem;
  color: var(--color-text-muted, #94a3b8);
  font-weight: 600;
}
.bar-select,
.bar-year,
.bar-week {
  padding: 0.2rem 0.4rem;
  background: var(--color-surface-alt, #1e293b);
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.25rem;
  color: var(--color-text, #e2e8f0);
  font-size: 0.8rem;
  outline: none;
}
.bar-select:focus,
.bar-year:focus,
.bar-week:focus { border-color: var(--color-primary, #6366f1); }
.bar-year { width: 5.5rem; }
.bar-week { width: 3.5rem; }

/* Table */
.card-table-wrap {
  flex: 1;
  overflow: auto;
}
.card-state {
  padding: 1.5rem;
  text-align: center;
  font-size: 0.85rem;
  color: var(--color-text-muted, #94a3b8);
}
.card-stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
.card-stats-table thead {
  position: sticky;
  top: 0;
  z-index: 4;
  background: var(--color-surface, #0f172a);
}

/* Group label cells */
.col-anchor {
  background: var(--color-surface, #0f172a);
  border-bottom: 1px solid var(--color-border, #334155);
}
.col-group-label {
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

/* Column headers */
.th-lead {
  padding: 0.35rem 0.5rem;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, #94a3b8);
  border-bottom: 1px solid var(--color-border, #334155);
  white-space: nowrap;
  background: var(--color-surface, #0f172a);
}
.th-stat {
  padding: 0.35rem 0.5rem;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--color-border, #334155);
  white-space: nowrap;
  text-align: right;
  background: var(--color-surface, #0f172a);
}
.th-sortable { cursor: pointer; user-select: none; }
.th-sortable:hover { color: var(--color-text, #e2e8f0); }

/* Column color accents on headers */
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

/* Group dividers */
.col-divider { border-left: 1px solid var(--color-border, #334155); }

/* Body rows inherit from PlayerStatRow but we add table-level td styles */
.card-stats-table td {
  padding: 0.3rem 0.5rem;
  color: var(--color-text, #e2e8f0);
  white-space: nowrap;
  border-bottom: 1px solid var(--color-border, #334155);
  font-size: 0.8rem;
}
.card-stats-table tbody tr:hover td {
  background: var(--color-surface-alt, #1e293b);
}
</style>
