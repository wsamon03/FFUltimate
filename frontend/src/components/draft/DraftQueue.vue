<template>
  <div class="queue-panel">
    <div class="queue-header">
      <span class="queue-title">My Queue</span>
      <button class="btn-save" :disabled="!dirty" @click="save">Save</button>
    </div>

    <div v-if="!queue.length" class="empty-msg">No players in queue.</div>

    <div v-for="(entry, idx) in queue" :key="entry.player_id" class="queue-row">
      <span class="q-num">{{ idx + 1 }}</span>
      <PlayerDraftCard :player="{ name: entry.player_name, position_code: entry.position_code, team_abbr: entry.team_abbr }" />
      <div class="q-actions">
        <button :disabled="idx === 0" @click="move(idx, -1)">↑</button>
        <button :disabled="idx === queue.length - 1" @click="move(idx, 1)">↓</button>
        <button class="btn-remove" @click="remove(idx)">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { getDraftQueue, setDraftQueue } from '@/api/leagues'
import PlayerDraftCard from './PlayerDraftCard.vue'

const props = defineProps<{
  leagueId: string
  teamId: string
  draftYear: number
}>()

const queue = ref<any[]>([])
const dirty = ref(false)

async function load() {
  queue.value = await getDraftQueue(props.leagueId, props.teamId, props.draftYear)
  dirty.value = false
}

function move(idx: number, dir: number) {
  const target = idx + dir
  if (target < 0 || target >= queue.value.length) return
  const tmp = queue.value[idx]
  queue.value[idx] = queue.value[target]
  queue.value[target] = tmp
  dirty.value = true
}

function remove(idx: number) {
  queue.value.splice(idx, 1)
  dirty.value = true
}

async function save() {
  await setDraftQueue(
    props.leagueId,
    props.teamId,
    props.draftYear,
    queue.value.map((e: any) => e.player_id),
  )
  dirty.value = false
}

defineExpose({
  addPlayer(player: any) {
    if (queue.value.find((e: any) => e.player_id === player.player_id)) return
    queue.value.push({
      player_id: player.player_id,
      player_name: player.name ?? player.player_name,
      position_code: player.position_code,
      team_abbr: player.team_abbr,
      priority: queue.value.length + 1,
    })
    dirty.value = true
  },
  reload: load,
})

load()
</script>

<style scoped>
.queue-panel { display: flex; flex-direction: column; gap: 0.35rem; }
.queue-header { display: flex; align-items: center; justify-content: space-between; }
.queue-title { font-weight: 700; font-size: 0.8rem; color: var(--color-text-muted, #94a3b8); }
.btn-save {
  padding: 0.15rem 0.5rem;
  background: var(--color-primary, #6366f1);
  color: #fff;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.75rem;
}
.btn-save:disabled { opacity: 0.4; cursor: not-allowed; }
.empty-msg { font-size: 0.8rem; color: var(--color-text-muted, #94a3b8); }
.queue-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.4rem;
  background: var(--color-surface-alt, #1e293b);
  border-radius: 0.25rem;
}
.q-num { font-size: 0.65rem; color: var(--color-text-muted, #94a3b8); min-width: 1rem; }
.q-actions { display: flex; gap: 0.2rem; margin-left: auto; flex-shrink: 0; }
.q-actions button {
  padding: 0.1rem 0.3rem;
  background: var(--color-surface, #0f172a);
  border: 1px solid var(--color-border, #334155);
  border-radius: 0.2rem;
  color: var(--color-text, #e2e8f0);
  cursor: pointer;
  font-size: 0.75rem;
  line-height: 1;
}
.q-actions button:disabled { opacity: 0.3; cursor: not-allowed; }
.btn-remove { color: #ef4444 !important; }
</style>
