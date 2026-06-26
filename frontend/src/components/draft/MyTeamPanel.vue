<template>
  <div class="my-team-panel">
    <h3 class="panel-title">My Team</h3>

    <div class="picks-list">
      <template v-if="myPicks.length">
        <div v-for="pick in myPicks" :key="pick.pick_number" class="pick-row">
          <span class="round-label">R{{ pick.round_number }}</span>
          <PlayerDraftCard
            :player="{
              name: pick.player_name,
              position_code: pick.position_code,
              team_abbr: pick.team_abbr,
            }"
          />
        </div>
      </template>
      <div v-else class="empty-msg">No picks yet.</div>
    </div>

    <div class="queue-section">
      <DraftQueue
        ref="queueRef"
        :league-id="leagueId"
        :team-id="teamId"
        :draft-year="draftYear"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import PlayerDraftCard from './PlayerDraftCard.vue'
import DraftQueue from './DraftQueue.vue'

const props = defineProps<{
  picks: any[]
  teamId: string
  leagueId: string
  draftYear: number
}>()

const queueRef = ref<InstanceType<typeof DraftQueue> | null>(null)

const myPicks = computed(() =>
  props.picks
    .filter((p: any) => p.league_team_id === props.teamId && !!p.player_id)
    .sort((a: any, b: any) => a.pick_number - b.pick_number),
)

defineExpose({
  addToQueue(player: any) {
    queueRef.value?.addPlayer(player)
  },
})
</script>

<style scoped>
.my-team-panel { display: flex; flex-direction: column; height: 100%; gap: 0.5rem; overflow: hidden; }
.panel-title { font-weight: 700; font-size: 0.9rem; margin: 0; }
.picks-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 0.25rem; }
.empty-msg { font-size: 0.85rem; color: var(--color-text-muted, #94a3b8); padding: 0.5rem 0; }
.pick-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.5rem;
  background: var(--color-surface-alt, #1e293b);
  border-radius: 0.3rem;
}
.round-label { font-size: 0.65rem; color: var(--color-text-muted, #94a3b8); min-width: 1.6rem; }
.queue-section { flex-shrink: 0; border-top: 1px solid var(--color-border, #334155); padding-top: 0.5rem; max-height: 40%; overflow-y: auto; }
</style>
