# Proper Discovery Before Implementation

> **Core Principle #3**: Take time to understand before coding. Rushing creates technical debt.

---

## The Problem: The Rush to Code

**The Temptation**:
```
❌ "I'll figure out the API as I code"
❌ "Let's skip research and just start"
❌ "We can refactor later"
```

**The Reality**:
- Gaps in understanding lead to incorrect implementations
- Assumptions made without research become bugs
- "Temporary" shortcuts become permanent technical debt
- Refactoring costs 10x more than doing it right initially

---

## When to Invest Discovery Time

**Invest time researching when**:
- ✅ New API or framework you're integrating
- ✅ Complex patterns or architectural decisions
- ✅ Third-party library behavior and quirks
- ✅ Authentication/security mechanisms
- ✅ Cross-platform considerations
- ✅ Performance or scaling implications

**For high-risk or complex discovery**, use a **formal spike** (see [Spike Template](../processes/spike-template.md)).

---

## Discovery Activities

### Before Implementation Checklist

```
Before Implementation:
├─ Read official documentation thoroughly
├─ Review API reference and examples
├─ Test API endpoints in isolation
├─ Understand error handling patterns
├─ Identify edge cases and limitations
├─ Check for known issues or workarounds
└─ Document findings before coding
```

### What to Research

**API/Framework**:
- Endpoints and methods available
- Request/response formats
- Authentication and authorization
- Rate limits and quotas
- Error codes and handling
- Pagination patterns
- Known bugs or limitations

**Architecture/Patterns**:
- Design trade-offs (approach A vs B)
- Scalability characteristics
- Performance implications
- Maintenance complexity
- Integration points

**Security**:
- Authentication mechanisms
- Authorization models
- Data encryption requirements
- Security best practices
- Known vulnerabilities

**Cross-Platform**:
- OS-specific behavior
- Platform availability
- Compatibility matrix
- Known platform issues

---

## Time Investment vs. Risk

| Scenario | Rush (Skip Discovery) | Proper Discovery |
|----------|----------------------|------------------|
| **Time to Code** | 2 hours | 4 hours (2h research + 2h code) |
| **Bugs Found** | 5-10 issues | 1-2 issues |
| **Refactor Time** | 8+ hours | 1 hour |
| **Technical Debt** | High | Low |
| **Total Time** | 10-18 hours | 5-7 hours |

**Insight**: Discovery takes 2x upfront but saves 3x total time.

---

## Real Example: Confluence Attachments

### Discovery Phase Findings

**Time invested**: 4 hours of API exploration

**Findings** (saved hours of rework):

1. **V2 API supports OAuth, V1 supports tokens**
   - Decision: Use adapter pattern
   - Saved: Would have had to refactor entire implementation

2. **PUT creates versions, POST creates duplicates**
   - Decision: Use PUT for existing attachments
   - Saved: Would have created duplicate attachments in UAT

3. **Comments need explicit charset in multipart form**
   - Decision: Add `content-type: text/plain; charset=utf-8`
   - Saved: Comments wouldn't have appeared in Confluence UI

4. **Media type filtering broken in API**
   - Decision: Document workaround (filter by filename instead)
   - Saved: Users wouldn't have discovered until production

5. **Download URLs are relative**
   - Decision: Must prepend base URL
   - Saved: Download links would have been broken

6. **SIGPIPE not available on Windows**
   - Decision: Add platform check (`hasattr(signal, 'SIGPIPE')`)
   - Saved: Server would crash on Windows

### Without Discovery

**Scenario**: Code first, discover later

```
Day 1: Implement attachment upload (POST method)
Day 2: UAT finds duplicate attachments
Day 3: Debug and discover PUT is correct method
Day 4: Refactor to use PUT
Day 5: UAT finds comments not visible
Day 6: Debug and discover charset issue
Day 7: Fix charset
Day 8: UAT finds download URLs broken
... pattern continues
```

**Total time**: 2-3 weeks, multiple UAT cycles, frustrated team

### With Discovery

**Scenario**: Research first, implement correctly

```
Day 1: API research and documentation (4 hours)
Day 2-3: Implement with correct approach (8 hours)
Day 4: UAT finds zero API-related issues
Day 5: Production ready
```

**Total time**: 5 days, single UAT cycle, confident team

**Result**: Discovery investment paid 3x return

---

## The Cost of Rushing

### Short-Term Gain

- ✅ Faster initial coding
- ✅ Feels like progress
- ✅ Looks productive in standup

### Long-Term Pain

- ❌ Incorrect assumptions become bugs
- ❌ Architectural mistakes are expensive to fix
- ❌ Technical debt accumulates
- ❌ Team loses confidence in code quality
- ❌ Users encounter preventable issues
- ❌ Total time increases 2-3x

---

## Discovery Best Practices

### Documentation Reading

**Don't just skim**:
- Read "Getting Started" completely
- Review all API methods, not just first one
- Check "Common Pitfalls" or "Known Issues" sections
- Read release notes for version you're using
- Look for "Best Practices" guidance

**Take notes**:
```markdown
## Confluence Attachments API Discovery

### Key Findings:
- PUT for updates/versions, POST for new
- Comments: multipart form with charset
- Download URLs: relative (need base URL)
- Media type filter: broken (use filename)

### Questions to Resolve:
- [ ] Does V2 support token auth? (Answer: No)
- [ ] Rate limits? (Answer: 100 req/min)

### Gotchas:
- SIGPIPE on Unix only
- OAuth requires V2 adapter
```

### Hands-On Testing

**Write exploration scripts**:
```python
# explore_confluence_api.py (throwaway code)

# Test 1: POST vs PUT for existing file
result1 = api.post("/attachment", data)  # Creates duplicate
result2 = api.put("/attachment", data)   # Creates version ✅

# Test 2: Comment visibility
result3 = upload(comment="Test")  # Not visible
result4 = upload(comment="Test", content_type="text/plain; charset=utf-8")  # Visible ✅

# Test 3: Download URL format
result5 = api.get_attachment()
print(result5.download_url)  # "/download/..." (relative) ⚠️
```

**Keep exploration code separate**:
- Don't mix with production code
- Use `exploration/` or `research/` folder
- Throwaway scripts (not committed)
- Or use spike template for formal research

### Ask for Help

**When stuck**:
- Check Stack Overflow
- Search GitHub issues
- Ask in community forums
- Consult with team members who have experience

**Document answers** for team's future reference.

---

## When Discovery Becomes a Spike

**Normal discovery** → **Spike** when:
- Time needed exceeds 3-4 hours
- Need to build prototype to validate
- Multiple approaches to compare
- Performance or feasibility questions
- High risk or complexity

**Use spike template** for:
- Formal time-boxing
- Structured evidence gathering
- Decision documentation
- Follow-on work planning

See: [Spike Template](../processes/spike-template.md)

---

## Discovery Anti-Patterns

### Anti-Pattern 1: "I'll Figure It Out as I Go"

```
Code → Hit issue → Google → Try fix → Hit another issue → Repeat
→ Implementation is patchwork of quick fixes
→ Doesn't understand underlying patterns
→ Technical debt accumulates
```

**Fix**: Research patterns upfront, understand the "why" not just "how"

### Anti-Pattern 2: "Documentation is for Wimps"

```
Skip docs → Copy Stack Overflow code → Works initially → Breaks in edge cases
→ Don't understand why it breaks → More Stack Overflow copies → More breakage
```

**Fix**: Read official documentation, understand properly

### Anti-Pattern 3: "We'll Refactor Later"

```
Rush to code → Make assumptions → Assumptions wrong → Need refactor
→ "No time to refactor" → Ship with assumptions → Production issues
```

**Fix**: Do it right the first time, refactoring later rarely happens

### Anti-Pattern 4: Analysis Paralysis

```
Read all documentation → Read every blog post → Watch all videos
→ Still researching after 2 weeks → Never start coding
```

**Fix**: Time-box discovery (2-4 hours), use spike for extended research

---

## Quick Reference

### Discovery Checklist

**Before starting implementation**:
- [ ] Read official documentation for API/framework
- [ ] Review examples and tutorials
- [ ] Test key operations in isolation
- [ ] Understand error handling patterns
- [ ] Identify edge cases and limitations
- [ ] Check for known issues or bugs
- [ ] Document findings (notes, code comments)
- [ ] Decide: Need formal spike? (if high-risk)

**Time budget**:
- Simple API: 1-2 hours
- Complex API: 3-4 hours
- High-risk/complex: Run spike (4-16 hours)

---

## Key Takeaways

**Remember**:
- 🔍 **Research before rushing** (saves 3x time)
- 🔍 **Discovery is investment** (not wasted time)
- 🔍 **Document findings** (helps team and future you)
- 🔍 **Test assumptions** (don't guess, verify)
- 🔍 **Use spike for high-risk** (formal process)

**Best Practice**:
> "If examining an API, framework, or pattern will help your next phase stick to standards and prevent unintentional debt, **take the time to examine it properly**."

**Philosophy**:
> "Discovery time is not wasted—it's an investment in quality. Taking time to understand APIs, frameworks, and patterns before implementing prevents technical debt and saves time in the long run."

---

**Related**:
- [Spike Template](../processes/spike-template.md) - Formal discovery process
- [TDD Principles](tdd-principles.md) - Test-driven implementation
- [Development Workflow](../processes/development-workflow.md) - Discovery in workflow
- [Security & Vulnerability Management](security-vulnerability-management.md) - Security research
