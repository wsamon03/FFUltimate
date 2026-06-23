<template>
  <div class="flex items-center justify-between gap-6 py-4 px-1">
    <!-- Left: showing X-Y of Z results -->
    <div class="text-sm" style="color: var(--color-text-secondary)">
      Showing {{ start }}–{{ end }} of {{ total }} results
    </div>

    <!-- Right: controls -->
    <div class="flex items-center gap-4">
      <!-- Preset buttons + custom input -->
      <div class="flex items-center gap-2">
        <div class="flex gap-1">
          <button
            v-for="preset in [10, 20, 50, 100]"
            :key="preset"
            class="px-3 py-1.5 rounded text-sm font-medium transition-colors"
            :style="perPage === preset
              ? 'background: var(--color-primary); color: white'
              : 'background: var(--color-card); color: var(--color-text-secondary); border: 1px solid var(--color-border)'"
            @click="$emit('update:perPage', preset)"
          >
            {{ preset }}
          </button>
        </div>
        <input
          :value="customPageSizeInput"
          type="number"
          min="1"
          :max="total"
          placeholder="Custom"
          class="w-20 px-2 py-1.5 rounded text-sm border focus:outline-none focus:ring-2"
          style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          @input="customPageSizeInput = ($event.target as HTMLInputElement).value"
          @blur="handleCustomPageSize"
          @keyup.enter="handleCustomPageSize"
          title="Enter a custom number of results per page"
        />
      </div>

      <!-- Page navigation -->
      <div class="flex items-center gap-3">
        <button
          :disabled="page === 1"
          class="w-8 h-8 flex items-center justify-center rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :style="page === 1
            ? 'color: var(--color-text-secondary)'
            : 'color: var(--color-primary); cursor: pointer; background: var(--color-card)'"
          @click="$emit('update:page', page - 1)"
        >
          ‹
        </button>
        <div class="flex items-center gap-1">
          <span class="text-sm" style="color: var(--color-text-secondary)">Page</span>
          <input
            :value="pageInput"
            type="number"
            min="1"
            :max="totalPages"
            class="w-12 px-2 py-1.5 rounded text-sm border focus:outline-none focus:ring-2 text-center"
            style="background: var(--color-card); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
            @input="pageInput = ($event.target as HTMLInputElement).value"
            @keyup.enter="jumpToPage"
            @blur="jumpToPage"
          />
          <span class="text-sm" style="color: var(--color-text-secondary)">of {{ totalPages }}</span>
        </div>
        <button
          :disabled="page === totalPages"
          class="w-8 h-8 flex items-center justify-center rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :style="page === totalPages
            ? 'color: var(--color-text-secondary)'
            : 'color: var(--color-primary); cursor: pointer; background: var(--color-card)'"
          @click="$emit('update:page', page + 1)"
        >
          ›
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  total: number
  page: number
  perPage: number
}>()

const emit = defineEmits<{
  'update:page': [page: number]
  'update:perPage': [perPage: number]
}>()

const pageInput = ref(String(props.page))
const customPageSizeInput = ref('')

const totalPages = computed(() => Math.ceil(props.total / props.perPage) || 1)

const start = computed(() => props.total === 0 ? 0 : (props.page - 1) * props.perPage + 1)

const end = computed(() => Math.min(props.page * props.perPage, props.total))

const isPreset = computed(() => [10, 20, 50, 100].includes(props.perPage))

watch(() => props.page, (newPage) => {
  pageInput.value = String(newPage)
})

function handleCustomPageSize() {
  let val = parseInt(customPageSizeInput.value, 10)
  if (isNaN(val) || val < 1) val = 1
  if (val > props.total) val = props.total
  if (val !== props.perPage) {
    emit('update:perPage', val)
    customPageSizeInput.value = ''
  }
}

function jumpToPage() {
  let val = parseInt(pageInput.value, 10)
  if (isNaN(val) || val < 1) val = 1
  if (val > totalPages.value) val = totalPages.value
  if (val !== props.page) {
    emit('update:page', val)
  } else {
    pageInput.value = String(val)
  }
}
</script>
