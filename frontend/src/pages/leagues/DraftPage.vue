<template>
  <div class="draft-page">
    <AppSpinner v-if="loading" fullPage />

    <template v-else>
      <!-- Status bar -->
      <div class="status-bar">
        <div class="status-left">
          <RouterLink :to="`/leagues/${leagueId}`" class="back-link">← {{ leagueName }}</RouterLink>
          <span class="status-label">
            <template v-if="draftState?.status === 'active'">
              Round {{ currentRound }} · Pick {{ draftState.current_pick }} of {{ draftState.total_picks }}
            </template>
            <template v-else-if="draftState?.status === 'completed'">Draft Complete</template>
            <template v-else-if="draftState?.status === 'paused'">Draft Paused</template>
            <template v-else>Draft Pending</template>
          </span>
        </div>

        <div class="status-center">
          <DraftTimer
            v-if="draftState?.status === 'active' || draftState?.status === 'paused'"
            :seconds-left="draftStore.clientSecondsLeft"
            :is-my-turn="draftStore.isMyTurn"
          />
          <span v-if="draftStore.isMyTurn" class="on-clock-badge">YOUR PICK</span>
        </div>

        <div class="status-right">
          <!-- Commissioner controls -->
          <template v-if="isCommissioner">
            <button
              v-if="!draftState || draftState.status === 'pending'"
              class="btn-ctrl btn-start"
              :disabled="ctrlLoading"
              @click="handleStart"
            >Start Draft</button>
            <button
              v-else-if="draftState.status === 'active'"
              class="btn-ctrl btn-pause"
              :disabled="ctrlLoading"
              @click="handlePause"
            >Pause</button>
            <button
              v-else-if="draftState.status === 'paused'"
              class="btn-ctrl btn-resume"
              :disabled="ctrlLoading"
              @click="handleResume"
            >Resume</button>
          </template>
          <span v-if="ctrlError" class="ctrl-error">{{ ctrlError }}</span>
        </div>
      </div>

      <!-- Pending: show order setup for commissioner -->
      <div v-if="!draftState || draftState.status === 'pending'" class="pending-layout">
        <div v-if="isCommissioner" class="order-setup-card">
          <DraftOrderSetup
            :league-id="leagueId"
            :draft-year="draftYear"
            :teams="teams.map(t => ({ id: t.id, name: t.name }))"
            @updated="draftStore.refresh()"
          />
        </div>
        <div v-else class="pending-msg">
          <p style="color: var(--color-text-secondary)">Waiting for the commissioner to start the draft.</p>
        </div>
      </div>

      <!-- Active / paused / completed: three-panel layout -->
      <div v-else class="draft-layout">
        <!-- Left: Draft Board -->
        <div class="panel panel-board">
          <div class="panel-title">Draft Board</div>
          <DraftBoard
            :order="draftStore.order"
            :picks="draftStore.picks"
            :current-pick="draftState?.current_pick ?? 0"
            :my-team-id="myTeamId"
          />
        </div>

        <!-- Center: Available Players -->
        <div class="panel panel-available">
          <div class="panel-title">Available Players</div>
          <AvailablePlayersPanel
            :league-id="leagueId"
            :draft-year="draftYear"
            :drafted-ids="draftStore.draftedPlayerIds"
            :can-pick="draftStore.isMyTurn || isCommissioner"
            @pick="openPickConfirm"
            @queue="addToQueue"
          />
        </div>

        <!-- Right: My Team + Queue -->
        <div class="panel panel-myteam">
          <MyTeamPanel
            ref="myTeamPanelRef"
            :picks="draftStore.picks"
            :team-id="myTeamId"
            :league-id="leagueId"
            :draft-year="draftYear"
          />
        </div>
      </div>
    </template>

    <!-- Pick confirmation modal -->
    <AppModal v-model="showPickModal">
      <template #title>Confirm Pick</template>
      <div v-if="pendingPlayer" class="confirm-body">
        <PlayerDraftCard :player="pendingPlayer" />
        <p class="confirm-label">Draft this player?</p>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="showPickModal = false">Cancel</button>
          <button class="btn-confirm" :disabled="pickLoading" @click="confirmPick">
            {{ pickLoading ? 'Drafting…' : 'Draft' }}
          </button>
        </div>
        <p v-if="pickError" class="pick-error">{{ pickError }}</p>
      </div>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

import { getLeague, getLeagueTeams, startDraft, pauseDraft, resumeDraft } from '@/api/leagues'
import { useDraftStore } from '@/stores/useDraftStore'
import { useAuthStore } from '@/stores/auth'

import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppModal from '@/components/ui/AppModal.vue'
import DraftTimer from '@/components/draft/DraftTimer.vue'
import DraftBoard from '@/components/draft/DraftBoard.vue'
import AvailablePlayersPanel from '@/components/draft/AvailablePlayersPanel.vue'
import MyTeamPanel from '@/components/draft/MyTeamPanel.vue'
import DraftOrderSetup from '@/components/draft/DraftOrderSetup.vue'
import PlayerDraftCard from '@/components/draft/PlayerDraftCard.vue'

const route = useRoute()
const leagueId = route.params.id as string
const draftYear = new Date().getFullYear()

const auth = useAuthStore()
const draftStore = useDraftStore()

const loading = ref(true)
const leagueName = ref('')
const teams = ref<any[]>([])
const myTeamId = ref('')
const isCommissioner = ref(false)
const ctrlLoading = ref(false)
const ctrlError = ref('')

// Pick confirm
const showPickModal = ref(false)
const pendingPlayer = ref<any>(null)
const pickLoading = ref(false)
const pickError = ref('')

const myTeamPanelRef = ref<InstanceType<typeof MyTeamPanel> | null>(null)

const draftState = computed(() => draftStore.state)

const currentRound = computed(() => {
  if (!draftState.value || !draftStore.order.length) return 1
  const n = draftStore.order.length
  return Math.ceil(draftState.value.current_pick / n)
})

onMounted(async () => {
  try {
    const [league, teamList] = await Promise.all([
      getLeague(leagueId),
      getLeagueTeams(leagueId),
    ])
    leagueName.value = league.name
    teams.value = teamList
    isCommissioner.value = league.created_by === auth.user?.id

    // Find this user's team via created_by_id
    const mine = teamList.find((t: any) => t.created_by_id === auth.user?.id)
    myTeamId.value = mine?.id ?? ''
  } finally {
    loading.value = false
  }

  draftStore.startPolling(leagueId, draftYear, myTeamId.value)
})

onUnmounted(() => {
  draftStore.stopPolling()
})

function openPickConfirm(player: any) {
  pendingPlayer.value = player
  pickError.value = ''
  showPickModal.value = true
}

async function confirmPick() {
  if (!pendingPlayer.value) return
  pickLoading.value = true
  pickError.value = ''
  try {
    await draftStore.submitPick(pendingPlayer.value.player_id)
    showPickModal.value = false
    pendingPlayer.value = null
  } catch (e: any) {
    pickError.value = e?.response?.data?.detail ?? 'Pick failed.'
  } finally {
    pickLoading.value = false
  }
}

function addToQueue(player: any) {
  myTeamPanelRef.value?.addToQueue(player)
}

async function handleStart() {
  ctrlLoading.value = true
  ctrlError.value = ''
  try {
    await startDraft(leagueId, draftYear)
    await draftStore.refresh()
  } catch (e: any) {
    ctrlError.value = e?.response?.data?.detail ?? 'Failed to start draft.'
  } finally {
    ctrlLoading.value = false
  }
}

async function handlePause() {
  ctrlLoading.value = true
  ctrlError.value = ''
  try {
    await draftStore.pause()
  } catch (e: any) {
    ctrlError.value = e?.response?.data?.detail ?? 'Failed to pause.'
  } finally {
    ctrlLoading.value = false
  }
}

async function handleResume() {
  ctrlLoading.value = true
  ctrlError.value = ''
  try {
    await draftStore.resume()
  } catch (e: any) {
    ctrlError.value = e?.response?.data?.detail ?? 'Failed to resume.'
  } finally {
    ctrlLoading.value = false
  }
}
</script>

<style scoped>
.draft-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 4rem);
  overflow: hidden;
}

/* Status bar */
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: var(--color-surface, #0f172a);
  border-bottom: 1px solid var(--color-border, #334155);
  flex-shrink: 0;
}
.status-left { display: flex; align-items: center; gap: 1rem; }
.back-link {
  font-size: 0.8rem;
  color: var(--color-text-muted, #94a3b8);
  text-decoration: none;
}
.back-link:hover { color: var(--color-text, #e2e8f0); }
.status-label { font-size: 0.875rem; font-weight: 600; color: var(--color-text, #e2e8f0); }
.status-center { display: flex; align-items: center; gap: 0.5rem; }
.on-clock-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  background: var(--color-primary, #6366f1);
  color: #fff;
  border-radius: 0.25rem;
  animation: pulse-badge 1s ease-in-out infinite;
}
@keyframes pulse-badge { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.status-right { display: flex; align-items: center; gap: 0.5rem; }

.btn-ctrl {
  padding: 0.35rem 0.9rem;
  border-radius: 0.375rem;
  border: none;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.8rem;
}
.btn-ctrl:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-start { background: var(--color-primary, #6366f1); color: #fff; }
.btn-pause { background: #f59e0b; color: #fff; }
.btn-resume { background: #22c55e; color: #fff; }
.ctrl-error { font-size: 0.75rem; color: #ef4444; }

/* Pending layout */
.pending-layout {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 2rem;
  overflow-y: auto;
}
.order-setup-card {
  background: var(--color-surface-alt, #1e293b);
  border-radius: 0.5rem;
  padding: 1.5rem;
  width: 100%;
  max-width: 480px;
  border: 1px solid var(--color-border, #334155);
}
.pending-msg { padding: 2rem; text-align: center; }

/* Three-panel layout */
.draft-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 320px 240px;
  gap: 0;
  overflow: hidden;
  min-height: 0;
}
.panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid var(--color-border, #334155);
  padding: 0.5rem;
}
.panel:last-child { border-right: none; }
.panel-title {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #94a3b8);
  padding: 0.25rem 0.25rem 0.5rem;
  flex-shrink: 0;
}

/* Modal confirm */
.confirm-body { display: flex; flex-direction: column; gap: 1rem; }
.confirm-label { font-size: 0.9rem; color: var(--color-text, #e2e8f0); }
.confirm-actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
.btn-cancel {
  padding: 0.4rem 1rem;
  border-radius: 0.375rem;
  border: 1px solid var(--color-border, #334155);
  background: transparent;
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
}
.btn-confirm {
  padding: 0.4rem 1.2rem;
  border-radius: 0.375rem;
  border: none;
  background: var(--color-primary, #6366f1);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}
.btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
.pick-error { color: #ef4444; font-size: 0.85rem; }
</style>
