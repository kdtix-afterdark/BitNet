# Playwright UI/UX Testing Guide

> **Visual + Accessibility Testing**: Validate UI behavior and catch UX debt early using Playwright.

---

## Overview

Playwright UI testing extends TDD to the user interface layer:

- **Functional testing**: Verify UI elements work correctly
- **Visual regression**: Detect unintended layout/style changes
- **Accessibility scanning**: Catch A11y violations automatically
- **UX debt tracking**: Identify and resolve usability issues early

**Philosophy**: UI tests are executable UX acceptance criteria.

---

## Why Playwright for UI Testing?

### Advantages

✅ **Multi-browser support**: Chromium, Firefox, WebKit (Safari engine)  
✅ **Visual regression**: Screenshot comparison built-in  
✅ **Accessibility testing**: Integrates with @axe-core/playwright  
✅ **Trace viewer**: Step-by-step UX inspection (action replay)  
✅ **Auto-wait**: Smart waiting for elements (reduces flaky tests)  
✅ **Cross-platform**: Works on Windows, Linux, macOS  

### When to Use Playwright

**✅ Use Playwright for**:
- Web application UI testing
- Visual regression detection
- Accessibility validation
- End-to-end user workflows
- Cross-browser compatibility

**❌ Don't use Playwright for**:
- Backend API testing (use requests/fetch)
- Unit testing (use pytest/jest)
- Performance testing (use lighthouse/k6)

---

## Test-Driven Development with UI

### TDD Workflow for UI

**Same Red-Green-Refactor cycle, applied to UI**:

1. **RED**: Write failing Playwright test
   ```typescript
   test('should display success message after form submission', async ({ page }) => {
     await page.goto('/contact');
     await page.fill('input[name="email"]', 'test@example.com');
     await page.click('button[type="submit"]');
     await expect(page.getByRole('alert')).toContainText('Success!');
   });
   ```

2. **Run test**: Verify it fails ❌ (UI not implemented)

3. **GREEN**: Implement minimal UI to pass
   ```html
   <form>
     <input name="email" type="email" />
     <button type="submit">Submit</button>
   </form>
   <div role="alert" id="message">Success!</div>
   ```

4. **Run test**: Verify it passes ✅

5. **REFACTOR**: Improve UI code (styling, accessibility, etc.)
   - Add proper labels
   - Improve contrast
   - Add loading states

6. **Run test**: Verify still passes ✅ (refactoring didn't break behavior)

---

## Playwright Test Structure

### Basic Test Template

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Feature: Contact Form', () => {
  test('should submit form successfully with good UX', async ({ page }, testInfo) => {
    // 1. FUNCTIONAL: Verify user can complete flow
    await page.goto('/contact');
    
    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('textarea[name="message"]', 'Test message');
    await page.click('button[type="submit"]');
    
    // Verify success message appears
    await expect(page.getByRole('alert')).toContainText('Thank you!');
    
    // 2. VISUAL: Capture screenshot for regression detection
    await expect(page).toHaveScreenshot('contact-success.png');
    
    // 3. ACCESSIBILITY: Automated A11y scan
    const results = await new AxeBuilder({ page }).analyze();
    
    // Attach results to test report
    await testInfo.attach('a11y-scan.json', {
      body: JSON.stringify(results, null, 2),
      contentType: 'application/json',
    });
    
    // Assert no violations
    expect(results.violations).toEqual([]);
  });
});
```

---

## Three Pillars of UI Validation

### 1. Functional Testing

**Purpose**: Verify UI elements behave correctly.

**What to test**:
- ✅ **User interactions**: Clicks, form fills, navigation
- ✅ **State changes**: Loading, success, error states
- ✅ **Data display**: Correct content shown
- ✅ **Workflows**: Multi-step processes complete

**Example**:
```typescript
test('should filter products by category', async ({ page }) => {
  await page.goto('/products');
  
  // Select category filter
  await page.selectOption('select[name="category"]', 'electronics');
  
  // Wait for filtered results
  await page.waitForSelector('.product-card');
  
  // Verify only electronics shown
  const products = await page.locator('.product-card').all();
  for (const product of products) {
    const category = await product.getAttribute('data-category');
    expect(category).toBe('electronics');
  }
});
```

---

### 2. Visual Regression Testing

**Purpose**: Detect unintended UI changes (layout, spacing, typography).

**How it works**:
1. First run: Playwright captures baseline screenshot
2. Subsequent runs: Compares current screenshot to baseline
3. If different: Test fails, shows visual diff

**Setup**:
```typescript
// playwright.config.ts
export default defineConfig({
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 100, // Tolerance for minor differences
    },
  },
});
```

**Usage**:
```typescript
test('should maintain header layout', async ({ page }) => {
  await page.goto('/');
  
  // Full page snapshot
  await expect(page).toHaveScreenshot('homepage.png');
  
  // Component-level snapshot (more precise)
  await expect(page.locator('header')).toHaveScreenshot('header.png');
});
```

**Handling changes**:
```bash
# Update baseline when UI changes intentionally
npx playwright test --update-snapshots
```

**Best practices**:
- ✅ **Mask dynamic content**: Timestamps, random IDs
- ✅ **Stabilize animations**: Pause or disable during tests
- ✅ **Consistent viewport**: Set fixed dimensions
- ✅ **Mock data**: Use predictable test data

**Example with masking**:
```typescript
test('should match design with dynamic content masked', async ({ page }) => {
  await page.goto('/dashboard');
  
  await expect(page).toHaveScreenshot('dashboard.png', {
    mask: [
      page.locator('.timestamp'),      // Hide timestamps
      page.locator('.user-avatar'),    // Hide user images
    ],
  });
});
```

---

### 3. Accessibility Testing

**Purpose**: Catch A11y violations automatically (WCAG compliance).

**Install @axe-core/playwright**:
```bash
npm install --save-dev @axe-core/playwright
```

**Usage**:
```typescript
import AxeBuilder from '@axe-core/playwright';

test('should have no accessibility violations', async ({ page }, testInfo) => {
  await page.goto('/');
  
  // Scan entire page
  const results = await new AxeBuilder({ page }).analyze();
  
  // Attach results
  await testInfo.attach('a11y-report.json', {
    body: JSON.stringify(results, null, 2),
    contentType: 'application/json',
  });
  
  // Assert zero violations
  expect(results.violations).toEqual([]);
});
```

**Common violations caught**:
- Missing `alt` text on images
- Low color contrast (text readability)
- Missing form labels
- Duplicate IDs
- Invalid ARIA attributes
- Missing page title

**Scan specific sections**:
```typescript
test('should have accessible form', async ({ page }) => {
  await page.goto('/contact');
  
  // Scan only the form
  const results = await new AxeBuilder({ page })
    .include('form')
    .analyze();
  
  expect(results.violations).toEqual([]);
});
```

**Handle known violations** (temporary exceptions):
```typescript
test('should have minimal violations', async ({ page }) => {
  await page.goto('/legacy-page');
  
  const results = await new AxeBuilder({ page })
    .disableRules(['color-contrast']) // Temporarily skip contrast check
    .analyze();
  
  expect(results.violations).toEqual([]);
  
  // TODO: Fix color-contrast issues (Issue #123)
});
```

---

## UX Debt Tracking

### What is UX Debt?

**Definition**: Usability issues that accumulate when UX shortcuts are taken during development.

**Examples**:
- Confusing error messages
- Inconsistent button styling
- Missing loading states
- Unclear form validation
- Poor mobile experience

**Source**: [Nielsen Norman Group - UX Debt](https://www.nngroup.com/articles/ux-debt/)

---

### Observing UX Issues During Testing

**Every Playwright run is a UX observation opportunity**:

1. **Run tests** (functional, visual, A11y)
2. **Review artifacts**:
   - Screenshot diffs (spacing, alignment issues?)
   - Trace viewer (confusing interactions?)
   - A11y scan (violations?)
3. **Decide**: Fix now or log as UX debt
4. **Document** (if logging debt)

---

### UX Debt Entry Template

**Create one entry per observed issue**:

```markdown
## UX Debt: UXD-20260206-ambiguous-error

**Story/Feature**: User Login Flow
**Where observed**: `/login` page, after invalid credentials
**Symptom**: Error message "Invalid" is too vague
**Impact**: Users don't know if username or password is wrong
**Severity**: S2 (Medium)

**Evidence**:
- Screenshot: `tests/screenshots/login-error.png`
- Trace: `tests/traces/login-failed.zip`

**Proposed fix**: Change message to "Invalid username or password. Please try again."

**Done when**:
- Error message updated
- Playwright test verifies new message
- Visual snapshot updated

**Owner**: Frontend team
**Target milestone**: Sprint 23
```

**Severity levels**:
- **S0 (Blocker)**: Prevents core functionality, must fix immediately
- **S1 (High)**: Major usability issue, fix before release
- **S2 (Medium)**: Noticeable friction, fix soon
- **S3 (Low)**: Minor improvement, fix when convenient

---

### Celebrate Finding UX Debt! 🎉

**Mindset**: Finding UX issues during testing = winning

- 🎉 **Found during development** → Fixed before users affected
- 🎉 **Found in Playwright tests** → Prevented regression
- 🎉 **Found before UAT** → Saved stakeholder time
- 🎉 **Documented with evidence** → Clear path to resolution

**Don't hide UX issues**:
- ❌ "There are some minor issues" (downplaying)
- ✅ "Found 3 UX issues—2 fixed, 1 logged for next sprint!" (celebrating)

---

## Playwright Configuration

### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/ui',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',  // Enable trace on failure
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## Running Playwright Tests

### Local Development

```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test tests/ui/login.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run in debug mode
npx playwright test --debug

# Update snapshots (after intentional UI changes)
npx playwright test --update-snapshots
```

### View Test Results

```bash
# Open HTML report
npx playwright show-report

# Open trace viewer (for failed tests)
npx playwright show-trace trace.zip
```

---

## Pre-UAT Readiness Gate

**Before entering UAT, ensure**:

- [ ] **No S0/S1 UX debt** on critical flows
- [ ] **Visual snapshots stable** (no unexpected diffs)
- [ ] **A11y scans clean** on key flows (or exceptions documented)
- [ ] **Trace artifacts available** for recent changes
- [ ] **All Playwright tests passing** in CI

---

## Definition of Done (UI Features)

**Before merging UI changes**:

- [ ] **Playwright functional tests** exist and pass
- [ ] **Visual snapshots** updated intentionally (with PR note explaining why)
- [ ] **Accessibility scan** added for critical flow
- [ ] **UX debt** either:
  - Fixed in this PR, or
  - Logged with severity, evidence, and target milestone
- [ ] **Tests pass** on all target browsers (Chromium, Firefox, WebKit)
- [ ] **Cross-device verified** (if responsive UI)

---

## Integration with Development Workflow

### Phase 3: TDD Implementation (UI)

**When implementing UI features**:

1. **Write Playwright test FIRST** (RED)
   ```typescript
   test('should show product details', async ({ page }) => {
     await page.goto('/product/123');
     await expect(page.getByRole('heading')).toContainText('Product Name');
   });
   ```

2. **Run test**: Fails ❌ (UI not implemented)

3. **Implement UI** (GREEN)
   ```html
   <h1>Product Name</h1>
   ```

4. **Run test**: Passes ✅

5. **Add visual + A11y** (REFACTOR)
   ```typescript
   await expect(page).toHaveScreenshot('product-details.png');
   const results = await new AxeBuilder({ page }).analyze();
   expect(results.violations).toEqual([]);
   ```

6. **Run test**: Passes ✅

### Phase 6: UAT Testing

**Playwright tests complement manual UAT**:

- **Playwright**: Automated regression detection, A11y checks
- **UAT**: Real-world workflows, subjective usability, edge cases

**Both required** for comprehensive UI validation.

---

## Real-World Example

### Before Playwright

**Problem**:
- UI regressions not caught until UAT
- A11y violations found late
- Visual bugs introduced during refactoring

**Result**:
- 5 UI bugs found in UAT (late discovery)
- 3 A11y violations found by QA team
- Time wasted fixing issues after merge

### After Playwright

**Solution**:
- Playwright tests written with features
- Visual snapshots catch regressions
- A11y scans run automatically

**Result**:
- 8 UI issues caught during development 🎉
- 0 A11y violations reached UAT ✅
- Refactoring done confidently (tests verify no breakage)

**Time saved**: 4-6 hours per sprint (fewer UAT rounds, faster fixes)

---

## Best Practices

### Test Organization

```
tests/
├── ui/
│   ├── auth/
│   │   ├── login.spec.ts
│   │   └── register.spec.ts
│   ├── products/
│   │   ├── list.spec.ts
│   │   └── details.spec.ts
│   └── checkout/
│       └── flow.spec.ts
├── snapshots/
│   ├── auth/
│   │   └── login-success.png
│   └── products/
│       └── product-card.png
└── traces/
    └── (generated on failure)
```

### Naming Conventions

**Test files**: `<feature>.spec.ts`  
**Test names**: `should <user outcome> (and remain accessible)`  
**Snapshots**: `<component>-<state>.png`

**Examples**:
- `login.spec.ts` → `should display error for invalid credentials`
- `product-card.spec.ts` → `should show discount badge for sale items`

---

## Quick Reference

### Essential Commands

```bash
# Run tests
npx playwright test

# Debug
npx playwright test --debug

# Update snapshots
npx playwright test --update-snapshots

# View report
npx playwright show-report

# Generate code
npx playwright codegen http://localhost:3000
```

### Common Assertions

```typescript
// Visibility
await expect(page.getByRole('button')).toBeVisible();
await expect(page.locator('.modal')).toBeHidden();

// Content
await expect(page.getByRole('heading')).toContainText('Welcome');
await expect(page.locator('input[name="email"]')).toHaveValue('test@example.com');

// Visual
await expect(page).toHaveScreenshot('page.png');
await expect(page.locator('header')).toHaveScreenshot('header.png');

// Accessibility
const results = await new AxeBuilder({ page }).analyze();
expect(results.violations).toEqual([]);
```

---

## Key Takeaways

**Remember**:
- 🎭 **UI tests are TDD** (write test first, then UI)
- 🎭 **Visual snapshots catch regressions** (detect unintended changes)
- 🎭 **A11y scans are mandatory** (accessibility is non-negotiable)
- 🎭 **UX debt is tech debt** (identify and resolve early)
- 🎭 **Celebrate findings** (bugs found in tests = wins)

**Philosophy**:
> "Playwright tests are executable UX acceptance criteria. They validate functionality, prevent visual regressions, ensure accessibility, and help identify UX debt before it reaches users."

**Culture**:
> "Finding UI issues in Playwright tests is victory. Every bug caught here is a production incident or UAT delay prevented."

---

## References

**Playwright Documentation**:
- [Visual Comparisons](https://playwright.dev/docs/test-snapshots)
- [Accessibility Testing](https://playwright.dev/docs/accessibility-testing)
- [Trace Viewer](https://playwright.dev/docs/trace-viewer)
- [Best Practices](https://playwright.dev/docs/best-practices)

**UX Debt**:
- [Nielsen Norman Group: UX Debt](https://www.nngroup.com/articles/ux-debt/)

---

**Related**:
- [TDD Principles](../philosophy/tdd-principles.md) - Test-first approach
- [Testing Requirements](../standards/testing-requirements.md) - Test coverage standards
- [UAT Testing Guide](uat-testing-guide.md) - Manual UAT complements Playwright
- [Development Workflow](development-workflow.md) - Where Playwright fits in workflow
