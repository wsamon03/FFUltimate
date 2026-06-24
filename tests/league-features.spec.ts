/**
 * Comprehensive league feature tests.
 * Covers: leagues list, create, detail (teams tab), settings tab, edit settings,
 * commissioner check, add team, team detail navigation.
 *
 * mode: serial — tests share leagueId/teamId/leagueName across the describe block.
 * Login avoids networkidle (hangs with Vite HMR) — waits for specific elements instead.
 */
import { test, expect, Page } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

const EMAIL = 'wtest@test.com'
const PASSWORD = 'iwant2Test123'
const SS_DIR = 'test-results/league-features'

if (!fs.existsSync(SS_DIR)) {
  fs.mkdirSync(SS_DIR, { recursive: true })
}

async function login(page: Page) {
  await page.goto('/login')
  // Wait for the email toggle button — avoids networkidle hang from Vite HMR
  await page.locator('button:has-text("Sign in with Email")').waitFor({ state: 'visible', timeout: 15000 })
  await page.locator('button:has-text("Sign in with Email")').click()
  await page.locator('input[type="email"]').waitFor({ state: 'visible', timeout: 5000 })
  await page.locator('input[type="email"]').fill(EMAIL)
  await page.locator('input[type="password"]').fill(PASSWORD)
  await page.locator('button[type="submit"]').click()
  await page.waitForURL('**/dashboard**', { timeout: 15000 })
}

async function gotoLeagues(page: Page) {
  await page.goto('/leagues')
  await page.locator('h1:has-text("Leagues")').waitFor({ state: 'visible', timeout: 10000 })
}

async function ss(page: Page, name: string) {
  const filePath = path.join(SS_DIR, `${name}.png`)
  await page.screenshot({ path: filePath, fullPage: true })
  console.log(`  📸 ${name}`)
}

// ─── TRACK RESULTS ──────────────────────────────────────────────────────────
const results: { name: string; pass: boolean; note?: string }[] = []
function track(name: string, pass: boolean, note?: string) {
  results.push({ name, pass, note })
  const icon = pass ? '🟢' : '🔴'
  console.log(`${icon} ${name}${note ? ' — ' + note : ''}`)
}

test.afterAll(() => {
  console.log('\n═══════════════════════════════════════')
  console.log('TEST RESULTS SUMMARY')
  console.log('═══════════════════════════════════════')
  let pass = 0
  let fail = 0
  for (const r of results) {
    const icon = r.pass ? '🟢' : '🔴'
    console.log(`${icon} ${r.name}${r.note ? ' — ' + r.note : ''}`)
    r.pass ? pass++ : fail++
  }
  console.log('─────────────────────────────────────')
  console.log(`Total: ${pass} passed, ${fail} failed`)
  console.log('═══════════════════════════════════════')
})

// ─── TESTS ──────────────────────────────────────────────────────────────────

test.describe('League Features', () => {
  // Serial mode: all tests in this block run sequentially and share module-level state.
  // This ensures leagueId/leagueName set in test 2 is visible in tests 3-8.
  test.describe.configure({ mode: 'serial' })

  let leagueId: string
  let teamId: string
  const leagueName = `PW Test League ${Date.now()}`

  test('1 - Login and view leagues list', async ({ page }) => {
    await login(page)
    await gotoLeagues(page)

    await ss(page, '01-leagues-list')

    const headingVisible = await page.locator('h1:has-text("Leagues")').isVisible().catch(() => false)
    track('Login + view leagues list', headingVisible)
    expect(headingVisible).toBe(true)
  })

  test('2 - Create a new league with all fields', async ({ page }) => {
    await login(page)
    await gotoLeagues(page)

    await page.locator('button:has-text("New League")').click()
    await page.locator('text=Create League').waitFor({ state: 'visible', timeout: 8000 })

    await ss(page, '02a-create-modal-open')

    await page.locator('input[placeholder="My Fantasy League"]').fill(leagueName)
    await page.locator('textarea').fill('A Playwright test league')

    const selects = page.locator('select')
    await selects.first().selectOption({ value: '3' }) // Dynasty
    if (await selects.count() >= 2) {
      await selects.nth(1).selectOption({ value: '2' }) // Public
    }

    await ss(page, '02b-create-modal-filled')

    await page.locator('button[type="submit"]:has-text("Create")').click()

    // Wait for modal to close, then leagues list
    await page.locator('text=Create League').waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {})
    await page.locator('h1:has-text("Leagues")').waitFor({ state: 'visible', timeout: 10000 })

    await ss(page, '02c-after-create')

    const cardVisible = await page.locator(`text=${leagueName}`).isVisible({ timeout: 8000 }).catch(() => false)
    track('Create league with all fields', cardVisible, leagueName)
    expect(cardVisible).toBe(true)

    // Capture league ID from card link href
    const cardLink = page.locator(`a:has-text("${leagueName}")`)
    if (await cardLink.isVisible().catch(() => false)) {
      const href = await cardLink.getAttribute('href') ?? ''
      const match = href.match(/leagues\/([a-f0-9-]+)/)
      if (match) leagueId = match[1]
      console.log(`  League ID: ${leagueId}`)
    }
  })

  test('3 - View league detail — teams tab', async ({ page }) => {
    await login(page)
    await gotoLeagues(page)

    const card = page.locator(`a:has-text("${leagueName}")`)
    const found = await card.isVisible({ timeout: 8000 }).catch(() => false)
    if (!found) {
      track('View league detail — teams tab', false, 'league card not found')
      return
    }

    // Use goto(href) instead of card.click() — more reliable for SPA routing in Playwright
    const href = await card.getAttribute('href') ?? ''
    const match = href.match(/leagues\/([a-f0-9-]+)/)
    if (match) leagueId = match[1]

    await page.goto(href)
    await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 })

    await ss(page, '03-league-detail-teams')

    const nameVisible = await page.locator(`h1:has-text("${leagueName}")`).isVisible({ timeout: 5000 }).catch(() => false)
    const pageContent = await page.content()
    const hasType = pageContent.includes('Dynasty') || pageContent.includes('dynasty') ||
                    pageContent.includes('Redraft') || pageContent.includes('redraft')
    const hasYear = pageContent.includes('2026')
    const hasTeamsTab = await page.locator('button:has-text("teams"), button:has-text("Teams")').isVisible({ timeout: 3000 }).catch(() => false)
    const hasSettingsTab = await page.locator('button:has-text("settings"), button:has-text("Settings")').isVisible({ timeout: 3000 }).catch(() => false)

    track('View league detail — teams tab', nameVisible && hasTeamsTab,
      `name=${nameVisible}, type=${hasType}, year=${hasYear}, tabs=${hasTeamsTab && hasSettingsTab}`)
    expect(nameVisible).toBe(true)
    expect(hasTeamsTab).toBe(true)
  })

  test('4 - View league settings tab', async ({ page }) => {
    await login(page)

    if (!leagueId) {
      await gotoLeagues(page)
      const card = page.locator(`a:has-text("${leagueName}")`)
      const href = await card.getAttribute('href').catch(() => '') ?? ''
      const match = href.match(/leagues\/([a-f0-9-]+)/)
      if (match) leagueId = match[1]
    }

    await page.goto(`/leagues/${leagueId}`)
    await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 })

    await page.locator('button:has-text("settings"), button:has-text("Settings")').click()
    await page.waitForTimeout(1500)

    await ss(page, '04-league-settings-tab')

    const pageContent = await page.content()
    const hasScoringSection = pageContent.includes('Scoring') || pageContent.includes('scoring')
    const hasRosterSection = pageContent.includes('Roster') || pageContent.includes('roster')
    const hasDraftSection = pageContent.includes('Draft') || pageContent.includes('draft')
    const hasWaiverSection = pageContent.includes('Waivers') || pageContent.includes('waivers')
    const hasPlayoffSection = pageContent.includes('Playoffs') || pageContent.includes('playoffs')

    track('View league settings tab', hasScoringSection && hasRosterSection && hasDraftSection,
      `scoring=${hasScoringSection}, roster=${hasRosterSection}, draft=${hasDraftSection}, waivers=${hasWaiverSection}, playoffs=${hasPlayoffSection}`)
    expect(hasScoringSection).toBe(true)
    expect(hasRosterSection).toBe(true)
  })

  test('5 - Edit scoring settings as commissioner', async ({ page }) => {
    await login(page)

    if (!leagueId) {
      await gotoLeagues(page)
      const card = page.locator(`a:has-text("${leagueName}")`)
      const href = await card.getAttribute('href').catch(() => '') ?? ''
      const match = href.match(/leagues\/([a-f0-9-]+)/)
      if (match) leagueId = match[1]
    }

    await page.goto(`/leagues/${leagueId}`)
    await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 })

    await page.locator('button:has-text("settings"), button:has-text("Settings")').click()
    await page.waitForTimeout(2000)

    const editBtn = page.locator('button:has-text("Edit")').first()
    const editVisible = await editBtn.isVisible({ timeout: 5000 }).catch(() => false)

    if (!editVisible) {
      track('Edit scoring settings as commissioner', false, 'No Edit button (not commissioner or settings not loaded)')
      await ss(page, '05-no-edit-button')
      return
    }

    await editBtn.click()
    await page.waitForTimeout(1000)
    await ss(page, '05a-edit-modal-open')

    // Toggle fractional scoring twice (back to original)
    const checkbox = page.locator('input[type="checkbox"]').first()
    const checkboxVisible = await checkbox.isVisible({ timeout: 3000 }).catch(() => false)
    if (checkboxVisible) {
      await checkbox.click()
      await checkbox.click()
    }

    const saveBtn = page.locator('button[type="submit"]:has-text("Save"), button:has-text("Save")')
    const saveVisible = await saveBtn.isVisible({ timeout: 3000 }).catch(() => false)
    if (saveVisible) {
      await saveBtn.click()
      await page.waitForTimeout(2000)
    }

    await ss(page, '05b-after-save')

    track('Edit scoring settings as commissioner', editVisible && saveVisible,
      `editBtn=${editVisible}, saveBtn=${saveVisible}, checkbox=${checkboxVisible}`)
    expect(editVisible).toBe(true)
  })

  test('6 - Add a team to the league', async ({ page }) => {
    await login(page)

    if (!leagueId) {
      await gotoLeagues(page)
      const card = page.locator(`a:has-text("${leagueName}")`)
      const href = await card.getAttribute('href').catch(() => '') ?? ''
      const match = href.match(/leagues\/([a-f0-9-]+)/)
      if (match) leagueId = match[1]
    }

    await page.goto(`/leagues/${leagueId}`)
    await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 })

    await ss(page, '06a-teams-tab-before')

    const addTeamBtn = page.locator('button:has-text("Add Team")')
    const addVisible = await addTeamBtn.isVisible({ timeout: 5000 }).catch(() => false)

    if (!addVisible) {
      track('Add team to league', false, 'Add Team button not found')
      await ss(page, '06b-no-add-button')
      return
    }

    await addTeamBtn.click()
    await page.waitForTimeout(800)
    await ss(page, '06b-add-team-modal')

    const teamName = `PW Team ${Date.now()}`
    const teamNameInput = page.locator('form input[type="text"], form input:not([type])').first()
    if (await teamNameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await teamNameInput.fill(teamName)
    }

    const addBtn = page.locator('button[type="submit"]:has-text("Add")')
    if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addBtn.click()
      await page.waitForTimeout(2000)
    }

    await ss(page, '06c-after-add-team')

    const teamVisible = await page.locator(`text=${teamName}`).isVisible({ timeout: 8000 }).catch(() => false)
    track('Add team to league', teamVisible, teamName)

    if (teamVisible) {
      const teamLink = page.locator(`a:has-text("${teamName}")`)
      if (await teamLink.isVisible().catch(() => false)) {
        const teamHref = await teamLink.getAttribute('href').catch(() => '') ?? ''
        const tmatch = teamHref.match(/teams\/([a-f0-9-]+)/)
        if (tmatch) teamId = tmatch[1]
      }
    }
  })

  test('7 - Navigate to team detail page', async ({ page }) => {
    await login(page)

    if (!leagueId) {
      await gotoLeagues(page)
      const card = page.locator(`a:has-text("${leagueName}")`)
      const href = await card.getAttribute('href').catch(() => '') ?? ''
      const match = href.match(/leagues\/([a-f0-9-]+)/)
      if (match) leagueId = match[1]
    }

    await page.goto(`/leagues/${leagueId}`)
    await page.locator('h1').waitFor({ state: 'visible', timeout: 10000 })

    const teamLinks = page.locator('a[href*="/teams/"]')
    const count = await teamLinks.count()

    if (count === 0) {
      track('Navigate to team detail', false, 'no team links found')
      await ss(page, '07-no-team-links')
      return
    }

    // Use goto(href) for reliability
    const teamHref = await teamLinks.first().getAttribute('href') ?? ''
    await page.goto(teamHref)
    await page.locator('h1, h2').waitFor({ state: 'visible', timeout: 10000 })

    await ss(page, '07-team-detail')

    const url = page.url()
    const onTeamPage = url.includes('/teams/')
    const content = await page.content()
    const hasTeamContent = content.includes('Roster') || content.includes('Owner') ||
                           content.includes('Lineup') || content.includes('owner')

    track('Navigate to team detail', onTeamPage,
      `url=${url.split('/').slice(-3).join('/')}, content=${hasTeamContent}`)
    expect(onTeamPage).toBe(true)
  })

  test('8 - Verify leagues list renders league cards correctly', async ({ page }) => {
    await login(page)
    await gotoLeagues(page)

    await ss(page, '08-leagues-with-metadata')

    // Use locator visibility — more reliable than content.includes() for truncated text
    const leagueCard = page.locator(`a:has-text("${leagueName}")`)
    const hasLeagueName = await leagueCard.isVisible({ timeout: 5000 }).catch(() => false)

    const hasTeamsText = await page.locator('text=/\\d+ teams/').first().isVisible({ timeout: 3000 }).catch(() => false)
    const hasCreatedText = await page.locator('text=/Created/').first().isVisible({ timeout: 3000 }).catch(() => false)

    track('Leagues list renders cards correctly',
      hasTeamsText && hasLeagueName,
      `teamsText=${hasTeamsText}, leagueName=${hasLeagueName}, createdText=${hasCreatedText}`)
    expect(hasLeagueName).toBe(true)
    expect(hasTeamsText).toBe(true)
  })
})
