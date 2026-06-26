<template>
  <div class="avail-panel">
    <!-- Position tabs -->
    <div class="pos-tabs">
      <button
        v-for="pos in POSITIONS"
        :key="pos"
        class="pos-tab"
        :class="{ active: activePosition === pos }"
        @click="setPosition(pos)"
      >{{ pos }}</button>
    </div>

    <!-- Search -->
    <div class="search-row">
      <input
        v-model="searchText"
        class="search-input"
        type="text"
        placeholder="Search players…"
      />
    </div>

    <!-- Player list -->
    <div class="player-list">
      <div v-if="loading && !players.length" class="state-msg">Loading…</div>
      <div v-else-if="!players.length" class="state-msg">No players found.</div>

      <div
        v-for="player in players"
        :key="player.player_id"
        class="player-row"
        :class="{ drafted: draftedIds.has(player.player_id) }"
      >
        <PlayerDraftCard :player="player" />
        <div class="row-actions">
          <button
            class="btn-queue"
            title="Add to queue"
            @click="emit('queue', player)"
          >+</button>
          <button
            class="btn-pick"
            :disabled="!canPick || draftedIds.has(player.player_id)"
            @click="emit('pick', player)"
          >Draft</button>
        </div>
      </div>

      <button
        v-if="players.length > 0 && players.length % limit === 0"
        class="btn-more"
        :disabled="loading"
        @click="loadMore"
      >Load more</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { getAvailablePlayers } from '@/api/leagues'
import PlayerDraftCard from './PlayerDraftCard.vue'

const POSITIONS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DST']
const limit = 50

const props = defineProps<{
  leagueId: string
  draftYear: number
  draftedIds: Set<string>
  canPick: boolean
}>()

const emit = defineEmits<{
  (e: 'pick', player: any): void
  (e: 'queue', player: any): void
}>()

const players = ref<any[]>([])
const loading = ref(false)
const activePosition = ref('ALL')
const searchText = ref('')
let _debounceTimer: ReturnType<typeof setTimeout> | null = null

async function load(reset = true) {
  loading.value = true
  try {
    const params: Record<string, any> = { limit, offset: reset ? 0 : players.value.length }
    if (activePosition.value !== 'ALL') params.position = activePosition.value
    if (searchText.value.trim()) params.name = searchText.value.trim()
    const rows = await getAvailablePlayers(props.leagueId, props.draftYear, params)
    if (reset) {
      players.value = rows
    } else {
      players.value.push(...rows)
    }
  } finally {
    loading.value = false
  }
}

function loadMore() { load(false) }

function setPosition(pos: string) {
  activePosition.value = pos
  load()
}

watch(searchText, () => {
  if (_debounceTimer) clearTimeout(_debounceTimer)
  _debounceTimer = setTimeout(() => load(), 300)
})

// Reload when a pick is made (draftedIds changes)
watch(() => props.draftedIds.size, () => load())

onMounted(() => load())
</script>

<style scoped>
.avail-panel { display: flex; flex-direction: column; height: 100%; gap: 0.5rem; }
.pos-tabs { display: flex; gap: 0.25rem; flex-wrap: wrap; }
.pos-tab {
  padding: 0.25rem 0.6rem;
  border-radius: 0.25rem;
  border: 1px solid var(--color-border, #334155);
  background: var(--color-surface-alt, #1e293b);
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  transition: background 0.15s;
}
.pos-tab.active, .pos-tab:hover {
  background: var(--color-primary, #6366f1);
  border-color: var(--color-primary, #6366f1);
  color: #fff;
}
.search-row { flex-shrink: 0; }
.search-input {
  width: 100%;
  padding: 0.4rem 0.6rem;
  background: var(--color-surface-alt, #1e293b);
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.375rem;
  color: var(--color-text, #e2e8f0);
  font-size: 0.85rem;
}
.player-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.25rem; }
.state-msg { color: var(--color-text-muted, #94a3b8); padding: 0.5rem; font-size: 0.85rem; }
.player-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 0.5rem;
  background: var(--color-surface-alt, #1e293b);
  border-radius: 0.3rem;
  gap: 0.5rem;
}
.player-row.drafted { opacity: 0.4; }
.row-actions { display: flex; gap: 0.35rem; flex-shrink: 0; }
.btn-queue {
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid var(--color-border, #334155);
  background: transparent;
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-queue:hover { background: var(--color-surface, #0f172a); }
.btn-pick {
  padding: 0.2rem 0.6rem;
  border-radius: 0.25rem;
  background: var(--color-primary, #6366f1);
  color: #fff;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
}
.btn-pick:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-more {
  margin-top: 0.5rem;
  padding: 0.35rem;
  width: 100%;
  background: var(--color-surface, #0f172a);
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.25rem;
  color: var(--color-text-muted, #94a3b8);
  cursor: pointer;
  font-size: 0.8rem;
}
</style>
