# Documentation & Tracking Guide

> **Unified workflow**: Use Confluence, Jira, Azure DevOps, and GitHub effectively for documentation and issue tracking.

---

## Overview

Effective software development requires coordinated documentation and issue tracking across multiple platforms:

- **Confluence**: Technical documentation, design docs, runbooks, team knowledge
- **Jira**: Issue tracking, sprint planning, workflow management
- **Azure DevOps (ADO)**: Microsoft ecosystem integration, boards, repos
- **GitHub**: Code repositories, pull requests, project management

**Philosophy**: Document early, track everything, maintain single source of truth per domain.

---

## Documentation Strategy

### What to Document Where

**Confluence** (Long-form documentation):
- ✅ Architecture decisions (ADRs)
- ✅ Design documents
- ✅ API documentation
- ✅ Runbooks and playbooks
- ✅ Team processes
- ✅ Onboarding guides
- ✅ Meeting notes
- ✅ Project retrospectives

**GitHub/ADO** (Code-adjacent documentation):
- ✅ README.md (project overview)
- ✅ CONTRIBUTING.md (contribution guide)
- ✅ CHANGELOG.md (version history)
- ✅ Code comments (inline documentation)
- ✅ Pull request descriptions
- ✅ Issue templates

**When to use which**:
- **Confluence**: Documentation that changes infrequently, needs rich formatting, accessed by non-developers
- **GitHub/ADO**: Documentation that changes with code, needs version control, accessed by developers

---

## Part 1: Confluence MCP Tools

### Available Tools

**MCP Atlassian provides**:
1. `confluence_create_page` - Create new documentation
2. `confluence_update_page` - Update existing docs
3. `confluence_get_page` - Retrieve page content
4. `confluence_search` - Find documentation
5. `confluence_list_pages` - Browse space contents
6. `confluence_upload_attachment` - Add files to pages
7. `confluence_download_attachment` - Retrieve attachments
8. `confluence_list_attachments` - View page attachments

### Creating Documentation

**Use case**: Document a new feature

**Workflow**:
```markdown
## Step 1: Search for existing documentation

Use: confluence_search
Query: "authentication API"
Goal: Avoid duplicating existing docs

## Step 2: Create or update page

Option A - New page:
Use: confluence_create_page
Space: "ENGINEERING"
Title: "Authentication API v2"
Content: |
  # Authentication API v2
  
  ## Overview
  New OAuth 2.0 authentication flow...
  
  ## Endpoints
  - POST /api/v2/auth/login
  - POST /api/v2/auth/refresh
  
  ## Examples
  ...

Option B - Update existing:
Use: confluence_update_page
Page ID: 123456
Content: Updated documentation...

## Step 3: Add supporting files

Use: confluence_upload_attachment
Page ID: 123456
Files:
  - api-flow-diagram.png
  - postman-collection.json
  - example-responses.json
```

### Documentation Templates

**Architecture Decision Record (ADR)**:
```markdown
# ADR-001: Use OAuth 2.0 for Authentication

**Status**: Accepted
**Date**: 2026-02-06
**Context**: Need secure authentication for public API

## Decision
Implement OAuth 2.0 with JWT tokens

## Consequences
**Positive**:
- Industry standard
- Strong security
- Easy integration

**Negative**:
- More complex than API keys
- Requires token refresh logic

## Alternatives Considered
- API keys (rejected: less secure)
- Basic auth (rejected: credentials in every request)
```

**Design Document Template**:
```markdown
# Feature: User Dashboard Redesign

**Author**: Engineering Team
**Date**: 2026-02-06
**Status**: In Review

## Problem Statement
Current dashboard is cluttered and slow

## Goals
- Reduce load time by 50%
- Improve user navigation
- Mobile-responsive design

## Proposed Solution
### Architecture
[Diagram attachment: architecture.png]

### Components
- Dashboard Layout (React)
- Widget System (pluggable)
- Data API (GraphQL)

## Implementation Plan
Phase 1: Prototype (2 weeks)
Phase 2: User testing (1 week)
Phase 3: Production (3 weeks)

## Success Metrics
- Load time < 2 seconds
- Mobile score > 90 (Lighthouse)
- User satisfaction > 8/10
```

**Runbook Template**:
```markdown
# Runbook: Handling Production Outages

**Last Updated**: 2026-02-06
**Owner**: DevOps Team

## Symptoms
- API returning 503 errors
- Database connection timeouts
- High memory usage

## Diagnosis Steps
1. Check health endpoint: https://api.example.com/health
2. Review logs: kubectl logs -n production api-pod
3. Check database: pg_stat_activity query

## Resolution Steps
### Scenario 1: Database connection pool exhausted
1. Scale up connection pool
2. Restart API pods
3. Monitor recovery

### Scenario 2: Memory leak
1. Identify leaking pod
2. Restart affected pods
3. Investigate memory dump

## Escalation
- Severity 1: Page on-call engineer immediately
- Severity 2: Notify team lead within 1 hour
```

### Best Practices

**Documentation quality**:
- ✅ **Title clarity**: Descriptive, searchable titles
- ✅ **Table of contents**: For long documents
- ✅ **Version info**: Last updated date, author
- ✅ **Examples**: Code samples, screenshots, diagrams
- ✅ **Status**: Draft, In Review, Published, Deprecated

**Organization**:
- ✅ **Consistent structure**: Use templates
- ✅ **Clear hierarchy**: Spaces → Pages → Child Pages
- ✅ **Labels/tags**: For discoverability
- ✅ **Cross-references**: Link related docs

**Maintenance**:
- ✅ **Review cycle**: Quarterly review of all docs
- ✅ **Deprecation**: Mark outdated docs clearly
- ✅ **Archive**: Move old docs to archive space
- ✅ **Ownership**: Assign owner to each page

---

## Part 2: Jira MCP Tools

### Available Tools

**MCP Atlassian provides**:
1. `jira_create_issue` - Create tickets
2. `jira_update_issue` - Update ticket details
3. `jira_get_issue` - Retrieve issue info
4. `jira_search` - Find issues (JQL)
5. `jira_add_comment` - Comment on issues
6. `jira_transition_issue` - Move through workflow
7. `jira_assign_issue` - Assign to team members
8. `jira_add_worklog` - Log time spent

### Issue Tracking Workflow

**Bug tracking**:
```markdown
## Step 1: Create bug ticket

Use: jira_create_issue
Project: ENGINEERING
Type: Bug
Summary: "API returns 500 on large file upload"
Description: |
  **Environment**: Production
  **Reproducible**: Yes
  **Steps**:
  1. Upload file > 100MB
  2. API returns 500 error
  
  **Expected**: Upload succeeds
  **Actual**: 500 Internal Server Error
  
  **Logs**: [See attachment]
  
Priority: High
Labels: api, production, file-upload

## Step 2: Investigation

Use: jira_add_comment
Comment: |
  Root cause: Timeout after 30 seconds
  Fix: Increase timeout to 120 seconds
  
Use: jira_add_worklog
Time: 1h
Description: "Investigated root cause"

## Step 3: Link to documentation

Comment: |
  Fix documented in Confluence:
  https://confluence.example.com/pages/123456

## Step 4: Transition to resolved

Use: jira_transition_issue
Status: Resolved
Resolution: Fixed
```

**Feature tracking**:
```markdown
## Epic: User Dashboard Redesign

Use: jira_create_issue
Type: Epic
Summary: "User Dashboard Redesign"
Description: |
  Redesign user dashboard for better UX and performance
  
  **Goals**:
  - Reduce load time by 50%
  - Mobile-responsive design
  - Improved navigation
  
  **Design Doc**: [Confluence link]
  
Target: Q1 2026

## Stories under epic

Story 1:
Use: jira_create_issue
Type: Story
Parent: [Epic ID]
Summary: "Implement new dashboard layout"
Points: 8
Acceptance Criteria: |
  - [ ] Responsive grid layout implemented
  - [ ] Loads in < 2 seconds
  - [ ] Passes Lighthouse audit (>90)

Story 2:
Summary: "Migrate widgets to new system"
Points: 5
...
```

### JQL Search Examples

**Find your open issues**:
```
assignee = currentUser() AND status != Done
```

**Find bugs in current sprint**:
```
type = Bug AND sprint in openSprints()
```

**Find high-priority items**:
```
priority in (High, Highest) AND status != Done
```

**Find stale issues**:
```
status = "In Progress" AND updated < -14d
```

**Complex query**:
```
project = ENGINEERING 
AND type in (Bug, Story) 
AND status in ("To Do", "In Progress") 
AND (priority = High OR labels = production)
ORDER BY priority DESC, created ASC
```

### Jira Workflows

**Standard workflow**:
```
To Do → In Progress → Code Review → Testing → Done
```

**Transitions**:
1. **Start work**: To Do → In Progress
   ```
   Use: jira_transition_issue
   Status: "In Progress"
   ```

2. **Submit for review**: In Progress → Code Review
   ```
   Use: jira_transition_issue
   Status: "Code Review"
   Comment: "PR #123 ready for review"
   ```

3. **Move to testing**: Code Review → Testing
   ```
   Use: jira_transition_issue
   Status: "Testing"
   Comment: "Deployed to staging"
   ```

4. **Mark done**: Testing → Done
   ```
   Use: jira_transition_issue
   Status: "Done"
   Resolution: "Fixed"
   ```

### Best Practices

**Ticket quality**:
- ✅ **Clear summary**: Describes the issue in one line
- ✅ **Detailed description**: What, why, expected vs actual
- ✅ **Acceptance criteria**: How to verify it's done
- ✅ **Priority**: Reflects actual urgency
- ✅ **Labels**: For categorization and filtering

**Linking**:
- ✅ **Related issues**: Link bugs to stories, stories to epics
- ✅ **Documentation**: Link to Confluence pages
- ✅ **Code**: Reference commits/PRs in comments
- ✅ **Dependencies**: Block/blocked by relationships

**Communication**:
- ✅ **Regular updates**: Comment on progress
- ✅ **Blockers**: Call out impediments immediately
- ✅ **Decisions**: Document key decisions in comments
- ✅ **Mentions**: @mention people for visibility

---

## Part 3: Azure DevOps (ADO)

### Overview

**Azure DevOps components**:
- **Boards**: Work item tracking (similar to Jira)
- **Repos**: Git repositories
- **Pipelines**: CI/CD automation
- **Test Plans**: Test case management
- **Artifacts**: Package management

### When to Use ADO

**✅ Use ADO when**:
- Organization standardizes on Microsoft tools
- Integrating with Azure cloud services
- Need tight integration with Visual Studio
- Prefer unified platform (boards + repos + pipelines)

**❌ Use Jira + GitHub when**:
- Team prefers best-of-breed tools
- Already using GitHub for code
- Need flexibility in tool selection

### Work Item Tracking

**Work item types**:
```
Epic
├─ Feature
   ├─ User Story
   │  ├─ Task
   │  └─ Bug
   └─ User Story
      └─ Task
```

**Creating work items**:
```bash
# Epic
az boards work-item create \
  --type Epic \
  --title "User Dashboard Redesign" \
  --description "Redesign dashboard for better UX" \
  --project "MyProject"

# User Story (linked to epic)
az boards work-item create \
  --type "User Story" \
  --title "Implement dashboard layout" \
  --description "Create responsive grid layout" \
  --project "MyProject" \
  --relation Parent \
  --relation-type Parent \
  --relation-id 123  # Epic ID
```

**Querying work items**:
```sql
-- WIQL (Work Item Query Language)
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.AssignedTo] = @Me
  AND [System.State] <> 'Done'
  AND [System.WorkItemType] IN ('User Story', 'Bug')
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

### Linking ADO to Repos

**In commit messages**:
```bash
git commit -m "Fix login timeout issue

Increased timeout from 30s to 120s for large file uploads.
Fixes #123"  # Links to work item 123
```

**In pull requests**:
```markdown
# Pull Request Title
Fix login timeout issue (AB#123)

## Changes
- Increased timeout configuration
- Added retry logic

## Linked Work Items
- Fixes AB#123: API returns 500 on large file upload
```

### ADO Best Practices

**Organization**:
- ✅ **Clear area paths**: Team/product hierarchy
- ✅ **Sprint planning**: 2-week sprints (standard)
- ✅ **Capacity planning**: Track team velocity
- ✅ **Dashboards**: Team visibility into progress

**Integration**:
- ✅ **CI/CD triggers**: Auto-update work items from pipelines
- ✅ **Test integration**: Link test cases to user stories
- ✅ **Code coverage**: Track coverage in work items

---

## Part 4: GitHub

### Issues & Project Management

**GitHub Issues** (lightweight tracking):
```markdown
## Creating an issue

Title: "Add dark mode support"

Description:
## Feature Request
Add dark mode toggle to user preferences

**User Story**:
As a user, I want to enable dark mode so that I can reduce eye strain

**Acceptance Criteria**:
- [ ] Toggle in user settings
- [ ] Persists across sessions
- [ ] Applies to all pages
- [ ] Smooth transition animation

**Related**:
- Design: [Figma link]
- Discussion: #45
```

**GitHub Projects** (Kanban boards):
```
Backlog → Ready → In Progress → Review → Done
```

**Linking issues to PRs**:
```markdown
# Pull Request: Add dark mode support

Closes #123
Fixes #124
Relates to #125

## Changes
- Added dark mode CSS variables
- Implemented toggle component
- Updated user preferences API

## Testing
- [ ] Tested on Chrome, Firefox, Safari
- [ ] Verified persistence
- [ ] Checked all pages
```

### GitHub Discussions

**Use for**:
- ✅ Feature brainstorming
- ✅ Architecture discussions
- ✅ Q&A (community support)
- ✅ Announcements

**Don't use for**:
- ❌ Bug tracking (use Issues)
- ❌ Formal documentation (use Confluence)
- ❌ Sprint planning (use Jira/ADO)

### GitHub vs Jira/ADO

| Feature | GitHub Issues | Jira/ADO |
|---------|---------------|----------|
| **Best for** | Code-related tasks | Complex workflows |
| **Workflow** | Simple (columns) | Advanced (statuses, transitions) |
| **Estimation** | Labels/projects | Story points, velocity |
| **Reporting** | Basic | Advanced (burndown, velocity) |
| **Integration** | Native with GitHub | Requires setup |
| **Learning curve** | Low | Medium-High |

**Recommendation**:
- **Small teams**: GitHub Issues (simpler)
- **Large teams**: Jira/ADO (more features)
- **Hybrid**: Jira for planning, GitHub for code tasks

---

## Unified Workflow Example

### Scenario: Implementing a New Feature

**Phase 1: Planning & Documentation**

1. **Confluence**: Create design document
   ```
   Use: confluence_create_page
   Space: ENGINEERING
   Title: "Feature: Dark Mode Support"
   Content: [Design doc with architecture]
   
   Use: confluence_upload_attachment
   Files: design-mockups.pdf, architecture-diagram.png
   ```

2. **Jira**: Create epic and stories
   ```
   Use: jira_create_issue
   Type: Epic
   Summary: "Dark Mode Support"
   Description: |
     Implement dark mode across application
     Design doc: [Confluence link]
   
   Use: jira_create_issue (for each story)
   Type: Story
   Parent: [Epic ID]
   Summary: "Implement dark mode toggle"
   Points: 5
   ```

**Phase 2: Implementation**

3. **GitHub**: Create feature branch and implement
   ```bash
   git checkout -b feature/dark-mode
   # Implement feature
   git commit -m "Add dark mode toggle (ENG-123)"
   git push origin feature/dark-mode
   ```

4. **GitHub**: Create pull request
   ```markdown
   # Add Dark Mode Toggle (ENG-123)
   
   Implements dark mode toggle in user preferences.
   
   **Jira**: ENG-123
   **Design**: [Confluence link]
   
   ## Changes
   - Dark mode CSS variables
   - Toggle component
   - Persistence logic
   ```

5. **Jira**: Update progress
   ```
   Use: jira_transition_issue
   Issue: ENG-123
   Status: "In Progress"
   
   Use: jira_add_comment
   Comment: "PR created: https://github.com/org/repo/pull/456"
   ```

**Phase 3: Review & Testing**

6. **GitHub**: Code review
   - Team reviews PR
   - Comments addressed
   - Approved

7. **Jira**: Move to testing
   ```
   Use: jira_transition_issue
   Issue: ENG-123
   Status: "Testing"
   Comment: "Deployed to staging for UAT"
   ```

**Phase 4: Release & Documentation**

8. **GitHub**: Merge and release
   ```bash
   git merge feature/dark-mode
   git tag v2.1.0
   git push --tags
   ```

9. **Confluence**: Update user documentation
   ```
   Use: confluence_update_page
   Page: "User Guide"
   Content: Add section on dark mode feature
   ```

10. **Jira**: Close ticket
    ```
    Use: jira_transition_issue
    Issue: ENG-123
    Status: "Done"
    Resolution: "Fixed"
    
    Use: jira_add_comment
    Comment: |
      Released in v2.1.0
      Documentation: [Confluence link]
    ```

---

## Integration Patterns

### Confluence ↔ Jira

**Link Jira issues in Confluence**:
```markdown
Implementation tracked in [ENG-123|https://jira.example.com/browse/ENG-123]

Status: @@ENG-123@@  # Shows live status
```

**Link Confluence pages in Jira**:
```
Description:
Design document: https://confluence.example.com/pages/123456

Use: jira_add_comment
Comment: "Design doc updated: [Confluence link]"
```

### Jira ↔ GitHub

**GitHub commits → Jira**:
```bash
git commit -m "Fix timeout issue

Increased timeout from 30s to 120s.
ENG-123 #comment Fixed timeout issue"
```

**Jira issues → GitHub**:
```markdown
# Pull Request description
Fixes ENG-123: API timeout on large uploads

**Jira**: https://jira.example.com/browse/ENG-123
```

### ADO ↔ GitHub

**ADO work items → GitHub**:
```markdown
# Pull Request
Fixes AB#123

## Azure DevOps
- Work Item: AB#123
- Sprint: Sprint 45
```

---

## Best Practices Summary

### Documentation (Confluence)

✅ **Write early**: Document design before implementation  
✅ **Version control**: Track major updates  
✅ **Rich media**: Use diagrams, screenshots, attachments  
✅ **Ownership**: Assign owners to pages  
✅ **Review cycle**: Quarterly review and update  

### Tracking (Jira/ADO/GitHub)

✅ **Clear titles**: Descriptive, searchable  
✅ **Acceptance criteria**: Unambiguous "done" conditions  
✅ **Regular updates**: Comment on progress  
✅ **Link everything**: Connect issues, docs, code  
✅ **Close the loop**: Update status through workflow  

### Cross-Platform

✅ **Single source of truth**: One canonical location per artifact  
✅ **Link, don't duplicate**: Reference, don't copy  
✅ **Consistent naming**: Use same IDs/titles across platforms  
✅ **Automate links**: Use commit conventions, integrations  
✅ **Keep in sync**: Update all platforms when status changes  

---

## Quick Reference

### MCP Atlassian Tools

**Confluence**:
```
confluence_create_page, confluence_update_page
confluence_get_page, confluence_search
confluence_upload_attachment, confluence_list_attachments
```

**Jira**:
```
jira_create_issue, jira_update_issue
jira_get_issue, jira_search
jira_add_comment, jira_transition_issue
jira_add_worklog
```

### Common Workflows

**New feature**:
1. Create Confluence design doc
2. Create Jira epic + stories
3. Implement in GitHub branch
4. Link PR to Jira issue
5. Update Confluence after release

**Bug fix**:
1. Create Jira bug ticket
2. Investigate and comment
3. Fix in GitHub PR
4. Link PR to Jira
5. Close Jira when merged

**Documentation update**:
1. Update Confluence page
2. Add comment to related Jira issue
3. Link from GitHub PR (if code-related)

---

## Key Takeaways

**Remember**:
- 📚 **Confluence for deep docs** (design, architecture, runbooks)
- 📋 **Jira/ADO for tracking** (issues, sprints, workflows)
- 💻 **GitHub for code** (PRs, code reviews, releases)
- 🔗 **Link everything** (maintain traceability)
- ✅ **Close the loop** (update all platforms)

**Philosophy**:
> "Document early, track everything, link across platforms. Every feature has a design doc, every issue has a ticket, every commit has a reference."

**Culture**:
> "Good documentation and tracking aren't overhead—they're how teams scale. Invest time upfront, save time later."

---

**Related**:
- [Development Workflow](development-workflow.md) - Where docs/tracking fit in workflow
- [Celebrate Early Discovery](../philosophy/celebrate-early-discovery.md) - Document findings
- [Testing Requirements](../standards/testing-requirements.md) - Link tests to tickets
- [Confluence Attachments Success Story](../examples/confluence-attachments-success-story.md) - Real usage
