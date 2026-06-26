<template>
  <div class="player-draft-card">
    <span class="position-badge" :style="{ background: positionColor }">
      {{ player.position_code ?? '?' }}
    </span>
    <div class="player-info">
      <span class="player-name">{{ player.name ?? player.player_name }}</span>
      <span class="player-meta">{{ player.team_abbr ?? '—' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  player: {
    name?: string
    player_name?: string
    position_code?: string | null
    team_abbr?: string | null
  }
}>()

const POSITION_COLORS: Record<string, string> = {
  QB: '#ef4444',
  RB: '#22c55e',
  WR: '#3b82f6',
  TE: '#f59e0b',
  K: '#8b5cf6',
  DST: '#06b6d4',
  DEF: '#06b6d4',
}

const positionColor = computed(
  () => POSITION_COLORS[props.player.position_code ?? ''] ?? '#64748b',
)
</script>

<style scoped>
.player-draft-card {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.position-badge {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: 700;
  color: #fff;
  min-width: 2.4rem;
  text-align: center;
}
.player-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.player-name {
  font-weight: 600;
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.player-meta {
  font-size: 0.75rem;
  color: var(--color-text-muted, #94a3b8);
}
</style>
