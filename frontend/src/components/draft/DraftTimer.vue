<template>
  <div
    class="draft-timer"
    :class="{ 'is-my-turn': isMyTurn, 'is-urgent': secondsLeft <= 15 && secondsLeft > 0 }"
  >
    <span class="timer-value">{{ display }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  secondsLeft: number
  isMyTurn: boolean
}>()

const display = computed(() => {
  const s = Math.max(0, props.secondsLeft)
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${sec.toString().padStart(2, '0')}`
})
</script>

<style scoped>
.draft-timer {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 4rem;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  background: var(--color-surface-alt, #1e293b);
  border: 2px solid transparent;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--color-text, #e2e8f0);
  transition: border-color 0.2s, color 0.2s;
}
.draft-timer.is-my-turn {
  border-color: var(--color-primary, #6366f1);
  color: var(--color-primary, #6366f1);
}
.draft-timer.is-urgent {
  border-color: #ef4444;
  color: #ef4444;
  animation: pulse-border 0.8s ease-in-out infinite;
}
@keyframes pulse-border {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
