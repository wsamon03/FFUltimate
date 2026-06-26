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
          v-for="tab in ['teams', 'standings', 'settings', 'invite']"
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
                  <TeamHelmet
                    :primary-color="team.primary_color"
                    :secondary-color="team.secondary_color_1"
                    :tertiary-color="team.secondary_color_2"
                    :logo-url="team.logo_url"
                    :abbreviation="team.abbreviation"
                    :size="48"
                    :transparent="true"
                    class="flex-shrink-0"
                  />
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

      <!-- Invite tab -->
      <div v-else-if="activeTab === 'invite'" class="space-y-6">

        <!-- Code / URL / QR row -->
        <AppCard>
          <div class="flex items-start gap-6">

            <!-- Left: invite code + join URL stacked -->
            <div class="flex-1 min-w-0">
              <div class="space-y-4">
                <!-- Invite code -->
                <div>
                  <p class="text-xs font-medium uppercase tracking-wide mb-1" style="color: var(--color-text-secondary)">Invite Code</p>
                  <div class="flex items-center gap-1.5">
                    <code class="text-2xl font-mono font-bold tracking-widest" style="color: var(--color-text-primary)">{{ league?.invite_code }}</code>
                    <AppButton size="sm" variant="ghost" @click="copyCode" aria-label="Copy invite code">
                      <Check v-if="codeCopied" :size="15" />
                      <Copy v-else :size="15" />
                    </AppButton>
                  </div>
                </div>

                <hr style="border-color: var(--color-border)" />

                <!-- Join URL -->
                <div class="min-w-0">
                  <p class="text-xs font-medium uppercase tracking-wide mb-1" style="color: var(--color-text-secondary)">Join Link</p>
                  <div class="flex items-center gap-1.5 min-w-0">
                    <span class="text-sm" style="color: var(--color-text-primary)">{{ joinUrl }}</span>
                    <AppButton size="sm" variant="ghost" @click="copyUrl" aria-label="Copy join link" class="flex-shrink-0">
                      <Check v-if="urlCopied" :size="15" />
                      <Copy v-else :size="15" />
                    </AppButton>
                  </div>
                </div>
              </div>

              <!-- Regenerate (commissioner only) -->
              <div v-if="isCommissioner" class="flex items-start gap-3 mt-4 pt-4 border-t" style="border-color: var(--color-border)">
                <AppButton size="sm" variant="ghost" :loading="regenerating" @click="doRegenerateCode" class="flex-shrink-0">Regenerate</AppButton>
                <p class="text-xs mt-1.5" style="color: var(--color-text-secondary)">Generates a new code — anyone with the old link will no longer be able to join.</p>
              </div>
            </div>

            <!-- Right: QR code -->
            <div class="flex-shrink-0 flex items-center self-center">
              <canvas ref="qrCanvas" class="rounded-lg" />
            </div>

          </div>
        </AppCard>

        <!-- Email invites -->
        <AppCard v-if="canSendInvites">
          <h3 class="font-semibold mb-4" style="color: var(--color-text-primary)">Email Invites</h3>
          <form @submit.prevent="sendEmails" class="space-y-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary)">Recipients (one email per line)</label>
              <textarea
                v-model="emailRecipients"
                rows="3"
                placeholder="jane@example.com&#10;bob@example.com"
                class="w-full text-sm rounded-lg px-3 py-2 border resize-y focus:outline-none focus:ring-2"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary)">Message (editable)</label>
              <textarea
                v-model="emailMessage"
                rows="6"
                class="w-full text-sm rounded-lg px-3 py-2 border resize-y focus:outline-none focus:ring-2"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
              />
            </div>
            <p v-if="emailStatus" :class="emailStatus.ok ? 'text-green-600' : 'text-red-600'" class="text-sm">{{ emailStatus.msg }}</p>
            <AppButton type="submit" :loading="sendingEmails">Send Email Invites</AppButton>
          </form>
        </AppCard>

        <!-- SMS invites -->
        <AppCard v-if="canSendInvites">
          <h3 class="font-semibold mb-4" style="color: var(--color-text-primary)">Text Message Invites</h3>
          <form @submit.prevent="sendSms" class="space-y-3">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary)">Phone Numbers (one per line, e.g. +15551234567)</label>
              <textarea
                v-model="smsRecipients"
                rows="3"
                placeholder="+15551234567&#10;+14155552671"
                class="w-full text-sm rounded-lg px-3 py-2 border resize-y focus:outline-none focus:ring-2"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary)">Message (editable)</label>
              <textarea
                v-model="smsMessage"
                rows="3"
                class="w-full text-sm rounded-lg px-3 py-2 border resize-y focus:outline-none focus:ring-2"
                style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary); --tw-ring-color: var(--color-primary)"
              />
            </div>
            <p v-if="smsStatus" :class="smsStatus.ok ? 'text-green-600' : 'text-red-600'" class="text-sm">{{ smsStatus.msg }}</p>
            <AppButton type="submit" :loading="sendingSms">Send Text Invites</AppButton>
          </form>
        </AppCard>

        <p v-if="!canSendInvites" class="text-sm" style="color: var(--color-text-secondary)">
          Only the commissioner can send invites for this league. Share the code or URL above instead.
        </p>
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
        <!-- Logo -->
        <div>
          <label class="block text-sm font-medium mb-2" style="color: var(--color-text-primary)">Logo</label>
          <!-- Mode tabs -->
          <div class="flex gap-1 mb-3 p-1 rounded-lg" style="background: var(--color-bg-secondary)">
            <button
              v-for="mode in (['url', 'upload', 'choose'] as const)"
              :key="mode"
              type="button"
              class="flex-1 px-2 py-1 text-xs rounded font-medium transition-colors"
              :style="logoMode === mode
                ? 'background: var(--color-primary); color: white'
                : 'background: transparent; color: var(--color-text-secondary)'"
              @click="logoMode = mode"
            >{{ mode === 'url' ? 'URL' : mode === 'upload' ? 'Upload' : 'Presets' }}</button>
          </div>

          <!-- URL mode -->
          <div v-if="logoMode === 'url'">
            <input
              v-model="brandingForm.logo_url"
              placeholder="https://example.com/logo.png"
              class="w-full text-sm rounded-lg px-3 py-2 border focus:outline-none"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
            />
            <div v-if="brandingForm.logo_url" class="mt-2 flex items-center gap-2">
              <img :src="brandingForm.logo_url" class="w-8 h-8 rounded object-cover" @error="(e: Event) => ((e.target as HTMLImageElement).style.display = 'none')" />
              <span class="text-xs" style="color: var(--color-text-secondary)">Preview</span>
            </div>
          </div>

          <!-- Upload mode -->
          <div v-else-if="logoMode === 'upload'" class="space-y-2">
            <label
              class="flex flex-col items-center justify-center w-full h-24 rounded-lg cursor-pointer transition-colors border-2 border-dashed hover:opacity-70"
              style="border-color: var(--color-border)"
            >
              <span class="text-sm" style="color: var(--color-text-secondary)">Click to upload an image</span>
              <span class="text-xs mt-0.5" style="color: var(--color-text-secondary)">PNG, JPG, GIF — max 2 MB</span>
              <input type="file" accept="image/*" class="hidden" @change="onLogoFileChange" />
            </label>
            <div v-if="brandingForm.logo_url?.startsWith('data:')" class="flex items-center gap-3 p-2 rounded-lg" style="background: var(--color-bg-secondary)">
              <img :src="brandingForm.logo_url" class="w-10 h-10 rounded object-cover flex-shrink-0" />
              <span class="text-xs" style="color: var(--color-text-secondary)">Uploaded image preview</span>
            </div>
          </div>

          <!-- Presets mode -->
          <div v-else-if="logoMode === 'choose'">
            <div class="grid grid-cols-5 gap-2">
              <button
                v-for="preset in PRESET_LOGOS"
                :key="preset.id"
                type="button"
                class="aspect-square rounded-lg border-2 text-2xl flex items-center justify-center transition-all hover:scale-110"
                :style="brandingForm.logo_url === emojiLogoUri(preset.emoji)
                  ? 'border-color: var(--color-primary)'
                  : 'border-color: var(--color-border); background: var(--color-bg-secondary)'"
                :title="preset.label"
                @click="brandingForm.logo_url = emojiLogoUri(preset.emoji)"
              >{{ preset.emoji }}</button>
            </div>
          </div>
        </div>

        <!-- Team Colors -->
        <div class="grid grid-cols-3 gap-3">
          <div v-for="field in colorFields" :key="field.key" class="flex flex-col gap-1.5">
            <label class="block text-xs font-medium uppercase tracking-wide" style="color: var(--color-text-secondary)">{{ field.label }}</label>
            <!-- Large color swatch — clicking opens native color picker -->
            <label class="relative block cursor-pointer group">
              <div
                class="w-full h-12 rounded-lg border-2 transition-all group-hover:brightness-90 flex items-end justify-end pb-1 pr-1.5"
                :style="`background: ${brandingForm[field.key] || '#6b7280'}; border-color: rgba(0,0,0,0.18)`"
              >
                <span class="text-sm leading-none opacity-50 select-none">✎</span>
              </div>
              <input
                type="color"
                :value="brandingForm[field.key] || '#000000'"
                class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                @input="(e) => { brandingForm[field.key] = (e.target as HTMLInputElement).value }"
              />
            </label>
            <!-- Narrow hex input -->
            <input
              v-model="brandingForm[field.key]"
              maxlength="7"
              placeholder="#000000"
              class="w-28 text-xs rounded px-2 py-1.5 border font-mono focus:outline-none"
              style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
            />
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronRight, Pencil, Copy, Check } from '@lucide/vue'
import QRCode from 'qrcode'

import {
  getLeague, getLeagueTeams, createTeam,
  getLeagueSettings, updateLeagueSettings,
  getStandings, updateTeamBranding,
  regenerateInviteCode, sendEmailInvites, sendSmsInvites,
} from '@/api/leagues'
import { useAuthStore } from '@/stores/auth'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppCard from '@/components/ui/AppCard.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppEmptyState from '@/components/ui/AppEmptyState.vue'
import TeamHelmet from '@/components/leagues/TeamHelmet.vue'

const PRESET_LOGOS = [
  { id: 'dragon',    emoji: '🐉', label: 'Dragon'    },
  { id: 'crown',     emoji: '👑', label: 'Crown'     },
  { id: 'fire',      emoji: '🔥', label: 'Fire'      },
  { id: 'lightning', emoji: '⚡', label: 'Lightning' },
  { id: 'swords',    emoji: '⚔️', label: 'Swords'    },
  { id: 'shield',    emoji: '🛡️', label: 'Shield'    },
  { id: 'skull',     emoji: '💀', label: 'Skull'     },
  { id: 'star',      emoji: '⭐', label: 'Star'      },
  { id: 'rocket',    emoji: '🚀', label: 'Rocket'    },
  { id: 'wolf',      emoji: '🐺', label: 'Wolf'      },
  { id: 'eagle',     emoji: '🦅', label: 'Eagle'     },
  { id: 'bear',      emoji: '🐻', label: 'Bear'      },
  { id: 'lion',      emoji: '🦁', label: 'Lion'      },
  { id: 'shark',     emoji: '🦈', label: 'Shark'     },
  { id: 'gem',       emoji: '💎', label: 'Diamond'   },
  { id: 'thunder',   emoji: '🌩️', label: 'Thunder'   },
  { id: 'dagger',    emoji: '🗡️', label: 'Dagger'    },
  { id: 'trophy',    emoji: '🏆', label: 'Trophy'    },
  { id: 'bull',      emoji: '🐂', label: 'Bull'      },
  { id: 'hawk',      emoji: '🦆', label: 'Hawk'      },
]

function emojiLogoUri(emoji: string): string {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">${emoji}</text></svg>`
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
}

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
const activeTab = ref<'teams' | 'standings' | 'settings' | 'invite'>('teams')

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
const logoMode = ref<'url' | 'upload' | 'choose'>('url')

const isCommissioner = computed(() => league.value?.created_by === authStore.user?.id)

// Invite tab state

const qrCanvas = ref<HTMLCanvasElement | null>(null)
const codeCopied = ref(false)
const urlCopied = ref(false)
const regenerating = ref(false)

const joinUrl = computed(() =>
  league.value?.invite_code
    ? `${window.location.origin}/leagues/join/${league.value.invite_code}`
    : ''
)

const canSendInvites = computed(() => {
  if (!league.value) return false
  const scope = league.value.available_scope_id
  if (scope === 1) return isCommissioner.value
  return true
})

const defaultEmailMessage = computed(() => {
  if (!league.value) return ''
  return `Hey! You've been invited to join ${league.value.name} on our fantasy football platform!\n\nUse invite code: ${league.value.invite_code}\nOr join directly: ${joinUrl.value}\n\nCan't wait to compete with you this season!`
})

const defaultSmsMessage = computed(() => {
  if (!league.value) return ''
  return `Join ${league.value.name} on fantasy football! Code: ${league.value.invite_code} — ${joinUrl.value}`
})

const emailRecipients = ref('')
const emailMessage = ref('')
const sendingEmails = ref(false)
const emailStatus = ref<{ ok: boolean; msg: string } | null>(null)

const smsRecipients = ref('')
const smsMessage = ref('')
const sendingSms = ref(false)
const smsStatus = ref<{ ok: boolean; msg: string } | null>(null)

watch(activeTab, (tab) => {
  if (tab === 'invite') {
    if (!emailMessage.value) emailMessage.value = defaultEmailMessage.value
    if (!smsMessage.value) smsMessage.value = defaultSmsMessage.value
    setTimeout(() => {
      if (qrCanvas.value && joinUrl.value) {
        QRCode.toCanvas(qrCanvas.value, joinUrl.value, { width: 120, margin: 1 })
      }
    }, 50)
  }
})

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
  activeTab.value = tab as 'teams' | 'standings' | 'settings' | 'invite'
  if (tab === 'settings') await onSettingsTab()
  if (tab === 'standings') await onStandingsTab()
}

function copyCode() {
  if (!league.value?.invite_code) return
  navigator.clipboard.writeText(league.value.invite_code)
  codeCopied.value = true
  setTimeout(() => { codeCopied.value = false }, 2000)
}

function copyUrl() {
  navigator.clipboard.writeText(joinUrl.value)
  urlCopied.value = true
  setTimeout(() => { urlCopied.value = false }, 2000)
}

async function doRegenerateCode() {
  regenerating.value = true
  try {
    const result = await regenerateInviteCode(leagueId)
    if (league.value) league.value.invite_code = result.invite_code
    if (qrCanvas.value && joinUrl.value) {
      await QRCode.toCanvas(qrCanvas.value, `${window.location.origin}/leagues/join/${result.invite_code}`, { width: 120, margin: 1 })
    }
  } finally {
    regenerating.value = false
  }
}

async function sendEmails() {
  const recipients = emailRecipients.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (!recipients.length) return
  sendingEmails.value = true
  emailStatus.value = null
  try {
    await sendEmailInvites(leagueId, recipients, emailMessage.value)
    emailStatus.value = { ok: true, msg: `Sent to ${recipients.length} recipient(s).` }
    emailRecipients.value = ''
  } catch (err: any) {
    emailStatus.value = { ok: false, msg: err?.response?.data?.detail ?? 'Failed to send emails.' }
  } finally {
    sendingEmails.value = false
  }
}

async function sendSms() {
  const recipients = smsRecipients.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (!recipients.length) return
  sendingSms.value = true
  smsStatus.value = null
  try {
    await sendSmsInvites(leagueId, recipients, smsMessage.value)
    smsStatus.value = { ok: true, msg: `Sent to ${recipients.length} recipient(s).` }
    smsRecipients.value = ''
  } catch (err: any) {
    smsStatus.value = { ok: false, msg: err?.response?.data?.detail ?? 'Failed to send SMS.' }
  } finally {
    sendingSms.value = false
  }
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
  logoMode.value = 'url'
  showBrandingModal.value = true
}

function onLogoFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    alert('Image must be under 2 MB')
    return
  }
  const reader = new FileReader()
  reader.onload = (evt) => { brandingForm.value.logo_url = evt.target?.result as string }
  reader.readAsDataURL(file)
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
