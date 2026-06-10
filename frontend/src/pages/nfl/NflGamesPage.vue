<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">NFL Games</h1>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 items-end">
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Season</label>
        <input
          v-model.number="filters.season"
          type="number" min="2000" :max="currentYear"
          class="w-24 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
          style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Week</label>
        <input
          v-model.number="filters.week"
          type="number" min="0" max="22"
          class="w-20 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
          style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
        />
      </div>
      <AppButton size="sm" @click="loadGames">Apply</AppButton>
    </div>

    <AppSpinner v-if="loading" fullPage />

    <AppEmptyState v-else-if="games.length === 0" title="No games found" message="Try adjusting the filters." />

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <NflGameCard v-for="game in games" :key="game.id" :game="game" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getGames } from '@/api/stats'
import AppButton from '@/components/ui/AppButton.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import NflGameCard from '@/components/nfl/NflGameCard.vue'

const route = useRoute()
const currentYear = new Date().getFullYear()

const filters = ref({
  season: currentYear,
  week: 1,
  team: route.query.team as string || '',
})

const loading = ref(false)
const games = ref<any[]>([])

async function loadGames() {
  loading.value = true
  try {
    games.value = await getGames(filters.value.season, filters.value.week)
  } finally {
    loading.value = false
  }
}

onMounted(loadGames)
</script>
