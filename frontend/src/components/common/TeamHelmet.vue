<template>
  <img
    v-if="!imgError"
    :src="`/helmets/${normalizedAbbr}.png`"
    :alt="abbr"
    :width="size"
    :height="size"
    :style="`width: ${size}px; height: ${size}px; object-fit: contain;`"
    @error="imgError = true"
  />
  <span
    v-else
    :style="`display:inline-flex;align-items:center;justify-content:center;width:${size}px;height:${size}px;background:var(--color-primary);color:#fff;font-size:${Math.max(8, size * 0.35)}px;font-weight:700;border-radius:4px;`"
  >{{ abbr }}</span>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(defineProps<{ abbr: string; size?: number }>(), { size: 32 })
const imgError = ref(false)
const normalizedAbbr = computed(() => (props.abbr || '').toLowerCase())
</script>
