<template>
  <div class="relative">
    <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
      style="color: var(--color-text-secondary)" />
    <input
      :value="modelValue"
      :placeholder="placeholder"
      type="text"
      class="w-full pl-9 pr-8 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2"
      style="
        background: var(--color-card);
        border-color: var(--color-border);
        color: var(--color-text-primary);
        --tw-ring-color: var(--color-primary);
      "
      @input="onInput"
    />
    <button
      v-if="modelValue"
      class="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded transition-colors hover:bg-surface-hover"
      style="color: var(--color-text-secondary)"
      @click="$emit('update:modelValue', '')"
    >
      <X :size="14" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { Search, X } from '@lucide/vue'
import { useDebounceFn } from '@vueuse/core'

const props = withDefaults(
  defineProps<{ modelValue: string; placeholder?: string; debounce?: number }>(),
  { placeholder: 'Search…', debounce: 300 },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const onInput = useDebounceFn((e: Event) => {
  emit('update:modelValue', (e.target as HTMLInputElement).value)
}, props.debounce)
</script>
