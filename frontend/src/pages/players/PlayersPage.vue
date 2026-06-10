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
        <option v-for="pos in POSITIONS" :key="pos" :value="pos">{{ pos }}</option>
      </select>
    </div>

    <AppSpinner v-if="loading" fullPage />

    <AppEmptyState
      v-else-if="results.length === 0 && query"
      title="No players found"
      :message="`No results for '${query}'`"
    />

    <AppEmptyState v-else-if="results.length === 0" title="Search for a player" message="Enter a name above to search." />

    <AppTable v-else>
      <template #head>
        <tr>
          <th>Name</th>
          <th>Position</th>
          <th>Team</th>
          <th></th>
        </tr>
      </template>
      <tr v-for="p in results" :key="p.id">
        <td>
          <RouterLink :to="`/players/${p.id}`" class="font-medium hover:underline"
            style="color: var(--color-primary)">
            {{ p.full_name || p.name }}
          </RouterLink>
        </td>
        <td><PositionBadge :position="p.position || '—'" /></td>
        <td style="color: var(--color-text-secondary)">{{ p.team_code || p.team || '—' }}</td>
        <td>
          <FavoriteStar
            :is-favorited="favorites.has(p.id)"
            :loading="togglingFav === p.id"
            @toggle="toggleFav(p)"
          />
        </td>
      </tr>
    </AppTable>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { searchPlayers } from '@/api/players'
import { listFavorites, addPlayerFavorite, removePlayerFavorite } from '@/api/favorites'
import SearchInput from '@/components/common/SearchInput.vue'
import PositionBadge from '@/components/common/PositionBadge.vue'
import FavoriteStar from '@/components/common/FavoriteStar.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'

const POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']

const query = ref('')
const position = ref('')
const loading = ref(false)
const results = ref<any[]>([])
const favorites = ref<Set<string>>(new Set())
const togglingFav = ref<string | null>(null)

async function loadFavorites() {
  const data = await listFavorites()
  favorites.value = new Set((data.players || []).map((p: any) => p.id))
}

watch([query, position], async () => {
  if (!query.value && !position.value) { results.value = []; return }
  loading.value = true
  try {
    results.value = await searchPlayers(query.value, position.value)
  } finally {
    loading.value = false
  }
}, { debounce: 50 } as any)

async function toggleFav(player: any) {
  togglingFav.value = player.id
  try {
    if (favorites.value.has(player.id)) {
      await removePlayerFavorite(player.id)
      favorites.value.delete(player.id)
    } else {
      await addPlayerFavorite(player.id)
      favorites.value.add(player.id)
    }
    favorites.value = new Set(favorites.value) // trigger reactivity
  } finally {
    togglingFav.value = null
  }
}

loadFavorites()
</script>
