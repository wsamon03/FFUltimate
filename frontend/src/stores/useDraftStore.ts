import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import {
  getDraftRoom,
  makeDraftPick,
  autopick,
  pauseDraft,
  resumeDraft,
} from '@/api/leagues'

export const useDraftStore = defineStore('draft', () => {
  // Raw state from server
  const state = ref<Record<string, any> | null>(null)
  const order = ref<any[]>([])
  const picks = ref<any[]>([])

  // Local timer
  const clientSecondsLeft = ref(0)

  // IDs for polling scope
  const _leagueId = ref('')
  const _draftYear = ref(0)
  const _myTeamId = ref('')

  // Polling
  let _pollInterval: ReturnType<typeof setInterval> | null = null
  let _timerInterval: ReturnType<typeof setInterval> | null = null
  let _lastHash = ''

  // Computed
  const currentPickTeamId = computed(() => {
    if (!state.value || state.value.status !== 'active') return null
    const cur = state.value.current_pick
    const totalTeams = state.value.total_picks > 0
      ? Math.round(state.value.total_picks / (state.value.total_picks / order.value.length || 1))
      : order.value.length
    if (!totalTeams) return null
    // Find the pick shell for current_pick to get the team
    const pickShell = picks.value.find((p: any) => p.pick_number === cur)
    return pickShell?.league_team_id ?? null
  })

  const isMyTurn = computed(
    () => !!_myTeamId.value && currentPickTeamId.value === _myTeamId.value,
  )

  const draftedPlayerIds = computed<Set<string>>(() => {
    const ids = new Set<string>()
    for (const p of picks.value) {
      if (p.player_id) ids.add(p.player_id)
    }
    return ids
  })

  function _applyServerState(data: any) {
    if (!data) return
    const newHash = data.state?.state_hash ?? ''
    if (newHash && newHash === _lastHash) return
    _lastHash = newHash

    state.value = data.state ?? null
    order.value = data.order ?? []
    picks.value = data.picks ?? []

    // Sync client timer to server
    if (state.value?.status === 'active' && state.value.pick_started_at) {
      const elapsed = (Date.now() - new Date(state.value.pick_started_at).getTime()) / 1000
      const secs = state.value.seconds_per_pick ?? 90
      clientSecondsLeft.value = Math.max(0, Math.round(secs - elapsed))
    } else if (state.value?.status === 'paused') {
      clientSecondsLeft.value = state.value.paused_seconds_left ?? 0
    } else {
      clientSecondsLeft.value = 0
    }
  }

  function _startTimer() {
    if (_timerInterval) clearInterval(_timerInterval)
    _timerInterval = setInterval(() => {
      if (state.value?.status !== 'active') return
      if (clientSecondsLeft.value > 0) {
        clientSecondsLeft.value--
      } else {
        // Timer expired — trigger autopick
        _triggerAutopick()
      }
    }, 1000)
  }

  async function _triggerAutopick() {
    if (!_leagueId.value || !_draftYear.value) return
    try {
      await autopick(_leagueId.value, _draftYear.value)
      await _poll()
    } catch {
      // Ignore — another client may have already picked
    }
  }

  async function _poll() {
    if (!_leagueId.value || !_draftYear.value) return
    try {
      const data = await getDraftRoom(_leagueId.value, _draftYear.value)
      _applyServerState(data)
    } catch {
      // Network blip — keep polling
    }
  }

  function startPolling(leagueId: string, draftYear: number, myTeamId: string) {
    _leagueId.value = leagueId
    _draftYear.value = draftYear
    _myTeamId.value = myTeamId
    _lastHash = ''

    _poll()
    _pollInterval = setInterval(_poll, 2500)
    _startTimer()
  }

  function stopPolling() {
    if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null }
    if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null }
  }

  async function submitPick(playerId: string) {
    if (!state.value) return
    await makeDraftPick(
      _leagueId.value,
      _draftYear.value,
      state.value.current_pick,
      playerId,
    )
    await _poll()
  }

  async function pause() {
    await pauseDraft(_leagueId.value, _draftYear.value)
    await _poll()
  }

  async function resume() {
    await resumeDraft(_leagueId.value, _draftYear.value)
    await _poll()
  }

  async function refresh() {
    _lastHash = ''
    await _poll()
  }

  return {
    state,
    order,
    picks,
    clientSecondsLeft,
    currentPickTeamId,
    isMyTurn,
    draftedPlayerIds,
    startPolling,
    stopPolling,
    submitPick,
    pause,
    resume,
    refresh,
  }
})
