<template>
  <div class="flex flex-col items-center justify-center py-16 text-center px-4">
    <component :is="icon" :size="48" class="mb-4 opacity-30" style="color: var(--color-text-secondary)" />
    <p class="text-lg font-medium mb-1" style="color: var(--color-text-primary)">{{ title }}</p>
    <p v-if="message" class="text-sm max-w-xs" style="color: var(--color-text-secondary)">{{ message }}</p>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { Inbox } from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    icon?: object
    title: string
    message?: string
  }>(),
  { icon: () => Inbox },
)
</script>
