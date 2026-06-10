<template>
  <span
    class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold"
    :style="style"
  >
    {{ position }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ position: string }>()

const colorMap: Record<string, { bg: string; text: string }> = {
  QB:  { bg: '#ef4444', text: '#fff' },
  RB:  { bg: '#22c55e', text: '#fff' },
  WR:  { bg: '#3b82f6', text: '#fff' },
  TE:  { bg: '#f59e0b', text: '#fff' },
  K:   { bg: '#8b5cf6', text: '#fff' },
  DEF: { bg: '#6b7280', text: '#fff' },
  DB:  { bg: '#0ea5e9', text: '#fff' },
  LB:  { bg: '#14b8a6', text: '#fff' },
  DL:  { bg: '#64748b', text: '#fff' },
  OL:  { bg: '#78716c', text: '#fff' },
}

const style = computed(() => {
  const c = colorMap[props.position.toUpperCase()] ?? { bg: '#475569', text: '#fff' }
  return `background: ${c.bg}; color: ${c.text}`
})
</script>
