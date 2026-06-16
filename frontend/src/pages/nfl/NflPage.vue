<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">NFL</h1>
        <p class="text-sm mt-1" style="color: var(--color-text-secondary)">Scores, stats, and player data</p>
      </div>
    </div>

    <!-- Browse all games by season + week -->
    <AppCard>
      <div class="flex flex-wrap gap-3 items-end">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Season</label>
          <input
            v-model.number="season"
            type="number" min="2000" :max="currentYear"
            class="w-24 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
            style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Week</label>
          <input
            v-model.number="week"
            type="number" min="0" max="22"
            class="w-20 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
            style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          />
        </div>
        <RouterLink :to="`/nfl/games?season=${season}&week=${week}`">
          <AppButton>View All Games →</AppButton>
        </RouterLink>
      </div>
    </AppCard>

    <div>
      <h2 class="text-base font-semibold mb-3" style="color: var(--color-text-secondary)">Browse by Team</h2>

      <AppSpinner v-if="loading" fullPage />

      <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-3">
        <RouterLink
          v-for="team in teams"
          :key="team.id"
          :to="`/nfl/games?season=${season}&week=${week}&team=${team.abbr || team.id}`"
          class="block"
        >
          <AppCard hoverable>
            <div class="text-center">
              <div class="flex justify-center mb-2">
                <TeamHelmet :abbr="team.abbr || team.espn_id || '?'" :size="40" />
              </div>
              <div class="text-xs font-medium truncate" style="color: var(--color-text-primary)">
                {{ team.full_name || team.abbr }}
              </div>
            </div>
          </AppCard>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getTeams } from '@/api/stats'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import TeamHelmet from '@/components/common/TeamHelmet.vue'

const currentYear = new Date().getFullYear()
const season = ref(currentYear)
const week = ref(1)

const loading = ref(true)
const teams = ref<any[]>([])

onMounted(async () => {
  try { teams.value = await getTeams() }
  finally { loading.value = false }
})
</script>
