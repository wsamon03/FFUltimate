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

const loading = ref(true)
const leagues = ref<any[]>([])
const showCreate = ref(false)
const creating = ref(false)
const form = ref({ name: '', description: '' })

onMounted(async () => {
  try { leagues.value = await getLeagues() }
  finally { loading.value = false }
})

async function createLeague() {
  creating.value = true
  try {
    const league = await apiCreate(form.value.name, form.value.description)
    leagues.value.unshift(league)
    showCreate.value = false
    form.value = { name: '', description: '' }
  } finally {
    creating.value = false
  }
}
</script>
