<template>
  <div class="order-setup">
    <h3 class="title">Set Draft Order</h3>

    <div class="team-list">
      <div v-for="(team, idx) in localOrder" :key="team.id" class="team-row">
        <span class="slot-num">{{ idx + 1 }}</span>
        <span class="team-name">{{ team.name }}</span>
        <div class="actions">
          <button :disabled="idx === 0" @click="move(idx, -1)">↑</button>
          <button :disabled="idx === localOrder.length - 1" @click="move(idx, 1)">↓</button>
        </div>
      </div>
    </div>

    <div class="btn-row">
      <button class="btn-rand" :disabled="loading" @click="randomize">Randomize</button>
      <button class="btn-save" :disabled="loading" @click="save">Save Order</button>
    </div>

    <p v-if="error" class="error-msg">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { randomizeDraftOrder, setDraftOrder } from '@/api/leagues'

const props = defineProps<{
  leagueId: string
  draftYear: number
  teams: Array<{ id: string; name: string }>
}>()

const emit = defineEmits<{ (e: 'updated'): void }>()

const localOrder = ref<Array<{ id: string; name: string }>>(props.teams.map((t) => ({ ...t })))
const loading = ref(false)
const error = ref('')

watch(
  () => props.teams,
  (t) => { localOrder.value = t.map((x) => ({ ...x })) },
)

function move(idx: number, dir: number) {
  const target = idx + dir
  if (target < 0 || target >= localOrder.value.length) return
  const tmp = localOrder.value[idx]
  localOrder.value[idx] = localOrder.value[target]
  localOrder.value[target] = tmp
}

async function randomize() {
  loading.value = true
  error.value = ''
  try {
    const result = await randomizeDraftOrder(props.leagueId, props.draftYear)
    // result is list[DraftOrderEntry]; rebuild local from it
    const sorted = [...result].sort((a: any, b: any) => a.slot_position - b.slot_position)
    localOrder.value = sorted.map((e: any) => ({
      id: e.league_team_id,
      name: e.team_name,
    }))
    emit('updated')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to randomize'
  } finally {
    loading.value = false
  }
}

async function save() {
  loading.value = true
  error.value = ''
  try {
    await setDraftOrder(
      props.leagueId,
      props.draftYear,
      localOrder.value.map((t) => t.id),
    )
    emit('updated')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Failed to save'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.order-setup { display: flex; flex-direction: column; gap: 0.75rem; }
.title { font-weight: 700; font-size: 1rem; margin: 0; }
.team-list { display: flex; flex-direction: column; gap: 0.3rem; }
.team-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.6rem;
  background: var(--color-surface-alt, #1e293b);
  border-radius: 0.3rem;
}
.slot-num { font-size: 0.8rem; font-weight: 700; color: var(--color-text-muted, #94a3b8); min-width: 1.2rem; }
.team-name { flex: 1; font-size: 0.875rem; }
.actions { display: flex; gap: 0.25rem; }
.actions button {
  padding: 0.15rem 0.4rem;
  background: var(--color-surface, #0f172a);
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.2rem;
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  font-size: 0.8rem;
}
.actions button:disabled { opacity: 0.3; cursor: not-allowed; }
.btn-row { display: flex; gap: 0.5rem; }
.btn-rand, .btn-save {
  padding: 0.4rem 1rem;
  border-radius: 0.375rem;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
}
.btn-rand {
  background: var(--color-surface-alt, #1e293b);
  color: var(--color-text, #e2e8f0);
  border: 1px solid var(--color-border, #334155);
}
.btn-save {
  background: var(--color-primary, #6366f1);
  color: #fff;
}
.error-msg { color: #ef4444; font-size: 0.85rem; }
</style>
