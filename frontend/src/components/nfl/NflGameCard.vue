<template>
  <RouterLink :to="`/nfl/games/${game.id}`" class="block">
    <AppCard hoverable>
      <div class="flex items-center justify-between text-xs mb-3" style="color: var(--color-text-secondary)">
        <span>{{ formatDate(game.game_date) }}</span>
        <AppBadge :color="statusColor">{{ game.status_code || 'TBD' }}</AppBadge>
      </div>

      <div class="flex items-center justify-between gap-2">
        <!-- Away team -->
        <div class="flex-1 text-center">
          <div class="text-lg font-bold" style="color: var(--color-text-primary)">{{ game.away_team_abbr }}</div>
          <div class="text-2xl font-bold mt-1" style="color: var(--color-text-primary)">
            {{ game.away_score ?? '—' }}
          </div>
        </div>

        <div class="text-xs font-medium px-2" style="color: var(--color-text-secondary)">@</div>

        <!-- Home team -->
        <div class="flex-1 text-center">
          <div class="text-lg font-bold" style="color: var(--color-text-primary)">{{ game.home_team_abbr }}</div>
          <div class="text-2xl font-bold mt-1" style="color: var(--color-text-primary)">
            {{ game.home_score ?? '—' }}
          </div>
        </div>
      </div>
    </AppCard>
  </RouterLink>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppBadge from '@/components/ui/AppBadge.vue'

const props = defineProps<{ game: any }>()

const statusColor = computed(() => {
  const s = (props.game.status_code || '').toLowerCase()
  if (s === 'final' || s === 'ft') return 'gray'
  if (s === 'live' || s === 'in progress') return 'green'
  return 'blue'
})

function formatDate(d?: string) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
</script>
