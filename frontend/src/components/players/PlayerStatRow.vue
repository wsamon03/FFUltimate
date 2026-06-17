<template>
  <tr>
    <td style="color: var(--color-text-secondary)">{{ row.season_year ?? row.season ?? '—' }}</td>
    <td v-if="showWeek" style="color: var(--color-text-secondary)">{{ row.week ?? '—' }}</td>

    <!-- Offense stats -->
    <template v-if="statType === 'offense'">
      <td>{{ row.pass_comp ?? '—' }}</td>
      <td>{{ row.pass_att ?? '—' }}</td>
      <td>{{ row.pass_yds ?? '—' }}</td>
      <td>{{ row.pass_td ?? '—' }}</td>
      <td>{{ row.pass_int ?? '—' }}</td>
      <td>{{ row.rush_att ?? '—' }}</td>
      <td>{{ row.rush_yds ?? '—' }}</td>
      <td>{{ row.rush_td ?? '—' }}</td>
      <td>{{ row.rec_receptions ?? '—' }}</td>
      <td>{{ row.rec_targets ?? '—' }}</td>
      <td>{{ row.rec_yds ?? '—' }}</td>
      <td>{{ row.rec_td ?? '—' }}</td>
    </template>

    <!-- Defense stats -->
    <template v-else-if="statType === 'defense'">
      <td>{{ row.def_solo ?? '—' }}</td>
      <td>{{ row.def_ast ?? '—' }}</td>
      <td>{{ row.def_sacks ?? '—' }}</td>
      <td>{{ row.def_tfl ?? '—' }}</td>
      <td>{{ row.def_pd ?? '—' }}</td>
      <td>{{ row.def_qb_hits ?? '—' }}</td>
      <td>{{ row.def_int ?? '—' }}</td>
      <td>{{ row.def_td ?? '—' }}</td>
    </template>

    <!-- Special teams stats -->
    <template v-else-if="statType === 'special'">
      <td>{{ row.k_fg_make ?? '—' }}</td>
      <td>{{ row.k_fg_att ?? '—' }}</td>
      <td>{{ row.k_xp_make ?? '—' }}</td>
      <td>{{ row.k_xp_att ?? '—' }}</td>
      <td>{{ row.p_no ?? '—' }}</td>
      <td>{{ row.p_yds ?? '—' }}</td>
      <td>{{ row.p_in20 ?? '—' }}</td>
      <td>{{ row.p_tb ?? '—' }}</td>
      <td>{{ row.p_blk ?? '—' }}</td>
      <td>{{ row.p_long ?? '—' }}</td>
      <td>{{ row.ret_kick_no ?? '—' }}</td>
      <td>{{ row.ret_kick_yds ?? '—' }}</td>
      <td>{{ row.ret_kick_td ?? '—' }}</td>
      <td>{{ row.ret_punt_no ?? '—' }}</td>
      <td>{{ row.ret_punt_yds ?? '—' }}</td>
      <td>{{ row.ret_punt_td ?? '—' }}</td>
    </template>
  </tr>
</template>

<script setup lang="ts">
defineProps<{ row: any; showWeek?: boolean; statType?: string }>()
</script>
