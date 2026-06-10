<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="$emit('update:modelValue', false)"
      >
        <div class="absolute inset-0 bg-black/60" />
        <div
          class="relative w-full max-w-lg rounded-xl shadow-xl p-6"
          style="background: var(--color-card); border: 1px solid var(--color-border)"
        >
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold" style="color: var(--color-text-primary)">
              <slot name="title" />
            </h2>
            <button
              class="p-1 rounded-lg transition-colors hover:bg-surface-hover"
              style="color: var(--color-text-secondary)"
              @click="$emit('update:modelValue', false)"
            >
              <X :size="18" />
            </button>
          </div>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { X } from '@lucide/vue'

defineProps<{ modelValue: boolean }>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
