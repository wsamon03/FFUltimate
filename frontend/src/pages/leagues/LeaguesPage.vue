<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">Leagues</h1>
      <AppButton @click="showCreate = true">New League</AppButton>
    </div>

    <AppSpinner v-if="loading" fullPage />

    <div v-else-if="leagues.length === 0">
      <AppEmptyState :icon="Trophy" title="No leagues yet" message="Create your first league to get started.">
        <AppButton class="mt-4" @click="showCreate = true">Create League</AppButton>
      </AppEmptyState>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <LeagueCard v-for="l in leagues" :key="l.id" :league="l" />
    </div>

    <!-- Create league modal -->
    <AppModal v-model="showCreate">
      <template #title>Create League</template>
      <form class="space-y-4" @submit.prevent="createLeague">
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">League Name</label>
          <input
            v-model="form.name"
            required
            class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none focus:ring-2"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
            placeholder="My Fantasy League"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Description (optional)</label>
          <textarea
            v-model="form.description"
            rows="2"
            class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none focus:ring-2 resize-none"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">League Type</label>
            <select
              v-model="form.league_type_id"
              class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none focus:ring-2"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
            >
              <option v-for="t in LEAGUE_TYPES" :key="t.id" :value="t.id">{{ t.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Visibility</label>
            <select
              v-model="form.available_scope_id"
              class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none focus:ring-2"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
            >
              <option v-for="s in SCOPES" :key="s.id" :value="s.id">{{ s.label }}</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Season Year</label>
            <input
              v-model.number="form.season_year"
              type="number"
              min="2020"
              max="2035"
              class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none focus:ring-2"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Max Teams</label>
            <input
              v-model.number="form.max_teams"
              type="number"
              min="2"
              max="64"
              class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none focus:ring-2"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
            />
          </div>
        </div>
        <div class="flex gap-3 justify-end pt-2">
          <AppButton variant="ghost" type="button" @click="showCreate = false">Cancel</AppButton>
          <AppButton type="submit" :loading="creating">Create</AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Trophy } from '@lucide/vue'
import { getLeagues, createLeague as apiCreate } from '@/api/leagues'
import AppButton from '@/components/ui/AppButton.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import LeagueCard from '@/components/leagues/LeagueCard.vue'

const LEAGUE_TYPES = [
  { id: 1, label: 'Redraft' },
  { id: 2, label: 'Keeper' },
  { id: 3, label: 'Dynasty' },
  { id: 4, label: 'Best Ball' },
]
const SCOPES = [
  { id: 1, label: 'Private' },
  { id: 2, label: 'Public' },
]

const loading = ref(true)
const leagues = ref<any[]>([])
const showCreate = ref(false)
const creating = ref(false)
const form = ref({
  name: '',
  description: '',
  league_type_id: 1,
  available_scope_id: 1,
  season_year: new Date().getFullYear(),
  max_teams: 12,
})

onMounted(async () => {
  try { leagues.value = await getLeagues() }
  finally { loading.value = false }
})

async function createLeague() {
  creating.value = true
  try {
    const league = await apiCreate({ ...form.value })
    leagues.value.unshift(league)
    showCreate.value = false
    form.value = {
      name: '',
      description: '',
      league_type_id: 1,
      available_scope_id: 1,
      season_year: new Date().getFullYear(),
      max_teams: 12,
    }
  } finally {
    creating.value = false
  }
}
</script>
