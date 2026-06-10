<template>
  <div class="space-y-3">
    <!-- Mode tabs -->
    <div class="flex flex-wrap gap-1">
      <button
        v-for="mode in MODES"
        :key="mode.value"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
        :style="activeMode === mode.value
          ? `background: var(--color-primary); color: white`
          : `background: var(--color-card); color: var(--color-text-secondary); border: 1px solid var(--color-border)`"
        @click="activeMode = mode.value"
      >
        {{ mode.label }}
      </button>
    </div>

    <!-- Controls for modes that need inputs -->
    <div class="flex flex-wrap gap-3 items-end" v-if="activeMode !== 'career'">
      <!-- Season year dropdown (all modes except career) -->
      <div class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">
          {{ activeMode === 'range' ? 'Start Year' : 'Season Year' }}
        </label>
        <input
          v-model.number="startYear"
          type="number" min="2000" :max="currentYear"
          class="w-24 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
          style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
        />
      </div>

      <!-- Week (by_week mode only) -->
      <div v-if="activeMode === 'by_week'" class="flex flex-col gap-1">
        <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Week</label>
        <input
          v-model.number="startWeek"
          type="number" min="1" max="22"
          class="w-20 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
          style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
        />
      </div>

      <!-- End year + week for range mode -->
      <template v-if="activeMode === 'range'">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium" style="color: var(--color-text-secondary)">Start Week</label>
          <input
            v-model.number="startWeek"
            type="number" min="1" max="22"
            class="w-20 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
            style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium" style="color: var(--color-text-secondary)">End Year</label>
          <input
            v-model.number="endYear"
            type="number" min="2000" :max="currentYear"
            class="w-24 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
            style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium" style="color: var(--color-text-secondary)">End Week</label>
          <input
            v-model.number="endWeek"
            type="number" min="1" max="22"
            class="w-20 text-sm rounded-lg px-3 py-1.5 border focus:outline-none focus:ring-2"
            style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

export type StatMode = 'career' | 'full_season' | 'by_year' | 'by_week' | 'range'

export interface StatFilter {
  mode: StatMode
  startYear?: number
  startWeek?: number
  endYear?: number
  endWeek?: number
}

const MODES: { value: StatMode; label: string }[] = [
  { value: 'career',      label: 'Career' },
  { value: 'full_season', label: 'Full Season' },
  { value: 'by_year',     label: 'By Year' },
  { value: 'by_week',     label: 'By Week' },
  { value: 'range',       label: 'Range' },
]

const currentYear = new Date().getFullYear()

const activeMode = ref<StatMode>('career')
const startYear  = ref(currentYear)
const startWeek  = ref(1)
const endYear    = ref(currentYear)
const endWeek    = ref(18)

const emit = defineEmits<{ change: [filter: StatFilter] }>()

watch([activeMode, startYear, startWeek, endYear, endWeek], () => {
  emit('change', {
    mode:      activeMode.value,
    startYear: startYear.value,
    startWeek: startWeek.value,
    endYear:   endYear.value,
    endWeek:   endWeek.value,
  })
}, { immediate: true })
</script>
