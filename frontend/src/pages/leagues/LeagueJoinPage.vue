<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-md w-full max-w-md p-8">
      <!-- Loading -->
      <div v-if="loading" class="text-center text-gray-500">Loading league info…</div>

      <!-- Error -->
      <div v-else-if="error" class="text-center">
        <p class="text-red-600 font-medium mb-4">{{ error }}</p>
        <RouterLink to="/login" class="text-indigo-600 hover:underline">Go to login</RouterLink>
      </div>

      <!-- League preview -->
      <template v-else-if="league">
        <h1 class="text-2xl font-bold mb-1" style="color: #000000">Join {{ league.name }}</h1>
        <p v-if="league.description" class="text-sm mb-4" style="color: #000000">{{ league.description }}</p>

        <div class="grid grid-cols-2 gap-3 text-sm mb-6" style="color: #000000">
          <div><span class="font-medium">Season:</span> {{ league.season_year }}</div>
          <div><span class="font-medium">Format:</span> {{ league.league_type_name }}</div>
          <div><span class="font-medium">Teams:</span> {{ league.team_count }} / {{ league.max_teams }}</div>
        </div>

        <!-- Logged in: show join form -->
        <div v-if="authStore.token">
          <div v-if="joined" class="text-center">
            <p class="text-green-600 font-medium mb-4">You've joined the league!</p>
            <RouterLink
              :to="`/leagues/${league.id}`"
              class="bg-indigo-600 text-white px-5 py-2 rounded-lg hover:bg-indigo-700 transition"
            >
              Go to League
            </RouterLink>
          </div>
          <form v-else @submit.prevent="handleJoin" class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: #000000">Team Name</label>
              <input
                v-model="teamName"
                type="text"
                maxlength="100"
                required
                placeholder="My Team"
                class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                style="color: #000000"
              />
            </div>
            <p v-if="joinError" class="text-red-600 text-sm">{{ joinError }}</p>
            <button
              type="submit"
              :disabled="joining"
              class="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
            >
              {{ joining ? 'Joining…' : 'Join League' }}
            </button>
          </form>
        </div>

        <!-- Not logged in: redirect to login -->
        <div v-else class="text-center">
          <p class="text-black text-sm mb-4">You need to log in to join this league.</p>
          <RouterLink
            :to="`/login?redirect=/leagues/join/${route.params.code}`"
            class="inline-block bg-indigo-600 text-white px-5 py-2 rounded-lg hover:bg-indigo-700 transition"
          >
            Log in to Join
          </RouterLink>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getLeagueByCode, joinLeague } from '@/api/leagues'

const route = useRoute()
const authStore = useAuthStore()

const league = ref<any>(null)
const loading = ref(true)
const error = ref('')

const teamName = ref('My Team')
const joining = ref(false)
const joined = ref(false)
const joinError = ref('')

onMounted(async () => {
  try {
    const code = route.params.code as string
    league.value = await getLeagueByCode(code)
  } catch {
    error.value = 'This invite link is invalid or has expired.'
  } finally {
    loading.value = false
  }
})

async function handleJoin() {
  if (!teamName.value.trim()) return
  joining.value = true
  joinError.value = ''
  try {
    const code = route.params.code as string
    await joinLeague(code, teamName.value.trim())
    joined.value = true
  } catch (err: any) {
    joinError.value = err?.response?.data?.detail ?? 'Failed to join league. Please try again.'
  } finally {
    joining.value = false
  }
}
</script>
