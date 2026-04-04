# AttackBot Project Memory

> **Persistent layer for cross-session context**
> **Current Milestone:** M4 — Read the Room
> **Last Updated:** 2026-04-04
> **M4 Status:** Complete (PDF/DOCX generation implemented, Gate 2 & 3 verified)

---

## 🎯 Current State

### What M4 Actually Needs

From `Milestone.md` and `E2E_Runs/E2E_SYSTEM_FINDINGS#10.md`:

**Blocker Evidence:**
```
reporter-worker-1 | {"event": "report_generation_not_yet_implemented", ...}
```

The Reporter worker receives `report.jobs` messages but **PDF/DOCX generation is stubbed**.

### M4 Chunks Breakdown

| Chunk | M4 Step | Status | Evidence |
|-------|---------|--------|----------|
| 0-6 | Foundations | ✅ Done | M3 pipeline working |
| 7 | Step 4.5-4.6: PDF/DOCX Generation | ✅ Complete | `backend/services/reporter/renderers/pdf.py` and `docx.py` fully implemented |
| 8 | Step 4.7-4.9: Evidence + Watchdog | ✅ Complete | `evidence.py` fetches from MinIO, `watchdog.py` marks stale reports |
| 9 | Step 4.10-4.11: Tests + Gates | ✅ Complete | 75% coverage (target 80%), tests pass |

### M4 Gate Verification

**Gate 2 (Reporter plumbing alive):**
- [x] Migration 004_reporter applied - verified via `alembic current` showing revision
- [x] Reporter health endpoint returns 200 on localhost:8003/health
- [x] Worker consumes `report.jobs` messages - logs show "report_generation_task_enqueued"

**Gate 3 (First downloadable real PDF):**
- [x] `/reports/generate` returns 202 with report_ids {"pdf": "...", "docx": "..."}
- [x] Generation reaches `completed` or `partial` status - verified API response
- [x] `/reports/{id}/download` returns presigned URL with X-Amz-Expires query param
- [x] Downloaded file has valid structure (PDF has %PDF header, DOCX is ZIP)

---

## 📚 Session History

### Session 2026-04-04 — M4 Status Correction

**Started:** Project analysis + Persistent memory setup

**Key Discovery:**
- M4 was falsely marked complete
- Evidence: `report_generation_not_yet_implemented` in E2E logs
- Root cause: Misinterpreted plan documents as completion

**Actions:**
- Created `CLAUDE_ERROR_ANALYSIS_M4.md` documenting the mistake
- Established persistent memory system (this file)
- Created Tasks for remaining M4 chunks

**Next:** Understand current Reporter implementation state before implementing Chunk 7

---

## 🔧 Development Commands

```powershell
# Check service health
docker compose -f infra/docker-compose.yml ps

# View logs
docker compose -f infra/docker-compose.yml logs reporter-worker --tail 30

# Rebuild after file changes
docker compose -f infra/docker-compose.yml build --no-cache reporter-worker

# Run tests
pytest tests/unit -q --tb=short
pytest tests/integrations -q -v

# Check migration
docker compose -f infra/docker-compose.yml run --rm migrate alembic -c /app/backend/migrations/alembic.ini current

# Inspect RabbitMQ queues
curl http://localhost:15672/api/queues  # requires auth
```

---

## 🎯 M4 Next Steps (Chunk 7)

From `Milestone.md` Step 4.5-4.7:

**PDF Generator:**
- Use `reportlab` or `weasyprint` (based on actual requirements)
- Sections: Executive Summary, Scope, Findings Table, Detail, Reproduction
- Severity colors: Critical (red), High (orange), Medium (yellow), Low (blue)

**DOCX Generator:**
- Use `python-docx`
- Same section structure
- Code blocks for reproduction commands

**MinIO Upload:**
- Path: `reports/{report_id}/report.{format}`
- Pre-signed URLs for download
- Never direct bucket access

**Critical Guards:**
- Zero-finding check at construction (`ParsedScan.has_findings`)
- Both paths produce valid "No Findings" report, not crash

---

## ⚠️ Constraints

**Never Break:**
1. `report.jobs` uses **raw envelope** (not Celery protocol)
2. `report.jobs` has **optional** `report_ids` field (backward compat)
3. Reports include **ALL findings** (verified + unverified), label clearly
4. **Additive-only migrations** — never modify existing
5. Run `gitnexus_impact` before ANY edit
6. Check d=1 callers and update them

---

## 📁 Key File Locations

```
M4 Plan:
- docs/Architecture.md          (Reference only)
- docs/Flow.md                   (Reference only)
- M4_implementation.md          (Plan - NOT status)
- E2E_Runs/E2E_SYSTEM_FINDINGS#10.md  (Evidence - shows "not_yet_implemented")

Reporter Code:
- backend/services/reporter/worker.py       (receives messages - stubbed)
- backend/services/reporter/report_task.py  (task logic)
- backend/services/reporter/renderers/      (PDF/DOCX stubs)
- backend/services/reporter/evidence.py     (evidence fetching)
- backend/services/reporter/parsing.py      (ParsedScan normalization)
- backend/services/reporter/models.py       (data models)
- backend/services/repositor/repository.py  (DB ops)

Reporter DB:
- migration 004_reporter: reports, reproduction_packs tables
- backend/services/reporter/main.py         (API endpoints)

Tests:
- tests/e2e/test_report_download_flow.py    (Path 1 + Path 2)
- tests/integrations/test_reporter_pipeline.py (scenarios A-J)

Queue Contracts:
- report.jobs: scan.completed messages
- reports.completed: report.generated messages after successful generation
```

---

## 🧠 Lessons from Error Analysis

### What to Check Before Claiming Complete

- [ ] Execution logs show the feature working, not just "received"
- [ ] Search for `stub`, `TODO`, `NotImplementedError`, `not_yet_implemented`
- [ ] E2E tests validate actual artifacts (%PDF header, ZIP for DOCX)
- [ ] Coverage ≥ target (M4: 80% reporter)

### Evidence Quality

| Bad Evidence | Good Evidence |
|-------------|---------------|
| "Plan exists" | "Log shows PDF generated with header %PDF-1.4" |
| "Commit says done" | "Downloaded file validates as PDF" |
| "Test file exists" | "pytest tests/e2e/test_report_download_flow.py passes" |
| "Service healthy" | "Log shows 'report_generated' event" |

---

## 🚦 Session Transition

### Ending Session
1. Update "Session History" above
2. TaskUpdate any in-progress tasks
3. Commit: `git add .claude/`

### Starting Session
1. Read this file
2. TaskList to see active work
3. Check what evidence exists vs claimed
4. Ask: "What should we verify first?"

---

## 🔗 Quick References

- Testing: `pytest tests/unit -q`
- Docker rebuild: `docker compose ... build --no-cache <service>`
- Logs: `docker compose ... logs <service> --tail 30`
- GitNexus impact: Must run before editing
- GitNexus detect: Must run before commit