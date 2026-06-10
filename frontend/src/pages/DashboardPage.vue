<template>
  <div class="space-y-8 max-w-7xl mx-auto">
    <!-- Greeting -->
    <div>
      <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">
        Welcome back{{ authStore.user?.display_name ? ', ' + authStore.user.display_name.split(' ')[0] : '' }}
      </h1>
      <p class="text-sm mt-1" style="color: var(--color-text-secondary)">
        Here's what's happening with your leagues.
      </p>
    </div>

    <!-- My Leagues -->
    <section>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold" style="color: var(--color-text-primary)">My Leagues</h2>
        <RouterLink to="/leagues" class="text-sm hover:underline" style="color: var(--color-primary)">
          View all →
        </RouterLink>
      </div>

      <AppSpinner v-if="loadingLeagues" />

      <div v-else-if="leagues.length === 0">
        <AppEmptyState :icon="Trophy" title="No leagues yet" message="Create a league to get started.">
          <RouterLink to="/leagues" class="mt-4 inline-block">
            <AppButton>Create League</AppButton>
          </RouterLink>
        </AppEmptyState>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <LeagueCard v-for="league in leagues.slice(0, 6)" :key="league.id" :league="league" />
      </div>
    </section>

    <!-- My Teams -->
    <section v-if="teams.length > 0">
      <h2 class="text-lg font-semibold mb-4" style="color: var(--color-text-primary)">My Teams</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <RouterLink
          v-for="team in teams"
          :key="team.id"
          :to="`/leagues/${team.league_id}/teams/${team.id}`"
          class="block"
        >
          <AppCard hoverable>
            <div class="flex items-start justify-between">
              <div>
                <div class="font-semibold text-sm" style="color: var(--color-text-primary)">{{ team.name }}</div>
                <div class="text-xs mt-0.5" style="color: var(--color-text-secondary)">{{ team.league_name }}</div>
              </div>
              <ChevronRight :size="16" style="color: var(--color-text-secondary)" />
            </div>
          </AppCard>
        </RouterLink>
      </div>
    </section>

    <!-- Favorites quick view -->
    <section v-if="favorites.length > 0">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold" style="color: var(--color-text-primary)">Favorites</h2>
        <RouterLink to="/favorites" class="text-sm hover:underline" style="color: var(--color-primary)">
          View all →
        </RouterLink>
      </div>
      <div class="flex flex-wrap gap-2">
        <RouterLink
          v-for="fav in favorites.slice(0, 12)"
          :key="fav.type + fav.id"
          :to="fav.type === 'player' ? `/players/${fav.id}` : `/nfl`"
          class="px-3 py-1.5 rounded-full text-xs font-medium border transition-colors hover:bg-surface-hover"
          style="border-color: var(--color-border); color: var(--color-text-primary)"
        >
          {{ fav.name }}
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Trophy, ChevronRight } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { getLeagues } from '@/api/leagues'
import { listFavorites } from '@/api/favorites'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import LeagueCard from '@/components/leagues/LeagueCard.vue'

const authStore = useAuthStore()
const loadingLeagues = ref(true)
const leagues = ref<any[]>([])
const teams = ref<any[]>([])
const favorites = ref<any[]>([])

onMounted(async () => {
  try {
    const [leagueData, favData] = await Promise.all([getLeagues(), listFavorites()])
    leagues.value = leagueData

    // Flatten teams from all leagues that this user owns
    teams.value = leagueData.flatMap((l: any) =>
      (l.teams || [])
        .filter((t: any) => t.owners?.some((o: any) => o.user_id === authStore.user?.id))
        .map((t: any) => ({ ...t, league_id: l.id, league_name: l.name })),
    )

    // Combine player and team favorites into a flat list
    favorites.value = [
      ...(favData.players || []).map((p: any) => ({ type: 'player', id: p.id, name: p.full_name || p.name })),
      ...(favData.teams || []).map((t: any) => ({ type: 'team', id: t.id, name: t.full_name || t.name })),
    ]
  } finally {
    loadingLeagues.value = false
  }
})
</script>
