<template>
  <tr>
    <td style="color: var(--color-text-secondary)">{{ row.season_year ?? row.season ?? '—' }}</td>
    <td v-if="showWeek" style="color: var(--color-text-secondary)">{{ row.week ?? '—' }}</td>

    <template v-if="positionGroup === 'QB'">
      <td>{{ row.pass_att ?? '—' }}</td>
      <td>{{ row.pass_comp ?? '—' }}</td>
      <td>{{ row.pass_yds ?? '—' }}</td>
      <td>{{ row.pass_td ?? '—' }}</td>
      <td>{{ row.pass_int ?? '—' }}</td>
      <td>{{ row.rush_yds ?? '—' }}</td>
      <td>{{ row.rush_td ?? '—' }}</td>
    </template>

    <template v-else-if="positionGroup === 'RB'">
      <td>{{ row.rush_att ?? '—' }}</td>
      <td>{{ row.rush_yds ?? '—' }}</td>
      <td>{{ row.rush_td ?? '—' }}</td>
      <td>{{ row.rec_receptions ?? '—' }}</td>
      <td>{{ row.rec_targets ?? '—' }}</td>
      <td>{{ row.rec_yds ?? '—' }}</td>
      <td>{{ row.rec_td ?? '—' }}</td>
    </template>

    <template v-else-if="positionGroup === 'WR'">
      <td>{{ row.rec_receptions ?? '—' }}</td>
      <td>{{ row.rec_targets ?? '—' }}</td>
      <td>{{ row.rec_yds ?? '—' }}</td>
      <td>{{ row.rec_td ?? '—' }}</td>
      <td>{{ row.rush_yds ?? '—' }}</td>
    </template>

    <template v-else-if="positionGroup === 'DEF'">
      <td>{{ row.def_solo ?? '—' }}</td>
      <td>{{ row.def_ast ?? '—' }}</td>
      <td>{{ row.def_sacks ?? '—' }}</td>
      <td>{{ row.def_tfl ?? '—' }}</td>
      <td>{{ row.def_pd ?? '—' }}</td>
      <td>{{ row.def_qb_hits ?? '—' }}</td>
      <td>{{ row.def_int ?? '—' }}</td>
      <td>{{ row.def_td ?? '—' }}</td>
    </template>

    <template v-else-if="positionGroup === 'K'">
      <td>{{ row.k_fg_make ?? '—' }}</td>
      <td>{{ row.k_fg_att ?? '—' }}</td>
      <td>{{ row.k_xp_make ?? '—' }}</td>
      <td>{{ row.k_xp_att ?? '—' }}</td>
    </template>

    <template v-else-if="positionGroup === 'P'">
      <td>{{ row.p_no ?? '—' }}</td>
      <td>{{ row.p_yds ?? '—' }}</td>
      <td>{{ row.p_in20 ?? '—' }}</td>
    </template>

    <template v-else>
      <td>{{ row.pass_yds ?? '—' }}</td>
      <td>{{ row.pass_td ?? '—' }}</td>
      <td>{{ row.rush_yds ?? '—' }}</td>
      <td>{{ row.rush_td ?? '—' }}</td>
      <td>{{ row.rec_receptions ?? '—' }}</td>
      <td>{{ row.rec_yds ?? '—' }}</td>
      <td>{{ row.rec_td ?? '—' }}</td>
    </template>
  </tr>
</template>

<script setup lang="ts">
defineProps<{ row: any; showWeek?: boolean; positionGroup?: string }>()
</script>
