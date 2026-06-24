<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <AppSpinner v-if="loading" fullPage />

    <template v-else-if="league">
      <!-- Header -->
      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">{{ league.name }}</h1>
          <p v-if="league.description" class="text-sm mt-1" style="color: var(--color-text-secondary)">{{ league.description }}</p>
          <div class="flex flex-wrap gap-3 mt-2 text-xs" style="color: var(--color-text-secondary)">
            <span>{{ league.league_type_name }}</span>
            <span>·</span>
            <span>{{ league.season_year }} Season</span>
            <span>·</span>
            <span>{{ league.max_teams }} teams max</span>
            <span>·</span>
            <span>{{ league.available_scope_name }}</span>
          </div>
        </div>
        <AppButton v-if="activeTab === 'teams'" @click="showAddTeam = true">Add Team</AppButton>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 border-b" style="border-color: var(--color-border)">
        <button
          v-for="tab in ['teams', 'standings', 'settings']"
          :key="tab"
          class="px-4 py-2 text-sm font-medium capitalize border-b-2 -mb-px transition-colors"
          :style="activeTab === tab
            ? 'border-color: var(--color-primary); color: var(--color-primary)'
            : 'border-color: transparent; color: var(--color-text-secondary)'"
          @click="handleTabChange(tab)"
        >{{ tab }}</button>
      </div>

      <!-- Teams tab -->
      <div v-if="activeTab === 'teams'">
        <div v-if="teams.length === 0">
          <AppEmptyState title="No teams yet" message="Add the first team to this league." />
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="team in teams" :key="team.id" class="relative group">
            <RouterLink :to="`/leagues/${leagueId}/teams/${team.id}`">
              <AppCard hoverable>
                <div class="flex items-center gap-3">
                  <div
                    class="w-10 h-10 rounded-full flex-shrink-0 border"
                    :style="team.primary_color
                      ? `background: ${team.primary_color}; border-color: ${team.primary_color}`
                      : 'border-color: var(--color-border); background: var(--color-bg-secondary)'"
                  ></div>
                  <div class="flex-1 min-w-0">
                    <div class="font-semibold" style="color: var(--color-text-primary)">
                      {{ team.name }}
                      <span v-if="team.abbreviation" class="text-xs font-normal ml-1" style="color: var(--color-text-secondary)">({{ team.abbreviation }})</span>
                    </div>
                    <div class="text-xs mt-0.5" style="color: var(--color-text-secondary)">{{ team.owner_count || 0 }} owner(s)</div>
                    <div v-if="team.slogan" class="text-xs italic mt-0.5 truncate" style="color: var(--color-text-secondary)">{{ team.slogan }}</div>
                  </div>
                  <ChevronRight :size="16" style="color: var(--color-text-secondary)" />
                </div>
              </AppCard>
            </RouterLink>
            <button
              v-if="isCommissioner"
              class="absolute top-3 right-10 p-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity"
              style="color: var(--color-text-secondary); background: var(--color-bg-secondary)"
              title="Edit branding"
              @click="openBrandingEdit(team)"
            >
              <Pencil :size="13" />
            </button>
          </div>
        </div>
      </div>

      <!-- Standings tab -->
      <div v-else-if="activeTab === 'standings'" class="space-y-4">
        <AppSpinner v-if="loadingStandings" />
        <AppEmptyState
          v-else-if="standings.length === 0"
          title="No standings yet"
          message="Standings are computed from completed matchups."
        />
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs uppercase tracking-wide border-b" style="color: var(--color-text-secondary); border-color: var(--color-border)">
                <th class="pb-2 pr-3 font-medium">#</th>
                <th class="pb-2 pr-6 font-medium">Team</th>
                <th class="pb-2 px-2 text-center font-medium">W</th>
                <th class="pb-2 px-2 text-center font-medium">L</th>
                <th class="pb-2 px-2 text-center font-medium">T</th>
                <th class="pb-2 px-2 text-center font-medium">Win%</th>
                <th class="pb-2 px-2 text-right font-medium">PF</th>
                <th class="pb-2 px-2 text-right font-medium">PA</th>
                <th class="pb-2 px-2 text-right font-medium">Diff</th>
                <th class="pb-2 px-2 text-center font-medium">Streak</th>
                <th class="pb-2 px-2 text-center font-medium">All-Play</th>
                <th class="pb-2 px-2 text-center font-medium">GB</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(entry, idx) in standings"
                :key="entry.team_id"
                class="border-b transition-colors hover:bg-opacity-50"
                style="border-color: var(--color-border)"
              >
                <td class="py-3 pr-3 font-medium" style="color: var(--color-text-secondary)">{{ idx + 1 }}</td>
                <td class="py-3 pr-6">
                  <div class="flex items-center gap-2">
                    <div
                      class="w-3 h-3 rounded-full flex-shrink-0"
                      :style="entry.primary_color ? `background: ${entry.primary_color}` : 'background: var(--color-border)'"
                    ></div>
                    <div>
                      <RouterLink
                        :to="`/leagues/${leagueId}/teams/${entry.team_id}`"
                        class="font-semibold hover:underline"
                        style="color: var(--color-text-primary)"
                      >
                        {{ entry.abbreviation || entry.team_name }}
                      </RouterLink>
                      <span v-if="entry.is_eliminated" class="ml-1.5 text-xs px-1 rounded" style="background: #fee2e2; color: #dc2626">OUT</span>
                    </div>
                  </div>
                  <div v-if="entry.abbreviation" class="text-xs mt-0.5 ml-5" style="color: var(--color-text-secondary)">{{ entry.team_name }}</div>
                </td>
                <td class="py-3 px-2 text-center font-semibold" style="color: var(--color-text-primary)">{{ entry.wins }}</td>
                <td class="py-3 px-2 text-center" style="color: var(--color-text-primary)">{{ entry.losses }}</td>
                <td class="py-3 px-2 text-center" style="color: var(--color-text-secondary)">{{ entry.ties }}</td>
                <td class="py-3 px-2 text-center" style="color: var(--color-text-primary)">{{ entry.win_pct.toFixed(3) }}</td>
                <td class="py-3 px-2 text-right font-medium" style="color: var(--color-text-primary)">{{ entry.points_for.toFixed(1) }}</td>
                <td class="py-3 px-2 text-right" style="color: var(--color-text-secondary)">{{ entry.points_against.toFixed(1) }}</td>
                <td class="py-3 px-2 text-right font-medium"
                  :style="`color: ${Number(entry.points_diff) >= 0 ? '#16a34a' : '#dc2626'}`">
                  {{ Number(entry.points_diff) >= 0 ? '+' : '' }}{{ Number(entry.points_diff).toFixed(1) }}
                </td>
                <td class="py-3 px-2 text-center">
                  <span v-if="entry.streak_type && entry.streak_count > 0"
                    class="font-mono text-xs px-1.5 py-0.5 rounded font-semibold"
                    :style="`background: ${entry.streak_type === 'W' ? '#d1fae5' : '#fee2e2'}; color: ${entry.streak_type === 'W' ? '#16a34a' : '#dc2626'}`">
                    {{ entry.streak_type }}{{ entry.streak_count }}
                  </span>
                  <span v-else style="color: var(--color-text-secondary)">—</span>
                </td>
                <td class="py-3 px-2 text-center text-xs" style="color: var(--color-text-secondary)">
                  {{ entry.all_play_wins }}-{{ entry.all_play_losses }}
                </td>
                <td class="py-3 px-2 text-center text-xs" style="color: var(--color-text-secondary)">
                  {{ Number(entry.games_behind) === 0 ? '—' : Number(entry.games_behind).toFixed(1) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Settings tab -->
      <div v-else-if="activeTab === 'settings'" class="space-y-4">
        <AppSpinner v-if="loadingSettings" />

        <template v-else-if="settings">
          <!-- Scoring -->
          <AppCard>
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="font-semibold mb-3" style="color: var(--color-text-primary)">Scoring</h3>
                <dl class="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-1 text-sm">
                  <div>
                    <dt style="color: var(--color-text-secondary)">Fractional</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.scoring.fractional_scoring ? 'On' : 'Off' }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Median Game</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.scoring.median_game ? 'On' : 'Off' }}</dd>
                  </div>
                </dl>
              </div>
              <AppButton v-if="isCommissioner" size="sm" variant="ghost" @click="startEdit('scoring')">Edit</AppButton>
            </div>
          </AppCard>

          <!-- Roster -->
          <AppCard>
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="font-semibold mb-3" style="color: var(--color-text-primary)">Roster</h3>
                <dl class="grid grid-cols-4 sm:grid-cols-6 gap-x-6 gap-y-1 text-sm">
                  <div v-for="slot in rosterSlots" :key="slot.key">
                    <dt style="color: var(--color-text-secondary)">{{ slot.label }}</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.roster[slot.key] }}</dd>
                  </div>
                </dl>
              </div>
              <AppButton v-if="isCommissioner" size="sm" variant="ghost" @click="startEdit('roster')">Edit</AppButton>
            </div>
          </AppCard>

          <!-- Draft -->
          <AppCard>
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="font-semibold mb-3" style="color: var(--color-text-primary)">Draft</h3>
                <dl class="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-1 text-sm">
                  <div>
                    <dt style="color: var(--color-text-secondary)">Type</dt>
                    <dd style="color: var(--color-text-primary)">{{ DRAFT_TYPES[settings.draft.draft_type_id] }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Seconds/Pick</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.draft.seconds_per_pick }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Autopick</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.draft.autopick_enabled ? 'On' : 'Off' }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">3rd Rd Reversal</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.draft.third_round_reversal ? 'Yes' : 'No' }}</dd>
                  </div>
                </dl>
              </div>
              <AppButton v-if="isCommissioner" size="sm" variant="ghost" @click="startEdit('draft')">Edit</AppButton>
            </div>
          </AppCard>

          <!-- Waivers -->
          <AppCard>
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="font-semibold mb-3" style="color: var(--color-text-primary)">Waivers</h3>
                <dl class="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-1 text-sm">
                  <div>
                    <dt style="color: var(--color-text-secondary)">Type</dt>
                    <dd style="color: var(--color-text-primary)">{{ WAIVER_TYPES[settings.waivers.waiver_type_id] }}</dd>
                  </div>
                  <div v-if="settings.waivers.waiver_type_id === 3">
                    <dt style="color: var(--color-text-secondary)">FAAB Budget</dt>
                    <dd style="color: var(--color-text-primary)">${{ settings.waivers.faab_budget }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Process Day</dt>
                    <dd style="color: var(--color-text-primary)" class="capitalize">{{ settings.waivers.waiver_process_day }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Max Acquisitions</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.waivers.max_acquisitions ?? 'Unlimited' }}</dd>
                  </div>
                </dl>
              </div>
              <AppButton v-if="isCommissioner" size="sm" variant="ghost" @click="startEdit('waivers')">Edit</AppButton>
            </div>
          </AppCard>

          <!-- Trades -->
          <AppCard>
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="font-semibold mb-3" style="color: var(--color-text-primary)">Trades</h3>
                <dl class="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-1 text-sm">
                  <div>
                    <dt style="color: var(--color-text-secondary)">Deadline Week</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.trades.deadline_week ?? 'None' }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Review Days</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.trades.review_days }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Veto Votes</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.trades.veto_votes_required }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Future Picks</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.trades.allow_future_picks ? 'Yes' : 'No' }}</dd>
                  </div>
                </dl>
              </div>
              <AppButton v-if="isCommissioner" size="sm" variant="ghost" @click="startEdit('trades')">Edit</AppButton>
            </div>
          </AppCard>

          <!-- Playoffs -->
          <AppCard>
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="font-semibold mb-3" style="color: var(--color-text-primary)">Playoffs</h3>
                <dl class="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-1 text-sm">
                  <div>
                    <dt style="color: var(--color-text-secondary)">Teams</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.playoffs.playoff_teams }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Weeks</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.playoffs.start_week }}–{{ settings.playoffs.end_week }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Consolation</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.playoffs.consolation_bracket ? 'Yes' : 'No' }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Seeding</dt>
                    <dd style="color: var(--color-text-primary)">{{ SEEDING_TYPES[settings.playoffs.seeding_id] }}</dd>
                  </div>
                </dl>
              </div>
              <AppButton v-if="isCommissioner" size="sm" variant="ghost" @click="startEdit('playoffs')">Edit</AppButton>
            </div>
          </AppCard>

          <!-- Keeper -->
          <AppCard>
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <h3 class="font-semibold mb-3" style="color: var(--color-text-primary)">Keeper / Dynasty</h3>
                <dl class="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-1 text-sm">
                  <div>
                    <dt style="color: var(--color-text-secondary)">Keeper Count</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.keeper.keeper_count }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Cost Type</dt>
                    <dd style="color: var(--color-text-primary)">{{ KEEPER_COST_TYPES[settings.keeper.cost_type_id] }}</dd>
                  </div>
                  <div>
                    <dt style="color: var(--color-text-secondary)">Taxi Squad</dt>
                    <dd style="color: var(--color-text-primary)">{{ settings.keeper.taxi_squad_size }}</dd>
                  </div>
                </dl>
              </div>
              <AppButton v-if="isCommissioner" size="sm" variant="ghost" @click="startEdit('keeper')">Edit</AppButton>
            </div>
          </AppCard>
        </template>
      </div>
    </template>

    <!-- Add Team modal -->
    <AppModal v-model="showAddTeam">
      <template #title>Add Team</template>
      <form class="space-y-4" @submit.prevent="addTeam">
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Team Name</label>
          <input
            v-model="teamForm.name"
            required
            class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none focus:ring-2"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
          />
        </div>
        <div class="flex gap-3 justify-end">
          <AppButton variant="ghost" type="button" @click="showAddTeam = false">Cancel</AppButton>
          <AppButton type="submit" :loading="addingTeam">Add</AppButton>
        </div>
      </form>
    </AppModal>

    <!-- Edit Branding modal -->
    <AppModal v-model="showBrandingModal">
      <template #title>Edit Team Branding</template>
      <form v-if="brandingForm" class="space-y-4" @submit.prevent="saveBranding">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Abbreviation (max 5)</label>
            <input
              v-model="brandingForm.abbreviation"
              maxlength="5"
              placeholder="e.g. GOAT"
              class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Slogan / Tagline</label>
            <input
              v-model="brandingForm.slogan"
              maxlength="200"
              placeholder="Optional team motto"
              class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
            />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Logo URL</label>
          <input
            v-model="brandingForm.logo_url"
            placeholder="https://..."
            class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
          />
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div v-for="field in colorFields" :key="field.key">
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">{{ field.label }}</label>
            <div class="flex items-center gap-2">
              <input
                type="color"
                :value="brandingForm[field.key] || '#000000'"
                class="w-8 h-8 rounded cursor-pointer border-0 p-0"
                @input="(e) => { brandingForm[field.key] = (e.target as HTMLInputElement).value }"
              />
              <input
                v-model="brandingForm[field.key]"
                maxlength="7"
                placeholder="#000000"
                class="flex-1 text-sm rounded-lg px-2 py-2 border focus:outline-none font-mono"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
              />
            </div>
          </div>
        </div>
        <div class="flex gap-3 justify-end pt-2">
          <AppButton variant="ghost" type="button" @click="showBrandingModal = false">Cancel</AppButton>
          <AppButton type="submit" :loading="savingBranding">Save</AppButton>
        </div>
      </form>
    </AppModal>

    <!-- Edit Settings modal -->
    <AppModal v-model="showEditModal">
      <template #title>Edit {{ sectionTitles[editingSection ?? ''] }}</template>
      <form v-if="editForm" class="space-y-4" @submit.prevent="saveEdit">

        <!-- Scoring -->
        <template v-if="editingSection === 'scoring'">
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="editForm.fractional_scoring" class="w-4 h-4 rounded" />
            <span class="text-sm" style="color: var(--color-text-primary)">Fractional Scoring</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="editForm.median_game" class="w-4 h-4 rounded" />
            <span class="text-sm" style="color: var(--color-text-primary)">Median Game (weekly double-header)</span>
          </label>
        </template>

        <!-- Roster -->
        <template v-if="editingSection === 'roster'">
          <p class="text-xs font-medium uppercase tracking-wide" style="color: var(--color-text-secondary)">Starters & Bench</p>
          <div class="grid grid-cols-3 gap-3">
            <div v-for="slot in rosterSlots.slice(0, 10)" :key="slot.key">
              <label class="block text-xs mb-1" style="color: var(--color-text-secondary)">{{ slot.label }}</label>
              <input type="number" min="0" max="20" v-model.number="editForm[slot.key]"
                class="w-full text-sm rounded px-2 py-1 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
          </div>
          <p class="text-xs font-medium uppercase tracking-wide mt-2" style="color: var(--color-text-secondary)">IDP Slots</p>
          <div class="grid grid-cols-4 gap-3">
            <div v-for="slot in rosterSlots.slice(10)" :key="slot.key">
              <label class="block text-xs mb-1" style="color: var(--color-text-secondary)">{{ slot.label }}</label>
              <input type="number" min="0" max="10" v-model.number="editForm[slot.key]"
                class="w-full text-sm rounded px-2 py-1 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
          </div>
        </template>

        <!-- Draft -->
        <template v-if="editingSection === 'draft'">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Draft Type</label>
            <select v-model.number="editForm.draft_type_id"
              class="w-full text-sm rounded-lg px-3 py-2 border"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)">
              <option v-for="(name, id) in DRAFT_TYPES" :key="id" :value="Number(id)">{{ name }}</option>
            </select>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Seconds Per Pick</label>
              <input type="number" min="10" max="600" v-model.number="editForm.seconds_per_pick"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
          </div>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="editForm.autopick_enabled" class="w-4 h-4 rounded" />
            <span class="text-sm" style="color: var(--color-text-primary)">Autopick Enabled</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="editForm.third_round_reversal" class="w-4 h-4 rounded" />
            <span class="text-sm" style="color: var(--color-text-primary)">3rd Round Reversal (snake)</span>
          </label>
        </template>

        <!-- Waivers -->
        <template v-if="editingSection === 'waivers'">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Waiver Type</label>
            <select v-model.number="editForm.waiver_type_id"
              class="w-full text-sm rounded-lg px-3 py-2 border"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)">
              <option v-for="(name, id) in WAIVER_TYPES" :key="id" :value="Number(id)">{{ name }}</option>
            </select>
          </div>
          <div v-if="editForm.waiver_type_id === 3">
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">FAAB Budget ($)</label>
            <input type="number" min="0" max="10000" v-model.number="editForm.faab_budget"
              class="w-full text-sm rounded-lg px-3 py-2 border"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Waiver Days</label>
              <input type="number" min="1" max="7" v-model.number="editForm.waiver_days"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Process Day</label>
              <select v-model="editForm.waiver_process_day"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)">
                <option v-for="d in WEEKDAYS" :key="d" :value="d" class="capitalize">{{ d }}</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Max Acquisitions (blank = unlimited)</label>
            <input type="number" min="1" v-model.number="editForm.max_acquisitions"
              placeholder="Unlimited"
              class="w-full text-sm rounded-lg px-3 py-2 border"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
          </div>
        </template>

        <!-- Trades -->
        <template v-if="editingSection === 'trades'">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Deadline Week (blank = none)</label>
              <input type="number" min="1" max="18" v-model.number="editForm.deadline_week"
                placeholder="No deadline"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Review Days</label>
              <input type="number" min="0" max="14" v-model.number="editForm.review_days"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Veto Votes Required</label>
            <input type="number" min="1" max="20" v-model.number="editForm.veto_votes_required"
              class="w-full text-sm rounded-lg px-3 py-2 border"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
          </div>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="editForm.allow_future_picks" class="w-4 h-4 rounded" />
            <span class="text-sm" style="color: var(--color-text-primary)">Allow Future Draft Pick Trades</span>
          </label>
        </template>

        <!-- Playoffs -->
        <template v-if="editingSection === 'playoffs'">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Playoff Teams</label>
              <input type="number" min="2" max="32" v-model.number="editForm.playoff_teams"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Start Week</label>
              <input type="number" min="1" max="18" v-model.number="editForm.start_week"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">End Week</label>
              <input type="number" min="1" max="22" v-model.number="editForm.end_week"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Seeding</label>
              <select v-model.number="editForm.seeding_id"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)">
                <option v-for="(name, id) in SEEDING_TYPES" :key="id" :value="Number(id)">{{ name }}</option>
              </select>
            </div>
          </div>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="editForm.consolation_bracket" class="w-4 h-4 rounded" />
            <span class="text-sm" style="color: var(--color-text-primary)">Consolation Bracket</span>
          </label>
        </template>

        <!-- Keeper -->
        <template v-if="editingSection === 'keeper'">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Keeper Count</label>
              <input type="number" min="0" max="30" v-model.number="editForm.keeper_count"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Taxi Squad Size</label>
              <input type="number" min="0" max="10" v-model.number="editForm.taxi_squad_size"
                class="w-full text-sm rounded-lg px-3 py-2 border"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-primary)">Keeper Cost</label>
            <select v-model.number="editForm.cost_type_id"
              class="w-full text-sm rounded-lg px-3 py-2 border"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)">
              <option v-for="(name, id) in KEEPER_COST_TYPES" :key="id" :value="Number(id)">{{ name }}</option>
            </select>
          </div>
        </template>

        <div class="flex gap-3 justify-end pt-2">
          <AppButton variant="ghost" type="button" @click="showEditModal = false">Cancel</AppButton>
          <AppButton type="submit" :loading="saving">Save</AppButton>
        </div>
      </form>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronRight, Pencil } from '@lucide/vue'
import {
  getLeague, getLeagueTeams, createTeam,
  getLeagueSettings, updateLeagueSettings,
  getStandings, updateTeamBranding,
} from '@/api/leagues'
import { useAuthStore } from '@/stores/auth'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'

const DRAFT_TYPES: Record<number, string> = { 1: 'Snake', 2: 'Auction', 3: 'Linear', 4: 'Random Per Round' }
const WAIVER_TYPES: Record<number, string> = { 1: 'Rolling Priority', 2: 'Reverse Standings', 3: 'FAAB' }
const SEEDING_TYPES: Record<number, string> = { 1: 'Record', 2: 'Total Points' }
const KEEPER_COST_TYPES: Record<number, string> = { 1: 'Previous Round', 2: 'Fixed', 3: 'None' }
const WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
const sectionTitles: Record<string, string> = {
  scoring: 'Scoring', roster: 'Roster', draft: 'Draft',
  waivers: 'Waivers', trades: 'Trades', playoffs: 'Playoffs', keeper: 'Keeper / Dynasty',
}
const rosterSlots = [
  { key: 'qb', label: 'QB' }, { key: 'rb', label: 'RB' }, { key: 'wr', label: 'WR' },
  { key: 'te', label: 'TE' }, { key: 'flex', label: 'FLEX' }, { key: 'superflex', label: 'SFLEX' },
  { key: 'k', label: 'K' }, { key: 'dst', label: 'DST' }, { key: 'bench', label: 'BENCH' },
  { key: 'ir', label: 'IR' },
  { key: 'idp_dl', label: 'DL' }, { key: 'idp_dt', label: 'DT' }, { key: 'idp_edge', label: 'EDGE' },
  { key: 'idp_lb', label: 'LB' }, { key: 'idp_ilb', label: 'ILB' }, { key: 'idp_db', label: 'DB' },
  { key: 'idp_cb', label: 'CB' }, { key: 'idp_s', label: 'S' },
]
const colorFields = [
  { key: 'primary_color', label: 'Primary Color' },
  { key: 'secondary_color_1', label: 'Secondary 1' },
  { key: 'secondary_color_2', label: 'Secondary 2' },
]

const authStore = useAuthStore()
const route = useRoute()
const leagueId = route.params.id as string

const loading = ref(true)
const loadingSettings = ref(false)
const loadingStandings = ref(false)
const league = ref<any>(null)
const teams = ref<any[]>([])
const settings = ref<any>(null)
const standings = ref<any[]>([])
const activeTab = ref<'teams' | 'standings' | 'settings'>('teams')

// Add team
const showAddTeam = ref(false)
const addingTeam = ref(false)
const teamForm = ref({ name: '' })

// Edit settings
const showEditModal = ref(false)
const editingSection = ref<string | null>(null)
const editForm = ref<Record<string, any> | null>(null)
const saving = ref(false)

// Edit branding
const showBrandingModal = ref(false)
const brandingTeamId = ref<string | null>(null)
const brandingForm = ref<Record<string, any>>({})
const savingBranding = ref(false)

const isCommissioner = computed(() => league.value?.created_by === authStore.user?.id)

onMounted(async () => {
  try {
    const [l, t] = await Promise.all([getLeague(leagueId), getLeagueTeams(leagueId)])
    league.value = l
    teams.value = t
  } finally {
    loading.value = false
  }
})

async function onSettingsTab() {
  if (settings.value) return
  loadingSettings.value = true
  try {
    settings.value = await getLeagueSettings(leagueId)
  } finally {
    loadingSettings.value = false
  }
}

async function onStandingsTab() {
  loadingStandings.value = true
  try {
    standings.value = await getStandings(leagueId)
  } finally {
    loadingStandings.value = false
  }
}

async function handleTabChange(tab: string) {
  activeTab.value = tab as 'teams' | 'standings' | 'settings'
  if (tab === 'settings') await onSettingsTab()
  if (tab === 'standings') await onStandingsTab()
}

function startEdit(section: string) {
  editingSection.value = section
  editForm.value = { ...settings.value[section] }
  showEditModal.value = true
}

async function saveEdit() {
  if (!editingSection.value || !editForm.value) return
  saving.value = true
  try {
    const updated = await updateLeagueSettings(leagueId, { [editingSection.value]: editForm.value })
    settings.value = updated
    showEditModal.value = false
  } finally {
    saving.value = false
  }
}

async function addTeam() {
  addingTeam.value = true
  try {
    const team = await createTeam(leagueId, teamForm.value.name)
    teams.value.push(team)
    showAddTeam.value = false
    teamForm.value = { name: '' }
  } finally {
    addingTeam.value = false
  }
}

function openBrandingEdit(team: any) {
  brandingTeamId.value = team.id
  brandingForm.value = {
    abbreviation: team.abbreviation ?? '',
    slogan: team.slogan ?? '',
    logo_url: team.logo_url ?? '',
    primary_color: team.primary_color ?? '',
    secondary_color_1: team.secondary_color_1 ?? '',
    secondary_color_2: team.secondary_color_2 ?? '',
  }
  showBrandingModal.value = true
}

async function saveBranding() {
  if (!brandingTeamId.value) return
  savingBranding.value = true
  try {
    const body: Record<string, string | null> = {}
    for (const key of ['abbreviation', 'slogan', 'logo_url', 'primary_color', 'secondary_color_1', 'secondary_color_2']) {
      body[key] = brandingForm.value[key] || null
    }
    const updated = await updateTeamBranding(leagueId, brandingTeamId.value, body)
    const idx = teams.value.findIndex(t => t.id === brandingTeamId.value)
    if (idx !== -1) teams.value[idx] = { ...teams.value[idx], ...updated }
    showBrandingModal.value = false
  } finally {
    savingBranding.value = false
  }
}
</script>
