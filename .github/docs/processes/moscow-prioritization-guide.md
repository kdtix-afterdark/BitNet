# MoSCoW Prioritization Guide

> **Priority-driven planning**: Apply MoSCoW method for requirements, roadmaps, releases, and sprints.

---

## Overview

MoSCoW is a prioritization framework for managing scope across different time horizons:

- **Must have**: Required for success, no workaround exists
- **Should have**: Important but increment can succeed without it
- **Could have**: Nice-to-have, first to drop under pressure
- **Won't have (this time)**: Explicitly out of scope

**Philosophy**: Start from "Won't" and justify promotions. Maintain contingency by keeping Must-haves ≤60% of capacity.

---

## Why MoSCoW?

### Benefits

✅ **Clear priorities**: Everyone knows what matters most  
✅ **Scope control**: "Won't" prevents scope creep  
✅ **Risk management**: Could items buffer schedule risks  
✅ **Transparent trade-offs**: Explicit about what's excluded  
✅ **Flexible planning**: Same item can shift by timeframe  

### When to Use MoSCoW

**✅ Use MoSCoW for**:
- Roadmap planning (quarterly/annual)
- Release planning (version milestones)
- Sprint planning (1-4 week iterations)
- Feature scoping (epics → stories)
- Risk management (identify critical path)

**❌ Don't use MoSCoW when**:
- All work is equally critical (rare)
- Priorities change too frequently (fix underlying issue first)
- Team size < 3 (simpler prioritization sufficient)

---

## MoSCoW Definitions

### Must Have

**Definition**: Required for success. Without it, the delivery is not viable.

**Criteria**:
- If not delivered, we **cancel** or **fail** the objective
- It's **illegal**, **unsafe**, or unviable without it
- No workaround exists (even painful/manual)

**Examples**:
- ✅ "User authentication" (can't launch without it)
- ✅ "Payment processing" (core business requirement)
- ✅ "GDPR compliance" (legal requirement)

**Not Must Have**:
- ❌ "Dark mode" (workaround: users adjust screen brightness)
- ❌ "Bulk export" (workaround: export one-by-one manually)
- ❌ "Performance optimization" (workaround: slower is acceptable)

**Questions to ask**:
1. Can we launch without this?
2. Is there a workaround (even if painful)?
3. Is it legally/safety required?
4. Will users abandon the product without it?

If answer to #1 is "Yes" or #2 is "Yes", it's **NOT** a Must.

---

### Should Have

**Definition**: Important, but the increment can succeed without it. A workaround exists.

**Criteria**:
- High value, but not critical path
- Workaround is painful but acceptable
- Can defer to next iteration without major impact

**Examples**:
- ✅ "Email notifications" (workaround: users check dashboard manually)
- ✅ "Search filters" (workaround: scroll through results)
- ✅ "Mobile responsive" (workaround: users can use desktop)

**When to downgrade from Must to Should**:
- Workaround exists but is tedious
- Feature is important for user satisfaction but not viability
- Can be delivered in next iteration without harm

---

### Could Have

**Definition**: Nice-to-have, valuable but not essential. First to drop when deadline threatened.

**Criteria**:
- Improves experience but not required
- Low effort, high value (quick wins)
- Buffer for schedule risk

**Examples**:
- ✅ "Keyboard shortcuts" (users can use mouse)
- ✅ "Tooltips" (users can learn through docs)
- ✅ "Animations" (functional without them)

**Strategic use of Could**:
- Keep ~20% of capacity as Could items
- Provides schedule buffer (drop if running late)
- Quick wins if ahead of schedule

---

### Won't Have (This Time)

**Definition**: Explicitly out of scope for this timeframe. Prevents scope creep.

**Criteria**:
- Valuable but not now (timing issue)
- Explicitly rejected for this window
- Documented to prevent repeated discussion

**Examples**:
- ✅ "Integration with Platform X" (deferred to Q3)
- ✅ "Advanced analytics" (deferred to v2.0)
- ✅ "Multi-language support" (won't do this year)

**Always specify**:
- **Won't in what window?** (this sprint? this release? this quarter?)
- **What happens next?** (revisit at next planning, or permanently rejected?)

**Template**:
```
Won't: [Feature name]
Timeframe: Sprint 23 / Q2 2026
Reason: Low ROI, focus on core features first
Revisit: Q3 planning cycle
```

---

## Three Planning Horizons

### Horizon 1: Roadmap (Project Level)

**Timeframe**: Quarter, half-year, or year  
**Artifacts**: Epics, initiatives, themes  
**Field**: `moscow_roadmap`

**Example**:
```yaml
Epic: User Dashboard Redesign
moscow_roadmap: Must
Timeframe: Q1 2026
Rationale: Core product differentiation, competitive requirement
Outcome: Increase user engagement by 30%
```

---

### Horizon 2: Release/Phase (Increment Level)

**Timeframe**: Version milestone, program increment (6-12 weeks)  
**Artifacts**: Features, story slices  
**Field**: `moscow_release`

**Example**:
```yaml
Epic: User Dashboard Redesign (same epic as above)
moscow_roadmap: Must
moscow_release: Should
Timeframe: Release 2.1 (Feb-Mar 2026)
Rationale: Phasing implementation; v2.1 ships core layout, v2.2 adds widgets
```

**Note**: Roadmap Must can be Release Should (sequencing/phasing).

---

### Horizon 3: Sprint (Timebox Level)

**Timeframe**: 1-4 week iteration  
**Artifacts**: User stories, tasks  
**Field**: `moscow_sprint`

**Example**:
```yaml
Story: Implement dashboard grid layout
moscow_roadmap: Must (part of Must epic)
moscow_release: Should (part of Should feature set)
moscow_sprint: Must
Sprint: Sprint 23
Rationale: Required for sprint goal "Basic dashboard functional"
```

---

## Agent Operating Rules

### Rule 1: Start from "Won't"

**Default every candidate item to "Won't (this time)"**, then promote with explicit rationale.

**Why**: Prevents scope creep, forces justification.

**Workflow**:
```
1. List all candidate items
2. Mark all as "Won't"
3. For each item, ask: "Why Must/Should/Could?"
4. Promote only with clear rationale
```

**Example**:
```markdown
## Backlog Items

All default to "Won't Sprint 23":

1. User authentication → Promote to Must (required for launch)
2. Dark mode → Promote to Could (nice-to-have, low effort)
3. Advanced analytics → Stay as Won't (defer to Q2)
```

---

### Rule 2: Must-Have Test

**For any proposed Must, answer these questions**:

1. **If not delivered, do we cancel/fail the objective?**
   - If no: Not a Must

2. **Is it illegal/unsafe/unviable without it?**
   - If no: Not a Must

3. **If a workaround exists (even painful), it's NOT a Must**
   - If workaround exists: Downgrade to Should

**Example evaluation**:

**Proposed Must**: "Bulk user export"

Q1: If not delivered, do we cancel launch?  
→ No, users can export one-by-one

Q2: Is it illegal/unsafe without it?  
→ No

Q3: Workaround exists?  
→ Yes, manual export (painful but possible)

**Result**: Downgrade to **Should** (workaround exists).

---

### Rule 3: Must Dependencies

**A Must item must not depend on anything lower than Must.**

**Why**: If Must depends on Should/Could, and that dependency slips, the Must fails.

**Fix**: Either promote dependency to Must, or downgrade dependent to Should.

**Example**:

❌ **Wrong**:
```
Must: Payment processing
  Depends on: API gateway (Should)
```

✅ **Fixed**:
```
Must: Payment processing
  Depends on: API gateway (Must)  ← Promoted to Must
```

Or:
```
Should: Payment processing  ← Downgraded to Should
  Depends on: API gateway (Should)
```

---

### Rule 4: Capacity Guardrails

**Target ≤60% of capacity as Must** to maintain contingency.

**Why**: Protects schedule from risks, unknowns, and interruptions.

**Recommended distribution**:
- **Must**: 50-60% of capacity (critical path)
- **Should**: 20-30% of capacity (important but flexible)
- **Could**: 10-20% of capacity (buffer, stretch goals)

**Example (10-person team, 2-week sprint, 40h/person = 800h total)**:
- Must: 480h (60% - critical features)
- Should: 200h (25% - important features)
- Could: 120h (15% - quick wins, buffer)

**If running late**: Drop Could first, then Should if necessary.

---

### Rule 5: "Won't" Must Be Time-Bounded

**"Won't" is ambiguous unless you specify the window.**

**Always document**:
- Won't in **what timeframe**? (this sprint? release? quarter?)
- **What happens next**? (revisit later? permanently rejected?)

**Template**:
```yaml
Item: Multi-language support
MoSCoW: Won't
Timeframe: Won't in Q1 2026
Reason: Focus on English market first, measure demand
Revisit: Q2 planning if international users >10%
Status: Active (will reconsider) | Rejected (permanently out)
```

---

## Planning Workflows

### Workflow 1: Roadmap Planning (Project Horizon)

**Goal**: Define quarterly/annual objectives.

**Steps**:

1. **List candidate epics/initiatives**
   ```
   Epic 1: User Dashboard Redesign
   Epic 2: Mobile App Launch
   Epic 3: API v2 Migration
   Epic 4: Advanced Analytics
   Epic 5: Multi-language Support
   ```

2. **Assign `moscow_roadmap` with rationale**
   ```yaml
   Epic 1: User Dashboard Redesign
     moscow_roadmap: Must
     Rationale: Competitive requirement, customer churn risk
     Outcome: Increase engagement 30%, reduce churn 15%
   
   Epic 2: Mobile App Launch
     moscow_roadmap: Should
     Rationale: Important for growth, but web is sufficient
     Outcome: 20% of users on mobile within 6 months
   
   Epic 3: API v2 Migration
     moscow_roadmap: Must
     Rationale: v1 deprecated June 2026, security risk
     Outcome: 100% traffic on v2 by May 2026
   
   Epic 4: Advanced Analytics
     moscow_roadmap: Could
     Rationale: Nice-to-have, low demand (5% of users)
     Outcome: 10% adoption if shipped
   
   Epic 5: Multi-language Support
     moscow_roadmap: Won't (Q1 2026)
     Rationale: English-only market focus, revisit Q2
     Revisit: Q2 if international users >10%
   ```

3. **Output**: Roadmap table

| Epic | MoSCoW | Quarter | Owner | Success Metric | Rationale |
|------|--------|---------|-------|----------------|-----------|
| Dashboard Redesign | Must | Q1 | Product | +30% engagement | Competitive requirement |
| Mobile App | Should | Q1-Q2 | Mobile | 20% mobile users | Growth opportunity |
| API v2 Migration | Must | Q1 | Backend | 100% on v2 | v1 deprecated June |
| Advanced Analytics | Could | Q2 | Data | 10% adoption | Low demand |
| Multi-language | Won't Q1 | Q2+ | Product | TBD | Revisit if demand |

---

### Workflow 2: Release/Phase Planning (Increment Horizon)

**Goal**: Define scope for version milestone (6-12 weeks).

**Steps**:

1. **Fix release window and capacity**
   ```
   Release: v2.1
   Dates: Feb 1 - Mar 15 (6 weeks)
   Team: 8 engineers × 6 weeks × 40h = 1,920h capacity
   Must cap: 1,152h (60%)
   ```

2. **Assign `moscow_release`** (may differ from roadmap)
   ```yaml
   Epic 1: Dashboard Redesign (Roadmap Must)
     moscow_release: Should
     Rationale: Phasing - v2.1 ships basic layout, v2.2 adds widgets
     Effort: 480h (25% of capacity)
   
   Epic 3: API v2 Migration (Roadmap Must)
     moscow_release: Must
     Rationale: Deadline June 2026, need 3 releases to complete
     Effort: 960h (50% of capacity) ← Must cap reached
   ```

3. **Break epics into story slices**
   ```
   Epic 3: API v2 Migration
     Story 1: Migrate authentication endpoints (Must, 200h)
     Story 2: Migrate user endpoints (Must, 300h)
     Story 3: Migrate data endpoints (Must, 300h)
     Story 4: Deprecation warnings (Should, 160h)
     Story 5: v1 shutdown automation (Could, 120h)
   ```

4. **Create Won't register**

| Item | Why Won't v2.1 | Revisit |
|------|----------------|---------|
| Dashboard widgets | Phasing | v2.2 |
| Mobile app | Capacity | v2.3+ |
| Advanced analytics | Low priority | Q2 |

5. **Output**: Release scope table

| Item | Type | MoSCoW | Effort | Notes |
|------|------|--------|--------|-------|
| API v2 auth | Story | Must | 200h | Critical path |
| API v2 users | Story | Must | 300h | Critical path |
| API v2 data | Story | Must | 300h | Critical path |
| Dashboard layout | Story | Should | 480h | Phased delivery |
| Deprecation warnings | Story | Should | 160h | Important for migration |
| v1 shutdown | Story | Could | 120h | Buffer |

---

### Workflow 3: Sprint Planning (Timebox Horizon)

**Goal**: Define scope for 1-4 week sprint.

**Steps**:

1. **Define sprint goal**
   ```
   Sprint 23 Goal: Complete API v2 authentication migration
   Duration: 2 weeks (Feb 1-14)
   Team: 8 engineers × 80h = 640h capacity
   Must cap: 384h (60%)
   ```

2. **Select stories and assign `moscow_sprint`**
   ```yaml
   Story 1: Migrate auth endpoints
     moscow_release: Must
     moscow_sprint: Must
     Effort: 200h
     Rationale: Sprint goal requires this
   
   Story 2: Add auth tests
     moscow_release: Must (implicit)
     moscow_sprint: Must
     Effort: 80h
     Rationale: Can't ship auth without tests
   
   Story 3: Update auth documentation
     moscow_release: Should
     moscow_sprint: Should
     Effort: 40h
     Rationale: Important but workaround exists (old docs)
   
   Story 4: Auth performance optimization
     moscow_release: Could
     moscow_sprint: Could
     Effort: 80h
     Rationale: Stretch goal, current performance acceptable
   ```

3. **Verify Must cap**
   ```
   Must effort: 280h (44% of 640h) ✅ Under 60% cap
   Should effort: 40h (6%)
   Could effort: 80h (13%)
   Remaining: 240h (37% buffer for unknowns)
   ```

4. **Output**: Sprint backlog

| Story | MoSCoW | Effort | Owner | Notes |
|-------|--------|--------|-------|-------|
| Migrate auth endpoints | Must | 200h | Backend | Sprint goal |
| Add auth tests | Must | 80h | QA | Required for quality |
| Update auth docs | Should | 40h | Docs | Workaround: old docs |
| Auth performance | Could | 80h | Backend | Stretch goal |
| **Total** | - | **400h** | - | 240h buffer (37%) |

---

### Workflow 4: End-of-Timebox Reassessment

**At sprint/release close, reassess scope.**

**Steps**:

1. **Confirm what shipped**
   ```yaml
   Sprint 23 Results:
     Migrated auth endpoints: ✅ Done
     Added auth tests: ✅ Done
     Updated auth docs: ✅ Done (bonus!)
     Auth performance: ❌ Not started (dropped as Could)
   ```

2. **Reclassify incomplete work** (don't auto-carry)
   ```yaml
   Auth performance optimization:
     Previous: Could (Sprint 23)
     Reassess: Should (Sprint 24)
     Rationale: Load tests show need, promote priority
   ```

3. **Update Won't register**
   ```
   Mobile app: Still Won't v2.1 (confirmed)
   Dashboard widgets: Still Won't v2.1 (confirmed)
   Advanced analytics: Promote from Won't Q1 to Could Q2 (new data)
   ```

4. **Lessons learned**
   ```
   - Auth migration took 20% longer than estimated
   - Buffer absorbed overrun successfully
   - Team velocity: 400h/sprint (50h/person/week)
   ```

---

## Templates

### Epic Template

```yaml
type: epic
id: EPIC-001
title: "User Dashboard Redesign"

timeframe:
  roadmap_window: "2026-Q1"
  release_window: "2026-02-01 to 2026-03-15"  # optional

moscow:
  roadmap: Must
  release: Should  # phased delivery

owner: "Product Team"

problem_statement: |
  Current dashboard is cluttered and slow. Users report 
  difficulty finding key information. Load time >5 seconds 
  causes frustration.

outcome_metric: |
  - Increase user engagement by 30%
  - Reduce load time to <2 seconds
  - Improve user satisfaction score from 6.5 to 8.0

non_goals:
  - Mobile app (separate epic)
  - Advanced analytics (deferred to Q2)

dependencies:
  - API v2 migration (must complete first)
  - Design system v2 (parallel effort)

risks:
  - Risk: Performance regression on old browsers
    Mitigation: Progressive enhancement approach

notes: |
  Phased delivery: v2.1 = layout, v2.2 = widgets, v2.3 = polish
```

### User Story Template

```yaml
type: story
id: STORY-042
title: "Implement dashboard grid layout"

epic: "EPIC-001: User Dashboard Redesign"

timeframe:
  sprint: "Sprint 23 (Feb 1-14)"
  release: "Release 2.1"

moscow:
  sprint: Must
  release: Should

acceptance_criteria:
  - "Given user loads dashboard, When page renders, Then grid layout displays in <2s"
  - "Given user resizes browser, When viewport changes, Then layout remains responsive"
  - "Given user has 10+ widgets, When grid loads, Then all widgets render correctly"

effort_estimate: "8 story points (40 hours)"

workaround_if_not_done: |
  Users continue with old dashboard (slow but functional).
  Since workaround exists, this is Should not Must at release level.

dependencies:
  - "STORY-041: Design system grid component"

test_notes:
  - "Unit tests for grid calculations"
  - "Visual regression tests for layout"
  - "Performance test: load time <2s"
```

### MoSCoW Scope Table

```markdown
| Item | Type | Timeframe | MoSCoW | Effort | Rationale | Notes |
|------|------|-----------|--------|--------|-----------|-------|
| API v2 auth | Story | Sprint 23 | Must | 200h | Sprint goal | Critical path |
| Auth tests | Story | Sprint 23 | Must | 80h | Quality gate | Required |
| Auth docs | Story | Sprint 23 | Should | 40h | Workaround exists | Nice-to-have |
| Auth perf | Story | Sprint 23 | Could | 80h | Current OK | Stretch |
| Dashboard layout | Story | Sprint 24 | Must | 120h | Core redesign | Next sprint |
```

### "Won't (This Time)" Register

```markdown
| Item | Timeframe Won't Ship | Why Not Now | Revisit On | Owner | Status |
|------|---------------------|-------------|------------|-------|--------|
| Mobile app | Q1 2026 | Focus on web first | Q2 planning | Mobile team | Active |
| Multi-language | 2026 | English market only | Q3 if demand >10% | Product | Active |
| Advanced analytics | Release 2.1 | Low ROI (5% users) | Release 2.3 | Data team | Active |
| Legacy API v1 | Never | Deprecated June 2026 | N/A | Backend | Rejected |
```

---

## Integration with Issue Tracking

### Jira Custom Fields

**Add custom fields**:
```
moscow_roadmap: Must | Should | Could | Won't
moscow_release: Must | Should | Could | Won't | TBD
moscow_sprint: Must | Should | Could | Won't
```

**JQL queries**:
```sql
-- All Must items for current sprint
sprint = 23 AND moscow_sprint = "Must"

-- Roadmap Must items not yet in a release
moscow_roadmap = "Must" AND moscow_release is EMPTY

-- Could items (candidates to drop)
sprint = 23 AND moscow_sprint = "Could"

-- Won't items to revisit
moscow_sprint = "Won't" AND labels = "revisit-q2"
```

---

### Confluence Documentation

**Document MoSCoW decisions in Confluence**:

```markdown
# Release 2.1 Scope

## Must Have (60% capacity)
- API v2 authentication migration (EPIC-001)
- Security vulnerability fixes (STORY-099)

## Should Have (25% capacity)
- Dashboard layout redesign (EPIC-002, phased)
- Deprecation warnings (STORY-105)

## Could Have (15% capacity)
- Performance optimizations (STORY-110)
- UI polish (STORY-115)

## Won't Have (This Release)
- Mobile app → Deferred to v2.3
- Advanced analytics → Deferred to Q2
- Multi-language → Won't in 2026, revisit 2027

**Capacity**: 1,920h total, 1,152h Must (60%), 480h Should (25%), 288h Could (15%)

**Rationale**: Focus on API migration (legal deadline) and core dashboard (competitive requirement).
```

---

## Best Practices

### Planning

✅ **Start from Won't**: Default to out-of-scope, justify promotions  
✅ **Must-have test**: Apply 3 questions rigorously  
✅ **Check dependencies**: Must can't depend on Should/Could  
✅ **Maintain contingency**: Must ≤60% of capacity  
✅ **Document Won't**: Time-bound and specify revisit criteria  

### Execution

✅ **Protect Musts**: Don't let them slip (they define success)  
✅ **Flexible Shoulds**: Can defer if necessary (workaround exists)  
✅ **Drop Coulds early**: When deadline threatened, drop Could first  
✅ **Reassess often**: Update MoSCoW based on learnings  

### Communication

✅ **Transparent priorities**: Share MoSCoW with all stakeholders  
✅ **Explicit trade-offs**: Document why items are Won't  
✅ **Celebrate drops**: Dropping Could to protect Must is good  
✅ **No surprises**: Communicate MoSCoW changes immediately  

---

## Real-World Example

### Scenario: New Feature Development

**Epic**: User Dashboard Redesign

**Roadmap Planning (Q1 2026)**:
```yaml
moscow_roadmap: Must
Rationale: Competitive requirement, customer churn risk
Capacity: 800h (2 engineers, 12 weeks)
```

**Release Planning (v2.1, 6 weeks)**:
```yaml
moscow_release: Should (phased delivery)
Rationale: v2.1 ships basic layout, v2.2 adds widgets
Capacity: 480h (phased: 240h this release)

Must items (60% = 144h):
  - Grid layout component (120h)
  - Basic responsive design (24h)

Should items (25% = 60h):
  - Widget placeholders (40h)
  - Error states (20h)

Could items (15% = 36h):
  - Animations (24h)
  - Tooltips (12h)

Won't (this release):
  - Widget library (deferred to v2.2)
  - Advanced customization (deferred to v2.3)
```

**Sprint Planning (Sprint 23, 2 weeks)**:
```yaml
Sprint Goal: Functional dashboard layout

Must items (60% = 48h of 80h per engineer):
  - Implement grid layout (40h)
  - Unit tests (8h)

Should items (25% = 20h):
  - Visual regression tests (12h)
  - Documentation (8h)

Could items (15% = 12h):
  - Animation polish (12h)

Buffer: 20h (25% - unknowns, bugs)
```

**Result**:
- All Must items shipped ✅
- All Should items shipped ✅ (team efficient)
- Could items started but not finished (acceptable)
- Buffer used for unexpected complexity in grid layout

---

## Quick Reference

### MoSCoW Decision Tree

```
Is there a workaround (even painful)?
├─ No → Could be Must (apply 3 questions)
│  ├─ Would we cancel without it? → Must
│  ├─ Is it illegal/unsafe without it? → Must
│  └─ Otherwise → Should
└─ Yes → Not a Must
   ├─ Workaround is painful → Should
   ├─ Workaround is acceptable → Could
   └─ Not needed this timeframe → Won't
```

### Capacity Guardrails

| MoSCoW | Target % | Purpose |
|--------|----------|---------|
| Must | 50-60% | Critical path, no compromise |
| Should | 20-30% | Important, some flexibility |
| Could | 10-20% | Buffer, stretch goals |
| Won't | Tracked | Prevent scope creep |

### 3 Must-Have Questions

1. **Cancel test**: Would we cancel/fail without it?
2. **Legal/safety test**: Is it illegal/unsafe without it?
3. **Workaround test**: Can we work around it (even painfully)?

If #3 is "Yes", it's **NOT** a Must.

---

## Key Takeaways

**Remember**:
- 🎯 **Start from Won't** - justify promotions, not demotions
- 🎯 **Must = no workaround** - if workaround exists, it's Should
- 🎯 **Keep Must ≤60%** - maintain contingency for risks
- 🎯 **Could = buffer** - first to drop when deadline threatened
- 🎯 **Time-bound Won't** - specify window and revisit criteria

**Philosophy**:
> "MoSCoW forces honest conversations about priority. Must means 'we cancel without it', not 'we really want it'. Discipline in applying the framework prevents scope creep and protects delivery predictability."

**Culture**:
> "Celebrate saying no. Dropping a Could to protect a Must is good prioritization, not failure. Won't (this time) is an active decision, not a passive rejection."

---

## References

**Authoritative sources**:
- [Agile Business Consortium - MoSCoW Prioritisation](https://www.agilebusiness.org/dsdm-project-framework/moscow-prioritisation.html)
- [Agile Business Consortium - Timeboxing](https://www.agilebusiness.org/dsdm-project-framework/13-timeboxing.html)
- [Atlassian - Prioritization Frameworks](https://www.atlassian.com/agile/product-management/prioritization-framework)

---

**Related**:
- [Development Workflow](development-workflow.md) - Phase 0: MoSCoW in planning
- [Documentation & Tracking Guide](documentation-tracking-guide.md) - Document MoSCoW in Jira/Confluence
- [Proper Discovery](../philosophy/proper-discovery.md) - Research before prioritizing
- [Celebrate Early Discovery](../philosophy/celebrate-early-discovery.md) - Celebrate dropping Could items early
