<template>
  <tr>
    <td style="color: var(--color-text-secondary)">{{ row.season_year ?? row.season ?? '—' }}</td>
    <td v-if="showWeek" style="color: var(--color-text-secondary)">{{ row.week ?? '—' }}</td>
    <td style="color: var(--color-text-primary)">{{ row.pass_yards ?? '—' }}</td>
    <td style="color: var(--color-text-primary)">{{ row.pass_tds ?? '—' }}</td>
    <td style="color: var(--color-text-primary)">{{ row.rush_yards ?? '—' }}</td>
    <td style="color: var(--color-text-primary)">{{ row.rush_tds ?? '—' }}</td>
    <td style="color: var(--color-text-primary)">{{ row.rec_yards ?? '—' }}</td>
    <td style="color: var(--color-text-primary)">{{ row.receptions ?? '—' }}</td>
    <td style="color: var(--color-text-primary)">{{ row.rec_tds ?? '—' }}</td>
  </tr>
</template>

<script setup lang="ts">
defineProps<{ row: any; showWeek?: boolean }>()
</script>
