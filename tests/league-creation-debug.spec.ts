import { test, expect } from '@playwright/test'

test.describe('League Creation Flow - Debug', () => {
  test('create league, navigate to dashboard, return to leagues', async ({ page }) => {
    // Update baseURL for current port
    const baseURL = 'http://localhost:5181'

    // 1. Navigate to app
    await page.goto(`${baseURL}/`)

    // Click "Sign in with Email"
    const emailSigninButton = page.locator('button:has-text("Sign in with Email")')
    await emailSigninButton.click()
    await page.waitForSelector('input[type="email"]', { timeout: 10000 })

    // 2. Login
    const emailInput = page.locator('input[type="email"]')
    const passwordInput = page.locator('input[type="password"]')
    const submitButton = page.locator('button[type="submit"]')

    await emailInput.fill('wtest@test.com')
    await passwordInput.fill('iwant2Test123')
    await submitButton.click()

    // Wait for redirect after login
    await page.waitForURL('**/dashboard**', { timeout: 10000 })
    console.log('✓ Logged in successfully')

    // 3. Navigate to Leagues page
    await page.goto(`${baseURL}/leagues`)
    await page.waitForLoadState('networkidle')
    console.log('✓ Navigated to Leagues page')

    // Take screenshot before creating league
    await page.screenshot({ path: 'test-results/01-leagues-before.png', fullPage: true })
    console.log('✓ Screenshot 1: Leagues page before creation')

    // 4. Create a new league with a unique name
    const leagueName = `Test League ${Date.now()}`
    const createButton = page.locator('button:has-text("New League")')
    await createButton.click()

    // Wait for modal to appear
    await page.waitForSelector('text=Create League', { timeout: 10000 })

    // Fill in league name
    const nameInput = page.locator('input[placeholder="My Fantasy League"]')
    await nameInput.fill(leagueName)

    // Submit - use the form's submit button (type="submit")
    const confirmButton = page.locator('button[type="submit"]:has-text("Create")')
    await confirmButton.click()

    // Wait for league to be created
    await page.waitForLoadState('networkidle')
    console.log(`✓ League created: ${leagueName}`)

    // Take screenshot after creating league
    await page.screenshot({ path: 'test-results/02-leagues-after-create.png', fullPage: true })

    // 5. Verify league appears in Leagues page
    const leagueCard = page.locator(`text=${leagueName}`)
    await expect(leagueCard).toBeVisible({ timeout: 5000 })
    console.log('✓ League visible in Leagues page')

    // 6. Intercept API calls to debug
    page.on('response', async (response) => {
      if (response.url().includes('/api/leagues')) {
        const status = response.status()
        console.log(`API /api/leagues: ${status}`)
        if (status === 500) {
          try {
            const data = await response.json()
            console.log('ERROR RESPONSE:', JSON.stringify(data, null, 2))
          } catch {
            console.log('(Could not parse error response)')
          }
        }
      }
    })

    // Navigate to Dashboard
    await page.goto(`${baseURL}/dashboard`)
    await page.waitForLoadState('networkidle')
    console.log('✓ Navigated to Dashboard')

    // Take screenshot of dashboard
    await page.screenshot({ path: 'test-results/03-dashboard.png', fullPage: true })

    // Check if league appears in Dashboard's "My Leagues" section
    const leagueInDashboard = page.locator(`text=${leagueName}`)
    const isDashboardVisible = await leagueInDashboard.isVisible().catch(() => false)
    console.log(isDashboardVisible ? '✓ League visible in Dashboard' : '✗ League NOT visible in Dashboard')

    // 7. Navigate back to Leagues page
    await page.goto(`${baseURL}/leagues`)
    await page.waitForLoadState('networkidle')
    console.log('✓ Navigated back to Leagues page')

    // Take screenshot after returning
    await page.screenshot({ path: 'test-results/04-leagues-after-return.png', fullPage: true })

    // 8. Check if league still appears
    const leagueCardAfterReturn = page.locator(`text=${leagueName}`)
    const isLeagueStillVisible = await leagueCardAfterReturn.isVisible().catch(() => false)

    if (isLeagueStillVisible) {
      console.log('✓ League still visible after returning to Leagues page')
    } else {
      console.log('✗ ISSUE: League disappeared after visiting Dashboard!')

      // Debug: Check page content
      const pageContent = await page.content()
      if (pageContent.includes(leagueName)) {
        console.log('  → League name found in HTML, but not rendered/visible')
      } else {
        console.log('  → League name NOT in HTML at all')
      }

      // Log what leagues are visible
      const leagueNames = await page.locator('[class*="LeagueCard"]').allTextContents()
      console.log('  → Leagues currently visible:', leagueNames)
    }

    expect(isLeagueStillVisible).toBe(true)
  })
})
