<template>
  <span
    :class="[
      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
      colorClasses,
    ]"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple' | 'gray' | 'indigo'
  }>(),
  { color: 'gray' },
)

const colorClasses = computed(() => ({
  blue: 'bg-blue-500/20 text-blue-300',
  green: 'bg-green-500/20 text-green-300',
  red: 'bg-red-500/20 text-red-300',
  yellow: 'bg-yellow-500/20 text-yellow-300',
  purple: 'bg-purple-500/20 text-purple-300',
  gray: 'bg-gray-500/20 text-gray-300',
  indigo: 'bg-indigo-500/20 text-indigo-300',
}[props.color]))
</script>
