<template>
  <tr>
    <!-- Career mode: clickable season year -->
    <template v-if="mode === 'career'">
      <td>
        <button
          class="text-sm font-medium hover:underline"
          style="color: var(--color-primary)"
          @click="$emit('season-click', row.season_year)"
        >{{ row.season_year ?? '—' }}</button>
      </td>
    </template>

    <!-- Season mode: week + opponent -->
    <template v-else-if="mode === 'season'">
      <td style="color: var(--color-text-secondary)">{{ row.week ?? '—' }}</td>
      <td>
        <div class="flex items-center gap-1">
          <span style="color: var(--color-text-secondary); font-size: 0.75rem">{{ row.is_home ? 'vs.' : '@' }}</span>
          <img v-if="row.opponent_abbr" :src="`/helmets/${row.opponent_abbr}.png`" style="height: 20px; width: auto;" alt="" />
          <span style="font-size: 0.8rem">{{ row.opponent_abbr ?? '—' }}</span>
        </div>
      </td>
    </template>

    <!-- Range mode: season + week + opponent -->
    <template v-else-if="mode === 'range'">
      <td style="color: var(--color-text-secondary)">{{ row.season_year ?? '—' }}</td>
      <td style="color: var(--color-text-secondary)">{{ row.week ?? '—' }}</td>
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
      <td class="col-pass col-divider">{{ row.pass_comp ?? '—' }}</td>
      <td class="col-pass">{{ row.pass_att ?? '—' }}</td>
      <td class="col-pass">{{ row.pass_yds ?? '—' }}</td>
      <td class="col-pass">{{ row.pass_td ?? '—' }}</td>
      <td class="col-pass">{{ row.pass_int ?? '—' }}</td>
      <td class="col-pass">{{ row.pass_qbr != null ? Number(row.pass_qbr).toFixed(1) : '—' }}</td>
      <td class="col-pass">{{ row.pass_rating != null ? Number(row.pass_rating).toFixed(1) : '—' }}</td>
      <td class="col-rush col-divider">{{ row.rush_att ?? '—' }}</td>
      <td class="col-rush">{{ row.rush_yds ?? '—' }}</td>
      <td class="col-rush">{{ row.rush_td ?? '—' }}</td>
      <td class="col-rush">{{ row.rush_long ?? '—' }}</td>
      <td class="col-rec col-divider">{{ row.rec_receptions ?? '—' }}</td>
      <td class="col-rec">{{ row.rec_targets ?? '—' }}</td>
      <td class="col-rec">{{ row.rec_yds ?? '—' }}</td>
      <td class="col-rec">{{ row.rec_td ?? '—' }}</td>
      <td class="col-rec">{{ row.rec_long ?? '—' }}</td>
      <td class="col-fum col-divider">{{ row.fum_total ?? '—' }}</td>
      <td class="col-fum">{{ row.fum_lost ?? '—' }}</td>
    </template>

    <!-- Defense stats -->
    <template v-else-if="statType === 'defense'">
      <td class="col-tkl col-divider">{{ row.def_solo ?? '—' }}</td>
      <td class="col-tkl">{{ row.def_ast ?? '—' }}</td>
      <td class="col-tkl">{{ row.def_sacks ?? '—' }}</td>
      <td class="col-tkl">{{ row.def_tfl ?? '—' }}</td>
      <td class="col-cov col-divider">{{ row.def_pd ?? '—' }}</td>
      <td class="col-cov">{{ row.def_qb_hits ?? '—' }}</td>
      <td class="col-to col-divider">{{ row.def_int ?? '—' }}</td>
      <td class="col-to">{{ row.def_int_yds ?? '—' }}</td>
      <td class="col-to">{{ row.def_td ?? '—' }}</td>
    </template>

    <!-- Special teams stats -->
    <template v-else-if="statType === 'special'">
      <td class="col-kick col-divider">{{ row.k_fg_make ?? '—' }}</td>
      <td class="col-kick">{{ row.k_fg_att ?? '—' }}</td>
      <td class="col-kick">{{ row.k_fg_long ?? '—' }}</td>
      <td class="col-kick">{{ row.k_xp_make ?? '—' }}</td>
      <td class="col-kick">{{ row.k_xp_att ?? '—' }}</td>
      <td class="col-punt col-divider">{{ row.p_no ?? '—' }}</td>
      <td class="col-punt">{{ row.p_yds ?? '—' }}</td>
      <td class="col-punt">{{ row.p_in20 ?? '—' }}</td>
      <td class="col-punt">{{ row.p_tb ?? '—' }}</td>
      <td class="col-punt">{{ row.p_blk ?? '—' }}</td>
      <td class="col-punt">{{ row.p_long ?? '—' }}</td>
      <td class="col-ret col-divider">{{ row.ret_kick_no ?? '—' }}</td>
      <td class="col-ret">{{ row.ret_kick_yds ?? '—' }}</td>
      <td class="col-ret">{{ row.ret_kick_td ?? '—' }}</td>
      <td class="col-ret">{{ row.ret_kick_long ?? '—' }}</td>
      <td class="col-ret">{{ row.ret_punt_no ?? '—' }}</td>
      <td class="col-ret">{{ row.ret_punt_yds ?? '—' }}</td>
      <td class="col-ret">{{ row.ret_punt_td ?? '—' }}</td>
      <td class="col-ret">{{ row.ret_punt_long ?? '—' }}</td>
    </template>
  </tr>
</template>

<script setup lang="ts">
defineProps<{
  row: any
  statType?: string
  mode?: 'career' | 'season' | 'range' | 'fantasy'
}>()

defineEmits<{ 'season-click': [year: number] }>()
</script>
