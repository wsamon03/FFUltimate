<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <AppSpinner v-if="loading" fullPage />

    <template v-else-if="league">
      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">{{ league.name }}</h1>
          <p v-if="league.description" class="text-sm mt-1" style="color: var(--color-text-secondary)">
            {{ league.description }}
          </p>
        </div>
        <AppButton @click="showAddTeam = true">Add Team</AppButton>
      </div>

      <!-- Teams grid -->
      <div v-if="teams.length === 0">
        <AppEmptyState title="No teams yet" message="Add the first team to this league." />
      </div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <RouterLink
          v-for="team in teams"
          :key="team.id"
          :to="`/leagues/${leagueId}/teams/${team.id}`"
        >
          <AppCard hoverable>
            <div class="flex items-center justify-between">
              <div>
                <div class="font-semibold" style="color: var(--color-text-primary)">{{ team.name }}</div>
                <div class="text-xs mt-0.5" style="color: var(--color-text-secondary)">
                  {{ team.owners?.length || 0 }} owner(s)
                </div>
              </div>
              <ChevronRight :size="16" style="color: var(--color-text-secondary)" />
            </div>
          </AppCard>
        </RouterLink>
      </div>
    </template>

    <!-- Add Team modal -->
    <AppModal v-model="showAddTeam">
      <template #title>Add Team</template>
      <form class="space-y-4" @submit.prevent="addTeam">
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Team Name</label>
          <input
            v-model="teamForm.name"
            required
            class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none focus:ring-2"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          />
        </div>
        <div class="flex gap-3 justify-end">
          <AppButton variant="ghost" type="button" @click="showAddTeam = false">Cancel</AppButton>
          <AppButton type="submit" :loading="addingTeam">Add</AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronRight } from '@lucide/vue'
import { getLeague, getLeagueTeams, createTeam } from '@/api/leagues'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'

const route = useRoute()
const leagueId = route.params.id as string

const loading = ref(true)
const league = ref<any>(null)
const teams = ref<any[]>([])
const showAddTeam = ref(false)
const addingTeam = ref(false)
const teamForm = ref({ name: '' })

onMounted(async () => {
  try {
    const [l, t] = await Promise.all([getLeague(leagueId), getLeagueTeams(leagueId)])
    league.value = l
    teams.value = t
  } finally {
    loading.value = false
  }
})

async function addTeam() {
  addingTeam.value = true
  try {
    const team = await createTeam(leagueId, teamForm.value.name)
    teams.value.push(team)
    showAddTeam.value = false
    teamForm.value = { name: '' }
  } finally {
    addingTeam.value = false
  }
}
</script>
