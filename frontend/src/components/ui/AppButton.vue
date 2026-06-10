<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[
      'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
      sizeClasses,
      variantClasses,
    ]"
    v-bind="$attrs"
  >
    <span v-if="loading" class="mr-2 w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'ghost' | 'danger' | 'secondary'
    size?: 'sm' | 'md' | 'lg'
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
    loading?: boolean
  }>(),
  { variant: 'primary', size: 'md', type: 'button' },
)

const sizeClasses = computed(() => ({
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2 text-sm gap-2',
  lg: 'px-5 py-2.5 text-base gap-2',
}[props.size]))

const variantClasses = computed(() => ({
  primary: 'bg-primary text-white hover:bg-primary-hover focus:ring-primary/50',
  secondary: 'bg-surface-card text-text-primary border border-border hover:bg-surface-hover focus:ring-border',
  ghost: 'bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-hover focus:ring-border',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500/50',
}[props.variant]))
</script>
