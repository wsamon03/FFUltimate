<template>
  <div
    :class="[
      'rounded-xl border p-4 md:p-6',
      hoverable ? 'transition-colors cursor-pointer hover:bg-surface-hover' : '',
    ]"
    style="background:var(--color-card); border-color:var(--color-border)"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ hoverable?: boolean }>()
</script>
