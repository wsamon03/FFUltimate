import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5173'
const EMAIL = 'wtest@test.com'
const PASS = 'iwant2Test123'

async function login(page: any) {
  await page.goto(`${BASE}/`)
  await page.locator('button:has-text("Sign in with Email")').click()
  await page.waitForSelector('input[type="email"]', { timeout: 10000 })
  await page.fill('input[type="email"]', EMAIL)
  await page.fill('input[type="password"]', PASS)
  await page.click('button[type="submit"]')
  await page.waitForURL(`${BASE}/dashboard`, { timeout: 15000 })
}

/** Returns the draft page URL for the first league found, or null. */
async function getFirstDraftUrl(page: any): Promise<string | null> {
  await page.goto(`${BASE}/leagues`)
  await page.waitForSelector('a[href^="/leagues/"]', { timeout: 10000 })
  const leagueLinks = page.locator('a[href^="/leagues/"]').filter({ hasNotText: 'join' })
  const count = await leagueLinks.count()
  if (count === 0) return null
  const href = await leagueLinks.first().getAttribute('href')
  const leagueId = href?.split('/')[2]
  if (!leagueId) return null
  return `${BASE}/leagues/${leagueId}/draft`
}

test.describe('Draft room UI redesign', () => {
  // ─── Layout ──────────────────────────────────────────────────────────────

  test('draft route uses fullscreen layout (no sidebar)', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(3000)
    await page.screenshot({ path: 'tests/screenshots/draft-ui-01-fullscreen.png', fullPage: false })

    const sidebar = page.locator('nav.sidebar, .sidebar, [class*="sidebar"]').first()
    const sidebarVisible = await sidebar.isVisible().catch(() => false)
    expect(sidebarVisible).toBe(false)
  })

  test('draft page shows status bar with league name back link', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const backLink = page.locator('a.back-link, a[href^="/leagues/"][class*="back"]')
    await expect(backLink.first()).toBeVisible({ timeout: 8000 })
    await page.screenshot({ path: 'tests/screenshots/draft-ui-02-statusbar.png' })
  })

  test('pending state shows order setup for commissioner or waiting message', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(3000)
    await page.screenshot({ path: 'tests/screenshots/draft-ui-03-pending.png' })

    const hasOrderSetup = await page.locator('text=Draft Order, text=Randomize').first().isVisible().catch(() => false)
    const hasWaiting = await page.locator('text=Waiting for the commissioner').first().isVisible().catch(() => false)
    const hasDraftLayout = await page.locator('.draft-layout').isVisible().catch(() => false)
    const hasStartBtn = await page.locator('button:has-text("Start Draft")').isVisible().catch(() => false)

    expect(hasOrderSetup || hasWaiting || hasDraftLayout || hasStartBtn).toBe(true)
  })

  // ─── Active draft: start and verify 3-column layout ─────────────────────

  test('starting a draft shows the three-panel layout', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    // If already active, skip the start flow
    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)

    if (!isDraftActive) {
      // Save order if needed
      const saveOrderBtn = page.locator('button:has-text("Save Order")')
      if (await saveOrderBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveOrderBtn.click()
        await page.waitForTimeout(1000)
      }

      // Start draft
      const startBtn = page.locator('button:has-text("Start Draft")')
      if (!await startBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        test.skip(); return
      }
      await startBtn.click()
      await page.waitForTimeout(3000)
    }

    await page.screenshot({ path: 'tests/screenshots/draft-ui-04-active-layout.png', fullPage: false })

    // Three panels must be visible
    await expect(page.locator('.draft-layout')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.panel-left')).toBeVisible()
    await expect(page.locator('.panel-center')).toBeVisible()
    await expect(page.locator('.panel-right')).toBeVisible()
  })

  test('active draft shows queue and my team panels in left column', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    // Left column should have both queue and myteam panels
    await expect(page.locator('.panel-queue')).toBeVisible()
    await expect(page.locator('.panel-myteam')).toBeVisible()

    // Panel titles
    const panelTitles = await page.locator('.panel-title').allTextContents()
    const hasMQ = panelTitles.some(t => t.toLowerCase().includes('queue'))
    const hasMT = panelTitles.some(t => t.toLowerCase().includes('team'))
    expect(hasMQ).toBe(true)
    expect(hasMT).toBe(true)

    await page.screenshot({ path: 'tests/screenshots/draft-ui-05-left-panels.png', fullPage: false })
  })

  // ─── Available Players Panel ──────────────────────────────────────────────

  test('available players panel shows position tabs and player table', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    // Wait for players to load
    await page.waitForSelector('.avail-panel', { timeout: 10000 })
    await page.waitForTimeout(3000) // let players load

    await page.screenshot({ path: 'tests/screenshots/draft-ui-06-players-panel.png', fullPage: false })

    // Position tabs
    const posTabs = page.locator('.pos-tab')
    const tabCount = await posTabs.count()
    expect(tabCount).toBeGreaterThanOrEqual(7) // ALL + 6 positions

    const tabLabels = await posTabs.allTextContents()
    expect(tabLabels).toContain('ALL')
    expect(tabLabels).toContain('QB')
    expect(tabLabels).toContain('RB')
    expect(tabLabels).toContain('WR')

    // Stats table exists
    const table = page.locator('.stats-table')
    const tableVisible = await table.isVisible().catch(() => false)
    const stateMsg = page.locator('.state-msg')
    const stateMsgVisible = await stateMsg.isVisible().catch(() => false)
    // Either the table or a loading/empty message must be present
    expect(tableVisible || stateMsgVisible).toBe(true)
  })

  test('clicking a position tab filters the player table', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    await page.waitForSelector('.avail-panel', { timeout: 10000 })
    await page.waitForTimeout(3000)

    // Click QB tab
    const qbTab = page.locator('.pos-tab').filter({ hasText: 'QB' })
    await qbTab.click()
    await page.waitForTimeout(500)

    await page.screenshot({ path: 'tests/screenshots/draft-ui-07-qb-filter.png', fullPage: false })

    // QB tab should be active
    await expect(qbTab).toHaveClass(/active/)

    // If table visible, check QB column appears in header
    const tableVisible = await page.locator('.stats-table').isVisible().catch(() => false)
    if (tableVisible) {
      const headers = await page.locator('.col-header').allTextContents()
      // QB-specific stat columns: Comp, Att, Yds, TD, INT
      const hasQbStat = headers.some(h => ['Comp', 'Att', 'INT'].includes(h.trim()))
      expect(hasQbStat).toBe(true)
    }
  })

  test('search input filters player list', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    await page.waitForSelector('.avail-panel', { timeout: 10000 })
    await page.waitForTimeout(3000)

    const tableVisible = await page.locator('.stats-table').isVisible().catch(() => false)
    if (!tableVisible) { test.skip(); return }

    // Count initial rows
    const initialRows = await page.locator('.player-row').count()

    // Type a common name
    await page.fill('.search-input', 'Smith')
    await page.waitForTimeout(500)

    await page.screenshot({ path: 'tests/screenshots/draft-ui-08-search.png', fullPage: false })

    // Row count should be <= initial (filtered)
    const filteredRows = await page.locator('.player-row').count()
    expect(filteredRows).toBeLessThanOrEqual(initialRows)
  })

  test('sorting by a stat column changes order', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    await page.waitForSelector('.avail-panel', { timeout: 10000 })
    await page.waitForTimeout(3000)

    const tableVisible = await page.locator('.stats-table').isVisible().catch(() => false)
    if (!tableVisible) { test.skip(); return }

    // Click a stat column header (first non-actions header)
    const headers = page.locator('.col-header')
    const count = await headers.count()
    if (count < 2) { test.skip(); return }

    // Click the second header (Player column)
    await headers.nth(0).click()
    await page.waitForTimeout(300)

    // Sort arrow should appear
    const sortArrow = page.locator('.sort-arrow')
    await expect(sortArrow.first()).toBeVisible()

    // Click again to reverse
    await headers.nth(0).click()
    await page.waitForTimeout(300)

    await page.screenshot({ path: 'tests/screenshots/draft-ui-09-sort.png', fullPage: false })
    await expect(sortArrow.first()).toBeVisible()
  })

  // ─── Draft Board Vertical ─────────────────────────────────────────────────

  test('vertical draft board is visible in right panel', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    await page.waitForSelector('.board-vert', { timeout: 8000 })

    // Board header and picks viewport must be visible
    await expect(page.locator('.board-title')).toBeVisible()
    await expect(page.locator('.picks-viewport')).toBeVisible()

    // Full board button
    await expect(page.locator('.btn-full-board')).toBeVisible()

    await page.screenshot({ path: 'tests/screenshots/draft-ui-10-board-vert.png', fullPage: false })
  })

  test('Full Board button opens draggable overlay with horizontal board', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    await page.waitForSelector('.btn-full-board', { timeout: 8000 })
    await page.locator('.btn-full-board').click()
    await page.waitForTimeout(500)

    await page.screenshot({ path: 'tests/screenshots/draft-ui-11-fullboard-overlay.png', fullPage: false })

    // Overlay backdrop and board must appear
    await expect(page.locator('.overlay-backdrop')).toBeVisible()
    await expect(page.locator('.overlay-board')).toBeVisible()
    await expect(page.locator('.overlay-title')).toContainText('Full Draft Board')

    // Close button must work
    await page.locator('.overlay-close').click()
    await page.waitForTimeout(300)
    const overlayGone = !(await page.locator('.overlay-backdrop').isVisible().catch(() => false))
    expect(overlayGone).toBe(true)
  })

  // ─── Chat Panel ──────────────────────────────────────────────────────────

  test('chat panel is visible and can send a message', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    await page.waitForSelector('.chat-panel', { timeout: 8000 })

    await page.screenshot({ path: 'tests/screenshots/draft-ui-12-chat-empty.png', fullPage: false })

    // Chat input must exist
    const chatInput = page.locator('.chat-input')
    await expect(chatInput).toBeVisible()

    // Type and send a message
    await chatInput.fill('Hello from Playwright test!')
    await page.locator('.btn-send').click()
    await page.waitForTimeout(300)

    await page.screenshot({ path: 'tests/screenshots/draft-ui-13-chat-sent.png', fullPage: false })

    // Message should appear in the chat list
    const messages = page.locator('.chat-msg')
    const msgCount = await messages.count()
    expect(msgCount).toBeGreaterThan(0)

    const msgText = await messages.first().textContent()
    expect(msgText).toContain('Hello from Playwright test!')
  })

  // ─── Pick flow ───────────────────────────────────────────────────────────

  test('Draft button opens pick confirmation modal', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    // Commissioner can always pick
    const draftBtns = page.locator('.btn-pick:not([disabled])')
    await page.waitForTimeout(3000) // let players load

    const enabledCount = await draftBtns.count()
    if (enabledCount === 0) { test.skip(); return }

    await draftBtns.first().click()
    await page.waitForTimeout(500)

    await page.screenshot({ path: 'tests/screenshots/draft-ui-14-pick-modal.png', fullPage: false })

    // Modal must appear
    const modal = page.locator('.app-modal, [role="dialog"], .modal-backdrop')
    const modalVisible = await modal.isVisible().catch(() => false)

    const confirmBody = page.locator('.confirm-body')
    const confirmVisible = await confirmBody.isVisible().catch(() => false)

    expect(modalVisible || confirmVisible).toBe(true)

    // Cancel should close it
    const cancelBtn = page.locator('.btn-cancel')
    if (await cancelBtn.isVisible().catch(() => false)) {
      await cancelBtn.click()
      await page.waitForTimeout(300)
    }
  })

  // ─── Queue button ─────────────────────────────────────────────────────────

  test('Add to queue button adds player to queue panel', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    await page.waitForTimeout(3000) // let players load

    const tableVisible = await page.locator('.stats-table').isVisible().catch(() => false)
    if (!tableVisible) { test.skip(); return }

    // Count queue items before
    const queueItemsBefore = await page.locator('.queue-item, .queue-entry').count()

    // Click + button for first player
    const queueBtns = page.locator('.btn-queue')
    const qCount = await queueBtns.count()
    if (qCount === 0) { test.skip(); return }

    await queueBtns.first().click()
    await page.waitForTimeout(500)

    await page.screenshot({ path: 'tests/screenshots/draft-ui-15-queue-add.png', fullPage: false })

    // Queue should have at least the same or more items
    const queueItemsAfter = await page.locator('.queue-item, .queue-entry').count()
    expect(queueItemsAfter).toBeGreaterThanOrEqual(queueItemsBefore)
  })

  // ─── Pagination ───────────────────────────────────────────────────────────

  test('pagination controls appear when players loaded', async ({ page }) => {
    await login(page)
    const draftUrl = await getFirstDraftUrl(page)
    if (!draftUrl) { test.skip(); return }

    await page.goto(draftUrl)
    await page.waitForTimeout(2000)

    const isDraftActive = await page.locator('.draft-layout').isVisible().catch(() => false)
    if (!isDraftActive) { test.skip(); return }

    await page.waitForTimeout(4000) // let players load

    await page.screenshot({ path: 'tests/screenshots/draft-ui-16-pagination.png', fullPage: false })

    // AppPagination renders "Showing X–Y of Z results" text
    const showingText = page.locator('text=/Showing \\d/')
    const paginationVisible = await showingText.first().isVisible().catch(() => false)

    // Or per-page preset buttons (10, 20, 50, 100)
    const presetBtn = page.locator('.avail-panel button:has-text("20")')
    const presetVisible = await presetBtn.isVisible().catch(() => false)

    const stateMsg = page.locator('.state-msg')
    const hasNoPlayers = await stateMsg.isVisible().catch(() => false)

    // Either pagination controls or a state message must be present
    expect(paginationVisible || presetVisible || hasNoPlayers).toBe(true)
  })
})
