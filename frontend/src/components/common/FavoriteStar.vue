<template>
  <button
    :disabled="loading"
    class="p-1 rounded-md transition-all disabled:opacity-40 hover:scale-110"
    :title="isFavorited ? 'Remove from favorites' : 'Add to favorites'"
    @click.prevent.stop="$emit('toggle')"
  >
    <Star
      :size="size"
      :fill="isFavorited ? 'currentColor' : 'none'"
      :style="isFavorited ? 'color: var(--color-primary)' : 'color: var(--color-text-secondary)'"
    />
  </button>
</template>

<script setup lang="ts">
import { Star } from '@lucide/vue'

withDefaults(
  defineProps<{ isFavorited: boolean; loading?: boolean; size?: number }>(),
  { size: 18 },
)

defineEmits<{ toggle: [] }>()
</script>
