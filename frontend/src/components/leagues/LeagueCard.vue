<template>
  <RouterLink :to="`/leagues/${league.id}`" class="block">
    <AppCard hoverable>
      <div class="flex items-start justify-between">
        <div class="flex-1 min-w-0">
          <div class="font-semibold truncate" style="color: var(--color-text-primary)">{{ league.name }}</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">
            {{ league.team_count || 0 }} teams · Created {{ formatDate(league.created_at) }}
          </div>
        </div>
        <ChevronRight :size="16" class="shrink-0 ml-2 mt-0.5" style="color: var(--color-text-secondary)" />
      </div>
      <div v-if="league.description" class="text-xs mt-2 line-clamp-2" style="color: var(--color-text-secondary)">
        {{ league.description }}
      </div>
    </AppCard>
  </RouterLink>
</template>

<script setup lang="ts">
import { ChevronRight } from '@lucide/vue'
import AppCard from '@/components/ui/AppCard.vue'

defineProps<{ league: any }>()

function formatDate(d?: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}
</script>
