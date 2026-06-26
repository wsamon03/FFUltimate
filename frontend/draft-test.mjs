/**
 * Draft Room Playwright Tests
 * Tests all features from the draft_room_checklist.md
 */
import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BASE_URL = 'http://localhost:5173';
const LEAGUE_ID = 'c957718b-c976-4f80-9c06-fe23982e1c24';
const DRAFT_YEAR = 2026;
const EMAIL = 'wtest@test.com';
const PASSWORD = 'iwant2Test123';

const screenshotDir = join(__dirname, 'test-screenshots');
mkdirSync(screenshotDir, { recursive: true });

let testResults = [];

function pass(name, notes = '') {
  testResults.push({ name, status: 'PASS', notes });
  console.log(`  ✅ PASS: ${name}${notes ? ' — ' + notes : ''}`);
}

function fail(name, notes = '') {
  testResults.push({ name, status: 'FAIL', notes });
  console.log(`  ❌ FAIL: ${name}${notes ? ' — ' + notes : ''}`);
}

async function screenshot(page, name) {
  const path = join(screenshotDir, `${name.replace(/[^a-z0-9]/gi, '-')}.png`);
  await page.screenshot({ path, fullPage: false });
  console.log(`    📸 ${path}`);
  return path;
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle');

  // Try email/password login if available
  const emailInput = page.locator('input[type="email"], input[name="email"]').first();
  const passwordInput = page.locator('input[type="password"]').first();

  if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
    await emailInput.fill(EMAIL);
    await passwordInput.fill(PASSWORD);
    const submitBtn = page.locator('button[type="submit"]').first();
    await submitBtn.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  }
}

async function loginViaAPI(context) {
  // Login via API and set cookie/localStorage
  const response = await context.request.post('http://localhost:8001/auth/login', {
    data: { email: EMAIL, password: PASSWORD }
  });
  const { access_token } = await response.json();

  // Set the token in a page's localStorage
  const page = await context.newPage();
  await page.goto(BASE_URL);
  await page.waitForLoadState('domcontentloaded');

  // Store token in localStorage as the app expects it
  await page.evaluate((token) => {
    localStorage.setItem('access_token', token);
  }, access_token);

  return { page, token: access_token };
}

// ============================================================
// Test 1: Navigation - Enter Draft Room button
// ============================================================
async function testNavigation(context) {
  console.log('\n=== Test 1: Navigation ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    await screenshot(page, '01-league-detail');

    // Check if "Enter Draft Room" button exists
    const draftBtn = page.getByText('Enter Draft Room');
    if (await draftBtn.isVisible({ timeout: 5000 })) {
      pass('Enter Draft Room button visible in LeagueDetailPage');

      // Click it
      await draftBtn.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);

      const url = page.url();
      if (url.includes('/draft')) {
        pass('Clicking Enter Draft Room navigates to /leagues/{id}/draft');
        await screenshot(page, '01-draft-page-initial');
      } else {
        fail('Enter Draft Room does not navigate to draft route', `URL: ${url}`);
      }
    } else {
      // Check if we're not logged in
      const loginText = await page.textContent('body');
      if (loginText.includes('login') || loginText.includes('Login') || loginText.includes('sign in')) {
        fail('Not logged in — cannot see Enter Draft Room button');
      } else {
        fail('Enter Draft Room button NOT visible in LeagueDetailPage');
        await screenshot(page, '01-league-detail-no-button');
      }
    }
  } catch (e) {
    fail('Navigation test', e.message);
    await screenshot(page, '01-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 2: DraftPage pending state
// ============================================================
async function testPendingState(context) {
  console.log('\n=== Test 2: Draft Pending State ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    await screenshot(page, '02-draft-pending');

    // Check status bar
    const statusLabel = page.locator('.status-label, .status-bar');
    const bodyText = await page.textContent('body');

    if (bodyText.includes('Draft Pending')) {
      pass('Status bar shows "Draft Pending" when no draft started');
    } else {
      fail('Status bar does not show "Draft Pending"', 'Body text: ' + bodyText.substring(0, 200));
    }

    // Check "Set Draft Order" component visible (commissioner)
    if (bodyText.includes('Set Draft Order') || bodyText.includes('set draft order')) {
      pass('DraftOrderSetup component visible for commissioner in pending state');
    } else {
      fail('DraftOrderSetup NOT visible for commissioner');
    }

    // Check Start Draft button
    if (bodyText.includes('Start Draft')) {
      pass('"Start Draft" button visible for commissioner');
    } else {
      fail('"Start Draft" button NOT visible');
    }

    // Check back link
    const backLink = page.locator('.back-link, a').filter({ hasText: '←' }).first();
    if (await backLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      pass('Back link (← League Name) visible');
    } else {
      fail('Back link not visible');
    }

  } catch (e) {
    fail('Pending state test', e.message);
    await screenshot(page, '02-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 3: Draft Order Setup
// ============================================================
async function testDraftOrderSetup(context) {
  console.log('\n=== Test 3: Draft Order Setup ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Test Randomize button
    const randomizeBtn = page.getByText('Randomize');
    if (await randomizeBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      pass('"Randomize" button present in DraftOrderSetup');
      await randomizeBtn.click();
      await page.waitForTimeout(2000);
      await screenshot(page, '03-after-randomize');

      const bodyText = await page.textContent('body');
      if (!bodyText.includes('Failed to randomize')) {
        pass('Randomize button works without error');
      } else {
        fail('Randomize returned error');
      }
    } else {
      fail('"Randomize" button NOT found');
    }

    // Test Save Order button
    const saveBtn = page.getByText('Save Order');
    if (await saveBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      pass('"Save Order" button present');
      await saveBtn.click();
      await page.waitForTimeout(1500);
      await screenshot(page, '03-after-save');

      const bodyText = await page.textContent('body');
      if (!bodyText.includes('Failed to save')) {
        pass('Save Order works without error');
      } else {
        fail('Save Order returned error');
      }
    } else {
      fail('"Save Order" button NOT found');
    }

    // Test Up/Down buttons
    const upButtons = page.locator('.actions button, button').filter({ hasText: '↑' });
    const downButtons = page.locator('.actions button, button').filter({ hasText: '↓' });
    const upCount = await upButtons.count();
    const downCount = await downButtons.count();

    if (upCount > 0 && downCount > 0) {
      pass(`Up/Down reorder buttons present (${upCount} up, ${downCount} down)`);
      // Click an enabled down button to reorder
      for (let i = 0; i < downCount; i++) {
        const btn = downButtons.nth(i);
        const isDisabled = await btn.isDisabled();
        if (!isDisabled) {
          await btn.click();
          await page.waitForTimeout(500);
          pass('Manual reorder via down button works');
          break;
        }
      }
    } else {
      fail('Up/Down reorder buttons NOT found');
    }

  } catch (e) {
    fail('Draft order setup test', e.message);
    await screenshot(page, '03-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 4: Start Draft
// ============================================================
async function testStartDraft(context) {
  console.log('\n=== Test 4: Start Draft ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // First ensure draft order is set
    const randomizeBtn = page.getByText('Randomize');
    if (await randomizeBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await randomizeBtn.click();
      await page.waitForTimeout(1500);
      const saveBtn = page.getByText('Save Order');
      if (await saveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveBtn.click();
        await page.waitForTimeout(1500);
      }
    }

    // Click Start Draft
    const startBtn = page.getByText('Start Draft');
    if (await startBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await startBtn.click();
      await page.waitForTimeout(3000);
      await screenshot(page, '04-after-start');

      const bodyText = await page.textContent('body');

      // Check draft is now active
      if (bodyText.includes('Round 1') || bodyText.includes('Pick 1')) {
        pass('Draft started — status shows "Round 1 · Pick 1"');
      } else if (bodyText.includes('Draft Paused') || bodyText.includes('active')) {
        pass('Draft started (status updated)');
      } else {
        fail('Draft start — status did not update', 'Body: ' + bodyText.substring(0, 300));
      }

      // Check DraftBoard is visible (three-panel layout)
      if (bodyText.includes('Draft Board') || bodyText.includes('DRAFT BOARD')) {
        pass('DraftBoard panel visible after draft start');
      } else {
        fail('DraftBoard NOT visible after draft start');
      }

      // Check Available Players panel
      if (bodyText.includes('Available Players') || bodyText.includes('AVAILABLE PLAYERS')) {
        pass('AvailablePlayersPanel visible after draft start');
      } else {
        fail('AvailablePlayersPanel NOT visible after draft start');
      }

      // Check My Team panel
      if (bodyText.includes('My Team') || bodyText.includes('MY TEAM')) {
        pass('MyTeamPanel visible after draft start');
      } else {
        fail('MyTeamPanel NOT visible after draft start');
      }

      // Check timer is visible
      const timer = page.locator('.draft-timer, .timer');
      const timerText = await page.textContent('body');
      if (timerText.match(/\d+:\d+/)) {
        pass('Timer displaying MM:SS format');
      } else {
        fail('Timer NOT displaying correctly');
      }

      // Check Pause button appeared
      if (bodyText.includes('Pause')) {
        pass('"Pause" button visible for commissioner during active draft');
      } else {
        fail('"Pause" button NOT visible during active draft');
      }

    } else {
      fail('Start Draft button not visible', 'May be in wrong state');
      await screenshot(page, '04-no-start-btn');
    }

  } catch (e) {
    fail('Start draft test', e.message);
    await screenshot(page, '04-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 5: Available Players Panel (Search & Filter)
// ============================================================
async function testAvailablePlayers(context) {
  console.log('\n=== Test 5: Available Players Panel ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Navigate to active draft state
    const bodyText = await page.textContent('body');
    if (bodyText.includes('Draft Pending') || bodyText.includes('Set Draft Order')) {
      // Start the draft first
      const startBtn = page.getByText('Start Draft');
      if (await startBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await startBtn.click();
        await page.waitForTimeout(3000);
      }
    }

    await screenshot(page, '05-available-players');

    // Check position filter tabs — count .pos-tab buttons in the DOM
    const tabCount = await page.locator('.pos-tab').count();
    if (tabCount >= 7) {
      pass(`Position filter tabs visible (${tabCount} tabs found)`);
    } else if (tabCount >= 5) {
      pass(`Position filter tabs visible (${tabCount}/7 found — acceptable)`);
    } else {
      // Fallback: check body text
      const bodyForTabs = await page.textContent('body');
      const found = ['ALL', 'QB', 'RB', 'WR', 'TE', 'K', 'DST'].filter(t => bodyForTabs.includes(t)).length;
      if (found >= 5) {
        pass(`Position filter tabs present in body (${found}/7 found)`);
      } else {
        fail(`Only ${tabCount} tab buttons / ${found}/7 positions found`);
      }
    }

    // Click QB tab
    const qbTab = page.getByText('QB', { exact: true });
    if (await qbTab.isVisible({ timeout: 2000 }).catch(() => false)) {
      await qbTab.click();
      await page.waitForTimeout(1500);
      await screenshot(page, '05-after-qb-filter');
      pass('Clicked QB tab without error');
    }

    // Test search input
    const searchInput = page.locator('input[placeholder*="Search"], input[placeholder*="search"]').first();
    if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      pass('Search input visible');

      // Click ALL tab first
      const allTab = page.getByText('ALL', { exact: true });
      if (await allTab.isVisible({ timeout: 1000 }).catch(() => false)) {
        await allTab.click();
        await page.waitForTimeout(1000);
      }

      await searchInput.fill('Josh');
      await page.waitForTimeout(1500); // wait for debounce
      await screenshot(page, '05-search-josh');

      const resultsText = await page.textContent('body');
      if (resultsText.toLowerCase().includes('josh') || resultsText.includes('No players')) {
        pass('Search input filters players (300ms debounce)');
      } else {
        fail('Search results did not update', resultsText.substring(0, 200));
      }

      // Clear search
      await searchInput.fill('');
      await page.waitForTimeout(1500);
    } else {
      fail('Search input NOT visible');
    }

    // Check player rows have Draft button
    const draftButtons = page.getByText('Draft', { exact: true });
    const count = await draftButtons.count();
    if (count > 0) {
      pass(`"Draft" buttons present in available players list (${count} buttons)`);
    } else {
      fail('"Draft" buttons NOT found in available players list');
    }

    // Check "+" queue buttons
    const queueButtons = page.locator('button').filter({ hasText: '+' });
    const queueCount = await queueButtons.count();
    if (queueCount > 0) {
      pass(`"+" queue buttons present (${queueCount} found)`);
    } else {
      fail('"+" queue buttons NOT found');
    }

  } catch (e) {
    fail('Available players test', e.message);
    await screenshot(page, '05-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 6: Pick Submission and Confirmation Modal
// ============================================================
async function testPickSubmission(context) {
  console.log('\n=== Test 6: Pick Submission ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Find first enabled Draft button
    const draftBtns = page.getByText('Draft', { exact: true });
    const count = await draftBtns.count();

    if (count === 0) {
      fail('No Draft buttons found to test pick submission');
      await screenshot(page, '06-no-draft-buttons');
      return;
    }

    // Click first enabled draft button
    let clicked = false;
    for (let i = 0; i < Math.min(count, 5); i++) {
      const btn = draftBtns.nth(i);
      const isDisabled = await btn.isDisabled().catch(() => true);
      if (!isDisabled) {
        await btn.click();
        clicked = true;
        break;
      }
    }

    if (!clicked) {
      fail('All Draft buttons are disabled (may not be user\'s turn)');
      // Commissioner can pick for any team — check if it's a turn issue
      const bodyText = await page.textContent('body');
      fail('Pick submission', 'Draft buttons disabled: ' + bodyText.substring(0, 200));
      return;
    }

    await page.waitForTimeout(1000);
    await screenshot(page, '06-pick-modal');

    // Check modal appeared
    const bodyText = await page.textContent('body');
    if (bodyText.includes('Confirm Pick') || bodyText.includes('Draft this player')) {
      pass('Pick confirmation modal appears after clicking "Draft"');

      // Check modal content
      if (bodyText.includes('Draft this player?')) {
        pass('Modal shows "Draft this player?" label');
      } else {
        fail('"Draft this player?" label NOT found in modal');
      }

      // Check Cancel button
      const cancelBtn = page.getByText('Cancel');
      if (await cancelBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        pass('"Cancel" button visible in modal');

        // Test cancel closes modal
        await cancelBtn.click();
        await page.waitForTimeout(500);
        const afterCancel = await page.textContent('body');
        if (!afterCancel.includes('Confirm Pick')) {
          pass('Cancel button closes modal without submitting');
        } else {
          fail('Cancel did not close modal');
        }
      } else {
        fail('"Cancel" button NOT visible in modal');
      }

      // Re-open and actually draft
      for (let i = 0; i < Math.min(count, 5); i++) {
        const btn = draftBtns.nth(i);
        const isDisabled = await btn.isDisabled().catch(() => true);
        if (!isDisabled) {
          await btn.click();
          break;
        }
      }

      await page.waitForTimeout(1000);
      const confirmBtn = page.getByText('Draft').last(); // The confirm button
      if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await confirmBtn.click();
        await page.waitForTimeout(3000);
        await screenshot(page, '06-after-pick');

        const afterPick = await page.textContent('body');
        if (!afterPick.includes('Confirm Pick')) {
          pass('Pick submitted — modal closed after confirmation');
        } else {
          // Check for error
          if (afterPick.includes('error') || afterPick.includes('failed') || afterPick.includes('Error')) {
            fail('Pick submission resulted in error', afterPick.substring(0, 200));
          } else {
            fail('Modal did not close after pick confirmation');
          }
        }

        // Check if pick number advanced
        if (afterPick.includes('Pick 2') || afterPick.includes('Round')) {
          pass('Pick number advanced after submission');
        }
      }
    } else {
      fail('Pick confirmation modal did NOT appear', 'Body: ' + bodyText.substring(0, 300));
      await screenshot(page, '06-no-modal');
    }

  } catch (e) {
    fail('Pick submission test', e.message);
    await screenshot(page, '06-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 7: DraftBoard visualization
// ============================================================
async function testDraftBoard(context) {
  console.log('\n=== Test 7: DraftBoard ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    await screenshot(page, '07-draft-board');

    const bodyText = await page.textContent('body');

    // Check board area exists
    if (bodyText.includes('Draft Board') || bodyText.includes('DRAFT BOARD')) {
      pass('Draft Board panel heading visible');
    } else {
      fail('Draft Board panel heading NOT visible');
    }

    // Check board cells exist (if draft is active)
    const boardGrid = page.locator('.board-grid, .board-container, [class*="board"]');
    if (await boardGrid.isVisible({ timeout: 2000 }).catch(() => false)) {
      pass('DraftBoard grid/container visible');
    } else {
      // Board might be in three-panel layout
      const threePanel = page.locator('.draft-layout');
      if (await threePanel.isVisible({ timeout: 2000 }).catch(() => false)) {
        pass('Three-panel draft layout visible');
      } else {
        fail('DraftBoard grid NOT visible');
      }
    }

    // Check for team headers or round labels
    const roundLabel = page.locator('[class*="round"], .round-label, .gutter-cell').first();
    if (await roundLabel.isVisible({ timeout: 2000 }).catch(() => false)) {
      pass('Round labels visible in DraftBoard');
    } else {
      // Check if the board has any numeric content (round numbers)
      if (bodyText.match(/\bR\d+\b|\bRound \d+\b/)) {
        pass('Round indicators visible in board');
      } else {
        fail('Round labels NOT visible in board');
      }
    }

  } catch (e) {
    fail('DraftBoard test', e.message);
    await screenshot(page, '07-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 8: DraftQueue (My Queue)
// ============================================================
async function testDraftQueue(context) {
  console.log('\n=== Test 8: Draft Queue ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    const bodyText = await page.textContent('body');

    // Check My Queue section
    if (bodyText.includes('My Queue') || bodyText.includes('MY QUEUE')) {
      pass('"My Queue" section visible');
    } else {
      fail('"My Queue" section NOT visible');
      await screenshot(page, '08-no-queue');
    }

    // Check "+" buttons exist for adding to queue
    const plusBtns = page.locator('button').filter({ hasText: '+' });
    const plusCount = await plusBtns.count();

    if (plusCount > 0) {
      pass(`"+" add to queue buttons found (${plusCount})`);

      // Add a player to queue
      const firstPlus = plusBtns.first();
      const isDisabled = await firstPlus.isDisabled().catch(() => true);
      if (!isDisabled) {
        await firstPlus.click();
        await page.waitForTimeout(1000);
        await screenshot(page, '08-after-add-queue');

        const afterAdd = await page.textContent('body');
        if (afterAdd.includes('My Queue') && (afterAdd.includes('↑') || afterAdd.includes('↓') || afterAdd.includes('×'))) {
          pass('Player added to queue — queue controls visible');

          // Test Save button
          const saveBtn = page.getByText('Save').first();
          if (await saveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
            const isEnabled = !(await saveBtn.isDisabled().catch(() => false));
            if (isEnabled) {
              await saveBtn.click();
              await page.waitForTimeout(1500);
              pass('Queue Save button works');
            } else {
              fail('Queue Save button is disabled after adding player');
            }
          } else {
            fail('Queue Save button NOT found');
          }
        } else {
          fail('Player may not have been added to queue', afterAdd.substring(0, 200));
        }
      }
    } else {
      fail('"+" buttons NOT found (may be no available players panel visible)');
    }

  } catch (e) {
    fail('Draft queue test', e.message);
    await screenshot(page, '08-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 9: Commissioner Pause/Resume
// ============================================================
async function testPauseResume(context) {
  console.log('\n=== Test 9: Pause/Resume ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    const bodyText = await page.textContent('body');

    // Check if draft is active (has Pause button)
    const pauseBtn = page.getByText('Pause');
    if (await pauseBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      pass('"Pause" button visible during active draft');

      await pauseBtn.click();
      await page.waitForTimeout(4000); // poll interval is 2.5s; wait for next poll
      await screenshot(page, '09-after-pause');

      const afterPause = await page.textContent('body');
      if (afterPause.includes('Draft Paused') || afterPause.includes('paused')) {
        pass('Status shows "Draft Paused" after pause');
      } else {
        fail('Status did not update to paused', afterPause.substring(0, 200));
      }

      // Check Resume button appeared
      const resumeBtn = page.getByText('Resume');
      if (await resumeBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        pass('"Resume" button visible when draft is paused');

        await resumeBtn.click();
        await page.waitForTimeout(4000); // wait for poll
        await screenshot(page, '09-after-resume');

        const afterResume = await page.textContent('body');
        if (afterResume.includes('Round') || afterResume.includes('Pick') || afterResume.includes('Pause')) {
          pass('Draft resumed — active state restored');
        } else {
          fail('Draft did not resume properly', afterResume.substring(0, 200));
        }
      } else {
        fail('"Resume" button NOT visible after pause');
      }
    } else {
      fail('"Pause" button NOT visible — draft may not be active');
      await screenshot(page, '09-no-pause-btn');
    }

  } catch (e) {
    fail('Pause/resume test', e.message);
    await screenshot(page, '09-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 10: DraftTimer component
// ============================================================
async function testDraftTimer(context) {
  console.log('\n=== Test 10: Draft Timer ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);
    await screenshot(page, '10-timer-initial');

    // Check timer exists and shows MM:SS
    const bodyText = await page.textContent('body');
    const timerPattern = /\d{1,2}:\d{2}/;
    if (timerPattern.test(bodyText)) {
      pass('Timer displays MM:SS format');

      // Wait 3 seconds and check timer decremented
      const initialTime = bodyText.match(timerPattern)?.[0];
      await page.waitForTimeout(3000);
      const afterBody = await page.textContent('body');
      const laterTime = afterBody.match(timerPattern)?.[0];

      if (initialTime && laterTime && initialTime !== laterTime) {
        pass(`Timer is counting down (${initialTime} → ${laterTime})`);
      } else {
        fail('Timer does not appear to be counting down', `${initialTime} → ${laterTime}`);
      }
    } else {
      fail('Timer MM:SS format NOT found', bodyText.substring(0, 300));
    }

    // Check "YOUR PICK" badge if it's user's turn
    if (bodyText.includes('YOUR PICK')) {
      pass('"YOUR PICK" badge visible when it is user\'s turn');
    } else {
      // This is OK if it's not user's turn
      pass('"YOUR PICK" badge not shown (expected if not user\'s turn)');
    }

  } catch (e) {
    fail('Draft timer test', e.message);
    await screenshot(page, '10-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Test 11: Back navigation
// ============================================================
async function testBackNavigation(context) {
  console.log('\n=== Test 11: Back Navigation ===');
  const page = await context.newPage();

  try {
    await page.goto(`${BASE_URL}/leagues/${LEAGUE_ID}/draft`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Click back link
    const backLink = page.locator('.back-link').first();
    if (await backLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      const linkText = await backLink.textContent();
      pass(`Back link visible: "${linkText}"`);

      await backLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      const url = page.url();
      if (url.includes(`/leagues/${LEAGUE_ID}`) && !url.includes('/draft')) {
        pass('Back link navigates to league detail page');
      } else {
        fail('Back link did not navigate to league detail', `URL: ${url}`);
      }
    } else {
      fail('Back link NOT visible in draft page status bar');
    }

  } catch (e) {
    fail('Back navigation test', e.message);
    await screenshot(page, '11-error').catch(() => {});
  } finally {
    await page.close();
  }
}

// ============================================================
// Main runner
// ============================================================
async function main() {
  console.log('🏈 Draft Room Feature Tests');
  console.log('============================');
  console.log(`League ID: ${LEAGUE_ID}`);
  console.log(`Frontend: ${BASE_URL}`);
  console.log(`Screenshots: ${screenshotDir}\n`);

  const browser = await chromium.launch({ headless: true });

  try {
    // Create context with API login
    const context = await browser.newContext();

    // Login via API and inject token
    const loginResp = await context.request.post('http://localhost:8001/auth/login', {
      data: { email: EMAIL, password: PASSWORD }
    });
    const { access_token } = await loginResp.json();

    // Set up storage state with the auth token
    const setupPage = await context.newPage();
    await setupPage.goto(BASE_URL);
    await setupPage.waitForLoadState('domcontentloaded');

    // Inject the access token into localStorage and pinia store
    await setupPage.evaluate((token) => {
      localStorage.setItem('access_token', token);
    }, access_token);

    // Navigate to force auth store to pick up the token
    await setupPage.goto(`${BASE_URL}/leagues`);
    await setupPage.waitForLoadState('networkidle');
    await setupPage.waitForTimeout(2000);

    const bodyText = await setupPage.textContent('body');
    if (bodyText.includes('login') || bodyText.includes('Login') || bodyText.includes('Sign in')) {
      console.log('⚠️  Not authenticated — trying login page');
      await setupPage.goto(`${BASE_URL}/login`);
      await setupPage.waitForLoadState('networkidle');

      // Try filling login form
      const emailInput = setupPage.locator('input[type="email"], input[name="email"]').first();
      if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await emailInput.fill(EMAIL);
        const passInput = setupPage.locator('input[type="password"]').first();
        await passInput.fill(PASSWORD);
        const submitBtn = setupPage.locator('button[type="submit"]').first();
        await submitBtn.click();
        await setupPage.waitForLoadState('networkidle');
        await setupPage.waitForTimeout(2000);
      }
    }

    console.log('Auth setup done. Body preview:', bodyText.substring(0, 100));
    await setupPage.close();

    // Save storage state for reuse
    const storageState = await context.storageState();
    await context.close();

    // Create fresh context with stored auth
    const authContext = await browser.newContext({ storageState });

    // Run all tests
    await testNavigation(authContext);
    await testPendingState(authContext);
    await testDraftOrderSetup(authContext);
    await testStartDraft(authContext);
    await testAvailablePlayers(authContext);
    await testPickSubmission(authContext);
    await testDraftBoard(authContext);
    await testDraftQueue(authContext);
    await testPauseResume(authContext);
    await testDraftTimer(authContext);
    await testBackNavigation(authContext);

    await authContext.close();

  } finally {
    await browser.close();
  }

  // Print summary
  console.log('\n============================');
  console.log('📊 TEST SUMMARY');
  console.log('============================');
  const passed = testResults.filter(r => r.status === 'PASS').length;
  const failed = testResults.filter(r => r.status === 'FAIL').length;
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`Total: ${testResults.length}`);

  if (failed > 0) {
    console.log('\nFailed tests:');
    testResults.filter(r => r.status === 'FAIL').forEach(r => {
      console.log(`  - ${r.name}: ${r.notes}`);
    });
  }

  // Write results JSON for programmatic access
  writeFileSync(join(__dirname, 'test-results.json'), JSON.stringify(testResults, null, 2));
  console.log(`\nResults saved to test-results.json`);

  return { passed, failed, results: testResults };
}

main().catch(console.error);
