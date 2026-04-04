---
name: attackbot-context
description: "Current project context for AttackBot M4 - Loaded at session start"
---

# AttackBot Context

> **Auto-loaded. Read first every session.**
> **Check .claude/MEMORY.md for detailed state.**

---

## 🔥 Immediate Context

**Current:** M4 - Read the Room (Reporter Service)
**Status:** Chunks 0-6 ✅, Chunks 7-9 🔲
**Next Priority:** Chunk 7 (PDF/DOCX rendering)

**Critical Finding:**
Evidence in `E2E_Runs/E2E_SYSTEM_FINDINGS#10.md` shows:
```
reporter-worker: "report_generation_not_yet_implemented"
```

**Reality:** Reporter receives messages but rendering is stubbed.

---

## 📋 Session Patterns

### Starting Work
```
You: "Load context" or "What's the state?"
Me:  Read MEMORY.md → Check TaskList → Summarize
     "M4: 60% complete. Chunk 7 (PDF/DOCX) needed. Evidence shows
      reporter worker stubbed. Tasks: #1 (Chunk 7), #2 (Chunk 8),
      #3 (Chunk 9, blocked). What should we work on?"
```

### Working Pattern
```
You: "Start Chunk 7"
Me:  TaskUpdate #1 status="in_progress"
     Analyze current reporter/renderers/ state
     Implement per M4_implementation.md
     Update MEMORY.md as work progresses
```

### Session End
```
You: "Save state"
Me:  Update MEMORY.md Session History
     TaskUpdate with progress
     State what remains for next time
     git add .claude/ (if committing)
```

---

## 🛡️ Safety Rules (Never Break)

| Rule | Action | Why |
|------|--------|-----|
| gitnexus_impact | Run before ANY edit | Know blast radius |
| d=1 callers | Update all | Prevent breakage |
| gitnexus_detect_changes | Check before commit | Verify scope |
|migration freeze| Never edit 001-004| Additive only |
|Docker rebuild| Use `--no-cache`| Cached images have stale code |

### Verification Steps

**Before editing:**
```
1. gitnexus_impact(target="symbol_name", direction="upstream")
2. Check risk_level - HIGH/CRITICAL = warn user
3. Only proceed if acceptable
```

**After editing:**
```
1. gitnexus_detect_changes(scope="staged")
2. Verify expected files changed
3. Check d=1 dependents updated
```

---

## 🔍 Understanding State

### Evidence Quality Hierarchy

| Level | Example |
|-------|---------|
| ✅ Best | "Log shows PDF generated: b'%PDF-1.4...'" |
| ✅ Good | "pytest tests/e2e/test_report_download_flow.py passes" |
| ⚠️ Weak | "reporter service healthy" (just means it starts) |
| ❌ Bad | "plan exists in M4_implementation.md" |
| ❌ Worse | "commit message says done" |

### Critical Keywords to Search

```powershell
# Find stubs in codebase
findstr /r /s "pass.*# TODO" backend\services\reporter\*.py
findstr /r /s "NotImplementedError" backend\services\reporter\*.py
findstr /r /s "def.*stub" backend\services\reporter\*.py

# Check E2E logs for "not_yet_implemented"
findstr /r "not_yet_implemented" E2E_Runs\*.md
```

---

## 🎯 M4 Chunk 7 Specifics

**From docs/Milestone.md Step 4.5-4.7:**

**PDF Generation:**
- Tool: `reportlab` or `weasyprint`
- Output: `reports/{report_id}/report.pdf` in MinIO
- Sections: Executive Summary → Scope → Findings Table → Detail → Reproduction
- Zero-finding guard: Must produce "No Findings" not crash

**DOCX Generation:**
- Tool: `python-docx`
- Same structure as PDF
- Pre-signed URL for download

**Critical Guard:**
```python
# ParsedScan.__post_init__ in reporter/parsing.py
self.has_findings = len(self.findings) > 0
```

**Evidence of Chunk 7 Done:**
- [ ] E2E log shows PDF/DOCX files uploaded to MinIO
- [ ] `%PDF` header validated in download test
- [ ] ZIP format validated for DOCX
- [ ] Zero-finding path produces valid (empty) report
- [ ] `pytest tests/integrations/test_reporter_pipeline.py` passes

---

## 🧰 Common Commands

```powershell
# Smoke check
docker compose -f infra/docker-compose.yml ps
curl http://localhost:8003/api/v1/health  # reporter

# View reporter logs
docker compose -f infra/docker-compose.yml logs reporter-worker --tail 50

# Rebuild after changes
docker compose -f infra/docker-compose.yml build --no-cache reporter-worker

# Test quickly
pytest tests/unit -q --tb=short
pytest tests/unit/test_reporter_*.py -v

# Full test
pytest tests/e2e/test_report_download_flow.py -v

# Check migration state
docker compose -f infra/docker-compose.yml run --rm migrate alembic -c /app/backend/migrations/alembic.ini current
```

---

## 📚 Reference Priority

**Trust Level (Highest First):**

1. ✅ **Execution logs** (E2E_Runs/*.md, docker logs)
2. ✅ **Code behavior** (actual function output)
3. ✅ **Test results** (pytest output)
4. ⚠️ **Milestone.md** (specification, may not match code)
5. ⚠️ **M4_implementation.md** (plan, NOT evidence)
6. ❌ **Git commits** (signal, not proof)

**Before claiming done:**
- Evidence from #1 or #2
- Not #5 or #6 alone

---

## 🚧 Current Blockers

| Blocker | Evidence | Unblocks |
|---------|----------|----------|
| Reporter worker stubbed | `"report_generation_not_yet_implemented"` in logs | Chunk 7 implementation |

---

## 🔄 Quick Context Reload

If session interrupted, reload:

1. **State:** Read `.claude/MEMORY.md`
2. **Work:** Check `TaskList`
3. **Evidence:** Search E2E logs for "not_yet_implemented"
4. **Next:** Ask user "Continue Chunk 7?"

**Session Continuity:**
- MEMORY.md = high-level state
- Task system = work tracking
- Both persist in git
- `CONTEXT` skill surfaces current situation