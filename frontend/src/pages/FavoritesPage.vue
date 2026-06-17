<template>
  <div class="max-w-7xl mx-auto space-y-8">
    <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">Favorites</h1>

    <AppSpinner v-if="loading" fullPage />

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Favorited Players -->
      <section>
        <h2 class="text-lg font-semibold mb-4" style="color: var(--color-text-primary)">Players</h2>
        <AppEmptyState
          v-if="players.length === 0"
          title="No favorite players"
          message="Star a player on their detail page to add them here."
        />
        <AppTable v-else>
          <template #head>
            <tr>
              <th>Player</th>
              <th>Position</th>
              <th>Team</th>
              <th></th>
            </tr>
          </template>
          <tr v-for="p in players" :key="p.id">
            <td>
              <RouterLink :to="`/players/${p.id}`" class="font-medium hover:underline"
                style="color: var(--color-primary)">
                {{ p.full_name || p.name }}
              </RouterLink>
            </td>
            <td><PositionBadge :position="p.position || '—'" /></td>
            <td>
              <TeamHelmet v-if="p.team_code" :abbr="p.team_code" :size="24" />
              <span v-else style="color: var(--color-text-secondary)">—</span>
            </td>
            <td>
              <FavoriteStar :is-favorited="true" :loading="removingPlayer === p.id" @toggle="removePlayer(p)" />
            </td>
          </tr>
        </AppTable>
      </section>

      <!-- Favorited NFL Teams -->
      <section>
        <h2 class="text-lg font-semibold mb-4" style="color: var(--color-text-primary)">NFL Teams</h2>
        <AppEmptyState
          v-if="nflTeams.length === 0"
          title="No favorite teams"
          message="Star an NFL team on the NFL page to add them here."
        />
        <AppTable v-else>
          <template #head>
            <tr>
              <th>Team</th>
              <th></th>
              <th></th>
            </tr>
          </template>
          <tr v-for="t in nflTeams" :key="t.id">
            <td class="font-medium" style="color: var(--color-text-primary)">{{ t.full_name || t.name }}</td>
            <td>
              <TeamHelmet v-if="t.abbreviation || t.code" :abbr="t.abbreviation || t.code" :size="24" />
              <span v-else style="color: var(--color-text-secondary)">—</span>
            </td>
            <td>
              <FavoriteStar :is-favorited="true" :loading="removingTeam === t.id" @toggle="removeTeam(t)" />
            </td>
          </tr>
        </AppTable>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listFavorites, removePlayerFavorite, removeTeamFavorite } from '@/api/favorites'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import FavoriteStar from '@/components/common/FavoriteStar.vue'
import PositionBadge from '@/components/common/PositionBadge.vue'
import TeamHelmet from '@/components/common/TeamHelmet.vue'

const loading = ref(true)
const players = ref<any[]>([])
const nflTeams = ref<any[]>([])
const removingPlayer = ref<string | null>(null)
const removingTeam = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    const favorites = await listFavorites()
    players.value = favorites
      .filter((f: any) => f.kind === 'player')
      .map((f: any) => ({ id: f.target_id, name: f.name, full_name: f.full_name, position: f.position_code, team_code: f.team_code }))
    nflTeams.value = favorites
      .filter((f: any) => f.kind === 'team')
      .map((f: any) => ({ id: f.target_id, name: f.name, full_name: f.full_name, code: f.abbr, abbreviation: f.abbr }))
  } finally {
    loading.value = false
  }
}

async function removePlayer(p: any) {
  removingPlayer.value = p.id
  try {
    await removePlayerFavorite(p.id)
    players.value = players.value.filter(x => x.id !== p.id)
  } finally {
    removingPlayer.value = null
  }
}

async function removeTeam(t: any) {
  removingTeam.value = t.id
  try {
    await removeTeamFavorite(t.id)
    nflTeams.value = nflTeams.value.filter(x => x.id !== t.id)
  } finally {
    removingTeam.value = null
  }
}

onMounted(load)
</script>
