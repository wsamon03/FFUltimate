<template>
  <div class="flex items-center justify-center" :class="fullPage ? 'min-h-64' : ''">
    <div
      class="rounded-full border-2 border-t-transparent animate-spin"
      :class="sizeClass"
      style="border-color: var(--color-primary); border-top-color: transparent"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{ size?: 'sm' | 'md' | 'lg'; fullPage?: boolean }>(),
  { size: 'md' },
)

const sizeClass = computed(() => ({ sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' }[props.size]))
</script>
