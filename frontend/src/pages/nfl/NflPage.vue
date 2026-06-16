<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">NFL</h1>
        <p class="text-sm mt-1" style="color: var(--color-text-secondary)">Scores, stats, and player data</p>
      </div>
      <RouterLink to="/nfl/games">
        <AppButton>Browse Games →</AppButton>
      </RouterLink>
    </div>

    <AppSpinner v-if="loading" fullPage />

    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-3">
      <RouterLink
        v-for="team in teams"
        :key="team.id"
        :to="`/nfl/games?team=${team.abbr || team.id}`"
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
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getTeams } from '@/api/stats'
import AppButton from '@/components/ui/AppButton.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import TeamHelmet from '@/components/common/TeamHelmet.vue'

const loading = ref(true)
const teams = ref<any[]>([])

onMounted(async () => {
  try { teams.value = await getTeams() }
  finally { loading.value = false }
})
</script>
