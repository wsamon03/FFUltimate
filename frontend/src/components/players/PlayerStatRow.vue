<template>
  <tr>
    <!-- Total mode: colspan leading cells with "Total" label -->
    <template v-if="mode === 'total'">
      <td
        :colspan="leadingCols ?? 2"
        class="total-label-cell"
      >Total</td>
    </template>

    <!-- Career mode: clickable season year + teams -->
    <template v-else-if="mode === 'career'">
      <td>
        <button
          class="text-sm font-medium hover:underline"
          style="color: var(--color-primary)"
          @click="$emit('season-click', row.season_year)"
        >{{ row.season_year ?? '—' }}</button>
      </td>
      <td>
        <template v-if="row.team_abbrs && row.team_abbrs.length">
          <TeamHelmet v-for="abbr in row.team_abbrs" :key="abbr" :abbr="abbr" :size="20" />
        </template>
        <span v-else style="color: var(--color-text-secondary)">—</span>
      </td>
    </template>

    <!-- Season mode: week + player team + opponent -->
    <template v-else-if="mode === 'season'">
      <td style="color: var(--color-text-secondary)">{{ row.week ?? '—' }}</td>
      <td>
        <TeamHelmet v-if="row.player_team_abbr" :abbr="row.player_team_abbr" :size="20" />
        <span v-else style="color: var(--color-text-secondary)">—</span>
      </td>
      <td>
        <div class="flex items-center gap-1">
          <span style="color: var(--color-text-secondary); font-size: 0.75rem">{{ row.is_home ? 'vs.' : '@' }}</span>
          <img v-if="row.opponent_abbr" :src="`/helmets/${row.opponent_abbr}.png`" style="height: 20px; width: auto;" alt="" />
          <span style="font-size: 0.8rem">{{ row.opponent_abbr ?? '—' }}</span>
        </div>
      </td>
    </template>

    <!-- Range mode: season + week + player team + opponent -->
    <template v-else-if="mode === 'range'">
      <td style="color: var(--color-text-secondary)">{{ row.season_year ?? '—' }}</td>
      <td style="color: var(--color-text-secondary)">{{ row.week ?? '—' }}</td>
      <td>
        <TeamHelmet v-if="row.player_team_abbr" :abbr="row.player_team_abbr" :size="20" />
        <span v-else style="color: var(--color-text-secondary)">—</span>
      </td>
      <td>
        <div class="flex items-center gap-1">
          <span style="color: var(--color-text-secondary); font-size: 0.75rem">{{ row.is_home ? 'vs.' : '@' }}</span>
          <img v-if="row.opponent_abbr" :src="`/helmets/${row.opponent_abbr}.png`" style="height: 20px; width: auto;" alt="" />
          <span style="font-size: 0.8rem">{{ row.opponent_abbr ?? '—' }}</span>
        </div>
      </td>
    </template>

    <!-- Fantasy / default mode: season_year + week -->
    <template v-else>
      <td style="color: var(--color-text-secondary)">{{ row.season_year ?? row.season ?? '—' }}</td>
      <td style="color: var(--color-text-secondary)">{{ row.week ?? '—' }}</td>
    </template>

    <!-- Offense stats -->
    <template v-if="statType === 'offense' || !statType">
      <td :class="['col-pass', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.pass_comp ?? '—' }}</td>
      <td :class="['col-pass', { 'total-stat-cell': mode === 'total' }]">{{ row.pass_att ?? '—' }}</td>
      <td :class="['col-pass', { 'total-stat-cell': mode === 'total' }]">{{ row.pass_yds ?? '—' }}</td>
      <td :class="['col-pass', { 'total-stat-cell': mode === 'total' }]">{{ row.pass_td ?? '—' }}</td>
      <td :class="['col-pass', { 'total-stat-cell': mode === 'total' }]">{{ row.pass_int ?? '—' }}</td>
      <td :class="['col-pass', { 'total-stat-cell': mode === 'total' }]">{{ row.pass_qbr != null ? Number(row.pass_qbr).toFixed(1) : '—' }}</td>
      <td :class="['col-pass', { 'total-stat-cell': mode === 'total' }]">{{ row.pass_rating != null ? Number(row.pass_rating).toFixed(1) : '—' }}</td>
      <td :class="['col-rush', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.rush_att ?? '—' }}</td>
      <td :class="['col-rush', { 'total-stat-cell': mode === 'total' }]">{{ row.rush_yds ?? '—' }}</td>
      <td :class="['col-rush', { 'total-stat-cell': mode === 'total' }]">{{ row.rush_td ?? '—' }}</td>
      <td :class="['col-rush', { 'total-stat-cell': mode === 'total' }]">{{ row.rush_long ?? '—' }}</td>
      <td :class="['col-rec', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.rec_receptions ?? '—' }}</td>
      <td :class="['col-rec', { 'total-stat-cell': mode === 'total' }]">{{ row.rec_targets ?? '—' }}</td>
      <td :class="['col-rec', { 'total-stat-cell': mode === 'total' }]">{{ row.rec_yds ?? '—' }}</td>
      <td :class="['col-rec', { 'total-stat-cell': mode === 'total' }]">{{ row.rec_td ?? '—' }}</td>
      <td :class="['col-rec', { 'total-stat-cell': mode === 'total' }]">{{ row.rec_long ?? '—' }}</td>
      <td :class="['col-fum', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.fum_total ?? '—' }}</td>
      <td :class="['col-fum', { 'total-stat-cell': mode === 'total' }]">{{ row.fum_lost ?? '—' }}</td>
    </template>

    <!-- Defense stats -->
    <template v-else-if="statType === 'defense'">
      <td :class="['col-tkl', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.def_solo ?? '—' }}</td>
      <td :class="['col-tkl', { 'total-stat-cell': mode === 'total' }]">{{ row.def_ast ?? '—' }}</td>
      <td :class="['col-tkl', { 'total-stat-cell': mode === 'total' }]">{{ row.def_sacks ?? '—' }}</td>
      <td :class="['col-tkl', { 'total-stat-cell': mode === 'total' }]">{{ row.def_tfl ?? '—' }}</td>
      <td :class="['col-cov', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.def_pd ?? '—' }}</td>
      <td :class="['col-cov', { 'total-stat-cell': mode === 'total' }]">{{ row.def_qb_hits ?? '—' }}</td>
      <td :class="['col-to', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.def_int ?? '—' }}</td>
      <td :class="['col-to', { 'total-stat-cell': mode === 'total' }]">{{ row.def_int_yds ?? '—' }}</td>
      <td :class="['col-to', { 'total-stat-cell': mode === 'total' }]">{{ row.def_td ?? '—' }}</td>
    </template>

    <!-- Special teams stats -->
    <template v-else-if="statType === 'special'">
      <td :class="['col-kick', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.k_fg_make ?? '—' }}</td>
      <td :class="['col-kick', { 'total-stat-cell': mode === 'total' }]">{{ row.k_fg_att ?? '—' }}</td>
      <td :class="['col-kick', { 'total-stat-cell': mode === 'total' }]">{{ row.k_fg_long ?? '—' }}</td>
      <td :class="['col-kick', { 'total-stat-cell': mode === 'total' }]">{{ row.k_xp_make ?? '—' }}</td>
      <td :class="['col-kick', { 'total-stat-cell': mode === 'total' }]">{{ row.k_xp_att ?? '—' }}</td>
      <td :class="['col-punt', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.p_no ?? '—' }}</td>
      <td :class="['col-punt', { 'total-stat-cell': mode === 'total' }]">{{ row.p_yds ?? '—' }}</td>
      <td :class="['col-punt', { 'total-stat-cell': mode === 'total' }]">{{ row.p_in20 ?? '—' }}</td>
      <td :class="['col-punt', { 'total-stat-cell': mode === 'total' }]">{{ row.p_tb ?? '—' }}</td>
      <td :class="['col-punt', { 'total-stat-cell': mode === 'total' }]">{{ row.p_blk ?? '—' }}</td>
      <td :class="['col-punt', { 'total-stat-cell': mode === 'total' }]">{{ row.p_long ?? '—' }}</td>
      <td :class="['col-ret', 'col-divider', { 'total-stat-cell': mode === 'total' }]">{{ row.ret_kick_no ?? '—' }}</td>
      <td :class="['col-ret', { 'total-stat-cell': mode === 'total' }]">{{ row.ret_kick_yds ?? '—' }}</td>
      <td :class="['col-ret', { 'total-stat-cell': mode === 'total' }]">{{ row.ret_kick_td ?? '—' }}</td>
      <td :class="['col-ret', { 'total-stat-cell': mode === 'total' }]">{{ row.ret_kick_long ?? '—' }}</td>
      <td :class="['col-ret', { 'total-stat-cell': mode === 'total' }]">{{ row.ret_punt_no ?? '—' }}</td>
      <td :class="['col-ret', { 'total-stat-cell': mode === 'total' }]">{{ row.ret_punt_yds ?? '—' }}</td>
      <td :class="['col-ret', { 'total-stat-cell': mode === 'total' }]">{{ row.ret_punt_td ?? '—' }}</td>
      <td :class="['col-ret', { 'total-stat-cell': mode === 'total' }]">{{ row.ret_punt_long ?? '—' }}</td>
    </template>
  </tr>
</template>

<script setup lang="ts">
import TeamHelmet from '@/components/common/TeamHelmet.vue'

defineProps<{
  row: any
  statType?: string
  mode?: 'career' | 'season' | 'range' | 'fantasy' | 'total'
  leadingCols?: number
}>()

defineEmits<{ 'season-click': [year: number] }>()
</script>

<style scoped>
.total-label-cell {
  font-weight: bold;
  color: var(--color-text-primary);
  border-top: 2px solid var(--color-border);
}

.total-stat-cell {
  border-top: 2px solid var(--color-border);
}</style>
