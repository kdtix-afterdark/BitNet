# UAT Testing Guide

> **User Acceptance Testing**: Real-world scenarios with realistic data to verify features work as expected.

---

## What is UAT?

**UAT (User Acceptance Testing)**: Manual testing with real or realistic data to verify:
- Features work in real-world scenarios
- Edge cases are handled
- User workflows are smooth
- Cross-platform compatibility
- Performance meets expectations

**UAT is NOT**:
- Unit testing (covered by automated tests)
- Exploratory testing (UAT has defined scenarios)
- Performance testing (separate activity)
- Security testing (separate activity)

---

## When to Run UAT

### Required UAT Scenarios

**Always run UAT for**:
- ✅ **New features** (verify real-world usage)
- ✅ **Major changes** (verify backward compatibility)
- ✅ **Bug fixes** (verify fix works in production-like environment)
- ✅ **Cross-platform code** (verify on all target platforms)
- ✅ **User-facing APIs** (verify usability)

### Optional UAT

**Consider UAT for**:
- Internal refactoring (if risk of behavioral changes)
- Performance improvements (measure before/after)
- Documentation updates (verify examples work)

---

## UAT Process

### Step 1: Create Test Scenarios

**Template**:
```markdown
## UAT Scenario: [Descriptive Name]

**Goal**: [What are we verifying?]

**Prerequisites**:
- [Environment setup]
- [Test data needed]
- [Configuration requirements]

**Steps**:
1. [Action 1]
2. [Action 2]
3. [Action 3]

**Expected Results**:
- [Expected outcome 1]
- [Expected outcome 2]

**Actual Results**:
- [What actually happened]
- [Bugs found (celebrate! 🎉)]
```

### Step 2: Set Up Test Environment

**Environment checklist**:
- [ ] **Staging/test instance** (not production!)
- [ ] **Test data prepared** (realistic but safe)
- [ ] **Credentials configured** (test accounts)
- [ ] **Network access** (if external APIs)
- [ ] **Logging enabled** (for debugging)

### Step 3: Execute Scenarios

**Execution tips**:
- Follow scenarios exactly as written
- Document deviations or unexpected behavior
- Take screenshots/videos if helpful
- Record timing for performance-sensitive operations
- Celebrate bugs found! 🎉

### Step 4: Document Results

**For each scenario**:
- ✅ **Pass**: Works as expected
- ❌ **Fail**: Doesn't work, bug found (celebrate!)
- ⏳ **Blocked**: Can't test (dependency issue)

**Document failures**:
```markdown
**Actual Results**:
- ❌ Timeout after 30 seconds (expected: complete within 60s)
- ❌ File integrity check failed (checksum mismatch)

**Bugs Found**:
- #42: Upload timeout too short for large files
- #43: Checksum calculation incorrect for binary files

**Status**: Bugs logged, fixes in progress
```

### Step 5: Fix Bugs & Re-test

**Bug fix workflow**:
1. Create issue/ticket for bug
2. Fix bug (TDD approach)
3. Run unit tests (verify fix)
4. Re-run UAT scenario (verify in real-world)
5. Update UAT results (mark as passed ✅)

### Step 6: Stakeholder Sign-off

**Get approval from**:
- Product owner (feature works as requested)
- QA team (quality standards met)
- Platform owners (if cross-platform)

---

## UAT Scenario Templates

### Template 1: Basic Feature Test

```markdown
## UAT Scenario: [Feature Name] - Happy Path

**Goal**: Verify [feature] works with valid inputs

**Prerequisites**:
- Test environment running
- Test data: [describe data]

**Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Results**:
- [Expected 1]
- [Expected 2]

**Actual Results**:
- ✅ [Actual 1]
- ✅ [Actual 2]

**Status**: ✅ PASSED
```

### Template 2: Error Handling Test

```markdown
## UAT Scenario: [Feature Name] - Error Handling

**Goal**: Verify [feature] handles errors gracefully

**Prerequisites**:
- Test environment running
- Invalid test data: [describe data]

**Steps**:
1. Provide invalid input: [describe]
2. Trigger error condition
3. Observe error message

**Expected Results**:
- Clear error message displayed
- No crash or hang
- System remains stable

**Actual Results**:
- ✅ Error message: "[error text]"
- ✅ System stable, no crash

**Status**: ✅ PASSED
```

### Template 3: Performance Test

```markdown
## UAT Scenario: [Feature Name] - Performance

**Goal**: Verify [feature] meets performance requirements

**Prerequisites**:
- Test environment running
- Large dataset: [describe size]

**Steps**:
1. Start timer
2. Execute operation
3. Measure completion time

**Expected Results**:
- Operation completes within [X seconds]
- Memory usage reasonable (<[Y MB])

**Actual Results**:
- ⏱️ Completion time: [X.X seconds]
- 💾 Memory usage: [X MB]

**Status**: ✅ PASSED (within requirements)
```

### Template 4: Cross-Platform Test

```markdown
## UAT Scenario: [Feature Name] - Cross-Platform

**Goal**: Verify [feature] works on all target platforms

**Prerequisites**:
- Test on each platform: [list platforms]
- Same test data across platforms

**Steps**:
1. Run on Platform 1
2. Run on Platform 2
3. Compare results

**Expected Results**:
- Identical behavior across platforms
- No platform-specific bugs

**Actual Results**:
**Platform 1 (Windows)**:
- ✅ Works as expected

**Platform 2 (Linux)**:
- ✅ Works as expected

**Platform 3 (macOS)**:
- ✅ Works as expected

**Status**: ✅ PASSED (all platforms)
```

---

## Real-World Example: Confluence Attachments

### UAT Scenario 1: Upload Single Attachment

```markdown
## UAT Scenario: Upload Single Attachment

**Goal**: Verify single file upload works with real Confluence page

**Prerequisites**:
- Confluence test instance running
- Test page created (ID: 123456)
- Test file: sample.pdf (1.2 MB)

**Steps**:
1. Call `upload_attachment(page_id=123456, filepath="sample.pdf")`
2. Verify response contains attachment ID
3. Check Confluence UI for uploaded file

**Expected Results**:
- API returns success response with attachment ID
- File appears in Confluence page attachments
- File size matches original (1.2 MB)

**Actual Results**:
- ✅ API response: `{"id": "att123", "size": 1258291, "title": "sample.pdf"}`
- ✅ File visible in Confluence UI
- ✅ File size: 1,258,291 bytes (matches)

**Status**: ✅ PASSED
```

### UAT Scenario 2: Batch Upload

```markdown
## UAT Scenario: Batch Upload Multiple Attachments

**Goal**: Verify batch upload of 3 files works

**Prerequisites**:
- Test page (ID: 123456)
- Test files:
  * document.docx (45 KB)
  * image.png (230 KB)
  * data.xlsx (12 KB)

**Steps**:
1. Call `upload_attachments(page_id=123456, filepaths=[...])`
2. Verify all 3 files uploaded
3. Check Confluence UI

**Expected Results**:
- All 3 files upload successfully
- Each file has unique attachment ID
- All files visible in Confluence

**Actual Results**:
- ✅ 3/3 files uploaded
- ✅ IDs: att124, att125, att126
- ✅ All visible in Confluence

**Status**: ✅ PASSED
```

### UAT Scenario 3: Download Attachment

```markdown
## UAT Scenario: Download Attachment

**Goal**: Verify attachment download works

**Prerequisites**:
- Attachment uploaded (ID: att123)
- Expected size: 1,258,291 bytes

**Steps**:
1. Call `download_attachment(attachment_id="att123", target_path="./downloads/")`
2. Verify file downloaded
3. Compare checksum with original

**Expected Results**:
- File downloads successfully
- File size matches expected
- Checksum matches original file

**Actual Results**:
- ❌ Download failed: "Attachment not found" (BUG FOUND 🎉)

**Bugs Found**:
- #44: Download method doesn't support relative URLs from API

**Status**: ❌ FAILED (bug logged, fix in progress)
```

### UAT Scenario 3 (Re-test after fix)

```markdown
## UAT Scenario: Download Attachment (Re-test)

**Goal**: Verify download works after bug fix

**Prerequisites**:
- Bug #44 fixed (prepend base URL to relative URLs)
- Attachment uploaded (ID: att123)

**Steps**:
1. Call `download_attachment(attachment_id="att123", target_path="./downloads/")`
2. Verify file downloaded
3. Compare size with expected

**Expected Results**:
- File downloads successfully
- File size matches expected (1,258,291 bytes)

**Actual Results**:
- ✅ File downloaded: downloads/sample.pdf
- ✅ File size: 1,258,291 bytes (matches!)

**Status**: ✅ PASSED (bug fixed!)
```

---

## UAT Best Practices

### Scenario Design

- ✅ **Real-world scenarios** (not just unit test cases)
- ✅ **Realistic data** (production-like volumes/complexity)
- ✅ **Happy path + error path** (test both success and failure)
- ✅ **Edge cases** (boundary conditions, limits)
- ✅ **Cross-platform** (test on all target platforms)

### Execution

- ✅ **Follow scenarios exactly** (consistency)
- ✅ **Document everything** (screenshots, logs, timing)
- ✅ **Celebrate bugs found** (finding bugs = winning)
- ✅ **Re-test after fixes** (verify bug is resolved)
- ✅ **Fresh environment** (avoid state pollution)

### Documentation

- ✅ **Clear expected results** (unambiguous)
- ✅ **Detailed actual results** (what really happened)
- ✅ **Bug references** (link to issues/tickets)
- ✅ **Timing data** (performance metrics)
- ✅ **Platform details** (OS, version, environment)

---

## Roles and Responsibilities

### Developer Responsibilities

- ✅ **Create UAT scenarios** (based on requirements)
- ✅ **Execute UAT** (if no separate QA team)
- ✅ **Fix bugs found** (prioritize UAT findings)
- ✅ **Re-test after fixes** (verify resolution)
- ✅ **Document results** (pass/fail/blocked)

### QA Team Responsibilities (if separate)

- ✅ **Review UAT scenarios** (ensure coverage)
- ✅ **Execute UAT independently** (fresh eyes)
- ✅ **Report bugs found** (celebrate findings!)
- ✅ **Verify bug fixes** (re-test scenarios)
- ✅ **Sign off on quality** (approve for release)

### Product Owner Responsibilities

- ✅ **Review scenarios** (ensure requirements met)
- ✅ **Provide test data** (realistic examples)
- ✅ **Final sign-off** (approve feature)

---

## UAT Checklist

### Before UAT

- [ ] **Scenarios written** (all major features covered)
- [ ] **Environment ready** (staging/test instance)
- [ ] **Test data prepared** (realistic but safe)
- [ ] **Credentials configured** (test accounts)
- [ ] **Baseline established** (know expected behavior)

### During UAT

- [ ] **Execute scenarios** (follow steps exactly)
- [ ] **Document results** (pass/fail/blocked)
- [ ] **Celebrate bugs found** (finding bugs = winning 🎉)
- [ ] **Log bugs immediately** (don't defer)
- [ ] **Take notes** (observations, timing, issues)

### After UAT

- [ ] **Fix critical bugs** (blocking issues first)
- [ ] **Re-test fixed scenarios** (verify fixes work)
- [ ] **Update documentation** (if behavior changed)
- [ ] **Get sign-off** (stakeholder approval)
- [ ] **Archive results** (for future reference)

---

## Celebrate Early Discovery

**UAT Philosophy**: Finding bugs during UAT is a VICTORY 🎉

**Why celebrate UAT bugs**:
- Found before production (no user impact)
- Found in realistic scenarios (validates testing approach)
- Fixed while context fresh (faster resolution)
- Demonstrates rigorous quality process

**Examples of UAT wins**:
- 🎉 **Windows UAT found 5 bugs** → All fixed before merge
- 🎉 **iOS UAT found cross-platform path issues** → Fixed in 30 minutes
- 🎉 **Performance UAT revealed timeout** → Increased from 30s to 120s
- 🎉 **Error handling UAT caught poor error message** → Improved UX

**Don't hide UAT findings**:
- ❌ "We found some small issues" (downplaying)
- ✅ "UAT found 5 bugs—all fixed within 2 hours!" (celebrating)

---

## Key Takeaways

**Remember**:
- 📋 **UAT verifies real-world usage** (not just unit tests)
- 📋 **Use realistic data** (production-like scenarios)
- 📋 **Test on all platforms** (if cross-platform)
- 📋 **Document everything** (for traceability)
- 📋 **Celebrate bugs found** (early discovery wins)

**Philosophy**:
> "UAT is the bridge between unit tests and production. It catches issues that automated tests miss and validates that features work as users expect."

**Culture**:
> "Finding bugs during UAT is not failure—it's success. Every bug found here is a production incident prevented."

---

**Related**:
- [Celebrate Early Discovery](../philosophy/celebrate-early-discovery.md) - Celebrate UAT findings
- [Development Workflow](development-workflow.md) - Phase 6: UAT Testing
- [Independent Verification](../philosophy/independent-verification.md) - Why UAT matters
- [Testing Requirements](../standards/testing-requirements.md) - UAT vs unit tests
