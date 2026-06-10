<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <AppSpinner v-if="loading" fullPage />

    <template v-else-if="team">
      <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">{{ team.name }}</h1>

      <!-- Tabs -->
      <div class="flex gap-1 border-b" style="border-color: var(--color-border)">
        <button
          v-for="tab in ['Roster', 'Lineup', 'Owners']"
          :key="tab"
          class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
          :style="activeTab === tab
            ? `border-color: var(--color-primary); color: var(--color-primary)`
            : `border-color: transparent; color: var(--color-text-secondary)`"
          @click="activeTab = tab"
        >
          {{ tab }}
        </button>
      </div>

      <!-- Roster tab -->
      <div v-if="activeTab === 'Roster'">
        <RosterTable :roster="roster" :can-edit="true" @drop="dropPlayer" />
      </div>

      <!-- Lineup tab -->
      <div v-else-if="activeTab === 'Lineup'">
        <div class="mb-3 flex items-center gap-3">
          <label class="text-sm font-medium" style="color: var(--color-text-primary)">Week</label>
          <input
            v-model.number="lineupWeek"
            type="number" min="1" max="22"
            class="w-20 text-sm rounded-lg px-3 py-1.5 border"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
          />
        </div>
        <LineupEditor
          :roster="roster"
          :initial-lineup="currentLineup"
          :saving="savingLineup"
          @save="saveLineup"
        />
      </div>

      <!-- Owners tab -->
      <div v-else-if="activeTab === 'Owners'">
        <AppTable>
          <template #head>
            <tr>
              <th>User</th>
              <th>Role</th>
            </tr>
          </template>
          <tr v-for="owner in team.owners" :key="owner.user_id">
            <td style="color: var(--color-text-primary)">{{ owner.display_name || owner.user_id }}</td>
            <td>
              <AppBadge :color="owner.is_commissioner ? 'blue' : 'gray'">
                {{ owner.is_commissioner ? 'Commissioner' : 'Owner' }}
              </AppBadge>
            </td>
          </tr>
        </AppTable>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getTeamDetail, getTeamRoster, getTeamLineup, setTeamLineup } from '@/api/leagues'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppTable from '@/components/ui/AppTable.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import RosterTable from '@/components/leagues/RosterTable.vue'
import LineupEditor from '@/components/leagues/LineupEditor.vue'

const route = useRoute()
const leagueId = route.params.id as string
const teamId = route.params.teamId as string

const loading = ref(true)
const team = ref<any>(null)
const roster = ref<any[]>([])
const activeTab = ref('Roster')
const lineupWeek = ref(1)
const currentLineup = ref<Record<string, string>>({})
const savingLineup = ref(false)

onMounted(async () => {
  try {
    const [t, r] = await Promise.all([getTeamDetail(leagueId, teamId), getTeamRoster(leagueId, teamId)])
    team.value = t
    roster.value = r
  } finally {
    loading.value = false
  }
})

async function dropPlayer(playerId: string) {
  roster.value = roster.value.filter(p => p.player_id !== playerId)
}

async function saveLineup(lineup: Record<string, string>) {
  savingLineup.value = true
  try {
    const slots = Object.entries(lineup)
      .filter(([, playerId]) => playerId)
      .map(([slotPosition, player_id]) => ({ slot_position: slotPosition, player_id }))
    await setTeamLineup(leagueId, teamId, lineupWeek.value, slots)
    currentLineup.value = lineup
  } finally {
    savingLineup.value = false
  }
}
</script>
