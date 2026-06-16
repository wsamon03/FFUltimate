<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">Players</h1>

    <!-- Search + filters -->
    <div class="flex flex-wrap gap-3 items-end">
      <div class="flex-1 min-w-56">
        <SearchInput v-model="query" placeholder="Search players…" />
      </div>
      <select
        v-model="position"
        class="text-sm rounded-lg px-3 py-2 border focus:outline-none"
        style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary)"
      >
        <option value="">All Positions</option>
        <option v-for="pos in positions" :key="pos" :value="pos">{{ pos }}</option>
      </select>
      <input
        v-model.number="year"
        type="number"
        min="2020"
        :max="2026"
        class="text-sm rounded-lg px-3 py-2 border focus:outline-none w-24"
        style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary)"
      />
      <div class="flex rounded-lg overflow-hidden border" style="border-color: var(--color-border)">
        <button
          v-for="type in statTypes"
          :key="type.value"
          class="px-4 py-2 text-sm font-medium transition-colors"
          :style="statType === type.value
            ? 'background: var(--color-primary); color: #fff'
            : 'background: var(--color-card); color: var(--color-text-secondary)'"
          @click="statType = type.value"
        >
          {{ type.label }}
        </button>
      </div>
    </div>

    <AppSpinner v-if="loading" fullPage />

    <AppEmptyState
      v-else-if="sortedPlayers.length === 0"
      title="No players found"
      message="No stats available for the selected filters."
    />

    <AppTable v-else>
      <template #head>
        <tr>
          <th class="fav-cell"></th>
          <th class="helmet-cell"></th>
          <th>Player</th>
          <th>Pos</th>
          <th>Team</th>
          <template v-if="statType === 'offense'">
            <th title="Completions">CMP</th>
            <th title="Pass Attempts">ATT</th>
            <th title="Pass Yards">YDS</th>
            <th title="Pass TDs">TD</th>
            <th title="Interceptions thrown">INT</th>
            <th title="Rush Attempts">ATT</th>
            <th title="Rush Yards">YDS</th>
            <th title="Rush TDs">TD</th>
            <th title="Receptions">REC</th>
            <th title="Targets">TGT</th>
            <th title="Receiving Yards">YDS</th>
            <th title="Receiving TDs">TD</th>
          </template>
          <template v-else>
            <th title="Solo Tackles">SOLO</th>
            <th title="Assisted Tackles">AST</th>
            <th title="Sacks">SACKS</th>
            <th title="Tackles for Loss">TFL</th>
            <th title="Passes Defensed">PD</th>
            <th title="QB Hits">QB HIT</th>
            <th title="Defensive TDs">DEF TD</th>
            <th title="Interceptions">INT</th>
          </template>
        </tr>
      </template>
      <tr v-for="p in sortedPlayers" :key="p.player_id">
        <td class="fav-cell">
          <FavoriteStar
            :is-favorited="favorites.has(p.player_id)"
            :loading="togglingFav === p.player_id"
            @toggle="toggleFav(p)"
          />
        </td>
        <td class="helmet-cell">
          <TeamHelmet v-if="p.team_abbr" :abbr="p.team_abbr" :size="24" />
          <span v-else style="color: var(--color-text-secondary)">—</span>
        </td>
        <td>
          <RouterLink
            :to="`/players/${p.player_id}`"
            class="font-medium hover:underline"
            style="color: var(--color-primary)"
          >
            {{ p.name }}
          </RouterLink>
        </td>
        <td>
          <PositionBadge v-if="p.position_code" :position="p.position_code" />
          <span v-else style="color: var(--color-text-secondary)">—</span>
        </td>
        <td style="color: var(--color-text-secondary); font-size: 0.875rem">{{ p.team_abbr || '—' }}</td>
        <template v-if="statType === 'offense'">
          <td>{{ p.pass_comp }}</td>
          <td>{{ p.pass_att }}</td>
          <td>{{ p.pass_yds }}</td>
          <td>{{ p.pass_td }}</td>
          <td>{{ p.pass_int }}</td>
          <td>{{ p.rush_att }}</td>
          <td>{{ p.rush_yds }}</td>
          <td>{{ p.rush_td }}</td>
          <td>{{ p.rec_receptions }}</td>
          <td>{{ p.rec_targets }}</td>
          <td>{{ p.rec_yds }}</td>
          <td>{{ p.rec_td }}</td>
        </template>
        <template v-else>
          <td>{{ p.def_solo }}</td>
          <td>{{ p.def_ast }}</td>
          <td>{{ p.def_sacks }}</td>
          <td>{{ p.def_tfl }}</td>
          <td>{{ p.def_pd }}</td>
          <td>{{ p.def_qb_hits }}</td>
          <td>{{ p.def_td }}</td>
          <td>{{ p.def_int }}</td>
        </template>
      </tr>
    </AppTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { getPlayerSeasonStats, getPlayerPositions } from '@/api/stats'
import { listFavorites, addPlayerFavorite, removePlayerFavorite } from '@/api/favorites'
import SearchInput from '@/components/common/SearchInput.vue'
import PositionBadge from '@/components/common/PositionBadge.vue'
import FavoriteStar from '@/components/common/FavoriteStar.vue'
import TeamHelmet from '@/components/common/TeamHelmet.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'

const statTypes = [
  { value: 'offense', label: 'Offense' },
  { value: 'defense', label: 'Defense' },
]

const query = ref('')
const position = ref('')
const year = ref(2025)
const statType = ref('offense')
const loading = ref(false)
const players = ref<any[]>([])
const positions = ref<string[]>([])
const favorites = ref<Set<string>>(new Set())
const togglingFav = ref<string | null>(null)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const sortedPlayers = computed(() => {
  if (statType.value === 'defense') {
    return [...players.value].sort((a, b) => {
      const aScore = (a.def_solo ?? 0) + (a.def_ast ?? 0) + (a.def_sacks ?? 0) * 2
      const bScore = (b.def_solo ?? 0) + (b.def_ast ?? 0) + (b.def_sacks ?? 0) * 2
      return bScore - aScore
    })
  }
  return players.value
})

async function loadStats() {
  loading.value = true
  try {
    players.value = await getPlayerSeasonStats(
      year.value,
      query.value || undefined,
      position.value || undefined,
    )
  } finally {
    loading.value = false
  }
}

async function loadFavorites() {
  const data = await listFavorites()
  favorites.value = new Set((data.players || []).map((p: any) => p.id))
}

watch(query, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadStats, 300)
})

watch([position, year], loadStats)

async function toggleFav(player: any) {
  togglingFav.value = player.player_id
  try {
    if (favorites.value.has(player.player_id)) {
      await removePlayerFavorite(player.player_id)
      favorites.value.delete(player.player_id)
    } else {
      await addPlayerFavorite(player.player_id)
      favorites.value.add(player.player_id)
    }
    favorites.value = new Set(favorites.value)
  } finally {
    togglingFav.value = null
  }
}

onMounted(async () => {
  await Promise.all([
    loadStats(),
    loadFavorites(),
    getPlayerPositions().then((p) => { positions.value = p }),
  ])
})
</script>

<style scoped>
.fav-cell {
  white-space: nowrap;
  flex-shrink: 0;
  text-align: center;
  padding: 8px 6px;
  width: 36px;
}
.helmet-cell {
  white-space: nowrap;
  flex-shrink: 0;
  text-align: center;
  padding: 8px 6px;
  width: 36px;
}
</style>
