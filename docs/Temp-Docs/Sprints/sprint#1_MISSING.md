# Sprint #1: Missing Implementation - Gap Analysis

> **Document Type:** Implementation Gap Report  
> **Sprint:** #1 - P0 Data Integrity  
> **Date:** 2026-03-29  
> **Source:** Test verification from `tests/verification/sprint_1/`  
> **Status:** INCOMPLETE - Critical gaps identified  

---

## Executive Summary

**Sprint #1 is NOT properly implemented.** Test verification reveals critical gaps in all 3 issues. Only 6/22 tests pass (27% pass rate).

| Issue | Expected | Actual | Gap |
|-------|----------|--------|-----|
| #1 Watchdog | Full recovery + observability | Partial - missing repository methods | Implementation incomplete |
| #2 DLQ Monitor | Full visibility + recovery | Untestable - RabbitMQ dependency | Infrastructure needed |
| #3 Idempotency | Duplicate prevention | Partial - integrity & validation errors | Implementation incomplete |

---

## Issue-by-Issue Gap Analysis

---

## Issue #1: Watchdog Scan Recovery Mechanism Failure

**Objective:** Ensure watchdog reliably marks stuck scans as `failed_internal` and provides full observability.

### ✅ What EXISTS

| Requirement (from sprint#1.md) | File | Status |
|--------------------------------|------|--------|
| Prometheus metrics (`watchdog_executions_total`, `watchdog_scans_recovered_total`, `watchdog_errors_total`, `stuck_scans_current`) | `backend/services/core_engine/watchdog.py` | ✅ Implemented |
| Comprehensive logging (start/end/in-progress) | `backend/services/core_engine/watchdog.py` | ✅ Implemented |
| Exception re-raising after logging | `backend/services/core_engine/watchdog.py` | ✅ Implemented |
| Timezone-aware timestamp handling | `backend/services/core_engine/watchdog.py` | ✅ Partially implemented |
| Scheduler job registration | `backend/services/core_engine/main.py` | ✅ Implemented via `start_watchdog()` |
| Startup verification of watchdog job | `backend/services/core_engine/main.py` | ✅ Implemented |

### ❌ What's MISSING

#### Missing #1: ScanRepository.create_scan() Method

**Evidence:** 3 watchdog tests fail with:
```
AttributeError: 'ScanRepository' object has no attribute 'create_scan'
```

**Files Tested:**
- `test_stuck_scan_recovery`
- `test_watchdog_timezone_handling` 
- `test_watchdog_logging`

**Sprint Requirement:**
```python
# From sprint#1.md, Issue #1 Implementation Plan
# Day 1-2: Watchdog enhancements
# Files: watchdog.py, main.py
```

**Actual State:**
The tests assume `ScanRepository` has a `create_scan()` method, but this method doesn't exist in the actual implementation. The tests need this to create test scans that can be recovered by the watchdog.

**Fix Required:**
- **Add `create_scan()` method to `backend/services/core_engine/repository.py`**
- Method should accept: scan_id, program_id, config, status
- Method should set: created_at, started_at with timezone awareness

#### Missing #2: Timezone Migrations Not Applied

**Sprint Requirement:**
```python
# From sprint#1.md, Issue #1
# Day 2: Add timezone-aware timestamp validation
# Files: watchdog.py, alembic/versions/005_...py
```

**Evidence:** 
- Migration `005_ensure_timezone_aware_timestamps.py` referenced in sprint doc
- Tests expect timezone-aware timestamps to work correctly
- Actual test: `test_watchdog_timezone_handling` fails

**Actual State:**
The migration file exists but may not have been applied, or the tests create scans without proper timezone handling. The watchdog's timezone logic needs verification.

**Check Required:**
```bash
# Verify migration applied
alembic current
# Should show: 005 or higher
```

#### Missing #3: Stuck Scan Recovery Logic Incomplete

**Sprint Requirement:**
- Scans stuck >2h should be auto-recovered
- Error detail should contain "Watchdog recovery"
- completed_at should be set

**Evidence:**
The watchdog code exists and metrics work, but the actual recovery logic may not be processing scans correctly because test setup fails before reaching recovery logic.

**Root Cause:**
Tests can't even set up the test condition (create stuck scan) because `create_scan` is missing.

---

## Issue #2: Dead Letter Queue Blind Spot

**Objective:** Full visibility into DLQ state with automatic monitoring and recovery.

### ✅ What EXISTS

| Requirement (from sprint#1.md) | File | Status |
|--------------------------------|------|--------|
| DLQMonitor service class | `backend/shared/dlq_monitor.py` | ✅ Exists |
| Prometheus metrics (`rabbitmq_dlq_depth`, `dlq_messages_replayed_total`, `dlq_messages_archived_total`) | `backend/shared/dlq_monitor.py` | ✅ Implemented |
| Message inspection and classification | `backend/shared/dlq_monitor.py` | ✅ Implemented |
| Message replay mechanism | `backend/shared/dlq_monitor.py` | ✅ Implemented |
| Message archive mechanism | `backend/shared/dlq_monitor.py` | ✅ Implemented |
| Auto-recovery based on classification | `backend/shared/dlq_monitor.py` | ✅ Implemented |
| Scheduled monitoring job | `backend/services/core_engine/main.py` | ✅ Configured (60s interval) |
| API endpoints (`/api/v1/queue/dlq/monitor`, `/api/v1/queue/dlq/{dlq_name}/inspect`, `/api/v1/queue/dlq/{dlq_name}/replay`) | `backend/services/core_engine/main.py` | ✅ Exists in code |
| Grafana alert configuration | `grafana/alerts/dlq_alerts.yml` | ✅ Exists |

### ❌ What's MISSING

#### Missing #1: cannot verify without RabbitMQ

**Evidence:** All 10 DLQ tests fail with:
```
ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
aiormq.exceptions.AMQPConnectionError: [WinError 1225]
```

**Test Files Affected:**
- `test_dlq_depth_metrics`
- `test_dlq_inspection`
- `test_dlq_message_classification`
- `test_dlq_auto_recovery`
- `test_dlq_scheduled_monitoring`
- `test_dlq_monitor_endpoint`
- `test_dlq_inspect_endpoint`
- `test_dlq_replay_endpoint`

**Issue:**
The tests require a running RabbitMQ instance to verify DLQ monitoring. This is an **infrastructure dependency issue**, not necessarily a code implementation issue.

**Status:** ⚠️ **UNVERIFIABLE** (code may be correct but can't be tested)

#### Missing #2: Queue declaration for report.jobs.dlq

**Sprint Requirement:**
- `reports.completed` queue must be actively declared
- All queues with DLQ suffix should be monitored

**From sprint#1.md Issue #2:**
```python
# Required: ensure_queue() for reports.completed
# Pattern: Queues.all_with_dlqs() should return all queues that have DLQs
```

**Check Required:**
Verify `backend/shared/queue.py` has `all_with_dlqs()` method that includes all queues from Issue #2 Implementation Plan.

---

## Issue #3: Idempotency Guarantee Gaps

**Objective:** Prevent duplicate processing of redelivered messages.

### ✅ What EXISTS

| Requirement (from sprint#1.md) | File | Status |
|--------------------------------|------|--------|
| `idempotency_keys` table migration | `alembic/versions/006_add_idempotency_keys.py` | ✅ Exists |
| IdempotencyKey SQLAlchemy model | `backend/shared/models/idempotency.py` | ✅ Implemented |
| IdempotencyService class | `backend/shared/idempotency.py` | ✅ Exists |
| `check_and_record()` method | `backend/shared/idempotency.py` | ✅ Implemented |
| `store_response()` method | `backend/shared/idempotency.py` | ✅ Implemented |
| `with_idempotency()` decorator | `backend/shared/idempotency.py` | ✅ Implemented |
| Cleanup job for expired keys | `backend/shared/jobs/idempotency_cleanup.py` | ✅ Exists |
| Scheduler integration for cleanup | Referenced in sprint doc | ✅ Configured |

### ❌ What's MISSING

#### Missing #1: IdempotencyKey Model Field Mismatch

**Evidence:** 
```
sqlalchemy.exc.IntegrityError: duplicate key violates unique constraint "idempotency_keys_pkey"
```

**Test:** `test_idempotency_different_services`

**Sprint Requirement:**
```python
# From sprint#1.md Issue #3, Solution Code #1
class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key = Column(String(36), primary_key=True)  # event_id from MessageEnvelope
    service = Column(String(50), nullable=False)
    operation = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    response = Column(JSONB, nullable=True)
    entity_id = Column(PGUUID(as_uuid=True), nullable=True)
```

**Issue:**
Tests are trying to insert duplicate keys, suggesting either:
1. The `key` field is not actually the primary key as defined
2. Tests are not properly cleaning up between runs
3. The key generation logic has issues

**Fix Required:**
- Verify `idempotency_keys` table schema matches model
- Ensure tests use unique event_ids
- Add test cleanup between test runs

#### Missing #2: Cleanup Job Not Working

**Evidence:**
```
AssertionError: assert 19 == 0
```

**Test:** `test_idempotency_cleanup`

**Sprint Requirement:**
```python
# From sprint#1.md Issue #3, Solution Code #6
async def cleanup_expired_idempotency_keys_job():
    """Scheduled job to remove expired idempotency keys. Runs daily."""
    # Should remove keys older than 7 days
```

**Issue:**
The cleanup job runs but doesn't remove expired keys (19 remain when 0 expected).

**Fix Required:**
- Verify cleanup logic in `IdempotencyService.cleanup_expired()`
- Check that TTL is correctly set to 7 days
- Ensure `expires_at` field is indexed for efficient cleanup

#### Missing #3: Table Indexes Not Created

**Evidence:**
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; 
can't call await_only() here
```

**Test:** `test_idempotency_table_indexes`

**Sprint Requirement:**
```python
# From sprint#1.md Issue #3, Solution Code #2
__table_args__ = (
    Index('idx_idempotency_created_at', 'created_at'),
    Index('idx_idempotency_expires_at', 'expires_at'),
    Index('idx_idempotency_service_operation', 'service', 'operation'),
)
```

**Issue:**
Test tries to query indexes asynchronously without proper context.

**Fix Required:**
- Fix test to use proper async context
- OR verify indexes exist via different method

#### Missing #4: Worker Integration Not Complete

**Evidence:**
```
pydantic_core._pydantic_core.ValidationError: 3 validation errors for ScanJobsPayload
pydantic_core._pydantic_core.ValidationError: 5 validation errors for ReportJobsPayload
```

**Tests:**
- `test_worker_rejects_duplicate_scan`
- `test_reporter_rejects_duplicate_report`

**Sprint Requirement:**
```python
# From sprint#1.md Issue #3, Solution Code #4 & #5
# Core Worker should use with_idempotency wrapper
# Reporter Worker should use with_idempotency wrapper
```

**Issue:**
The worker integration exists, but the test payloads don't match the expected schema for `ScanJobsPayload` and `ReportJobsPayload`.

**Root Causes:**
1. Test uses wrong payload format
2. Payload schemas changed but tests not updated
3. Missing required fields in test data

**Fix Required:**
- Update test payloads to match current schemas
- OR update schemas to match test expectations
- Verify worker code actually uses idempotency wrapper

---

## Critical Missing Repository Methods

From test failures, the following methods are expected but MISSING:

### backend/services/core_engine/repository.py

```python
# MISSING METHOD - Required by watchdog tests
async def create_scan(
    self,
    scan_id: UUID,
    program_id: UUID,
    config: dict,
    status: str = "running"
) -> Scan:
    """Create a new scan with initial state."""
    scan = Scan(
        scan_id=scan_id,
        program_id=program_id,
        config=config,
        status=status,
        created_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc)
    )
    self.session.add(scan)
    await self.session.commit()
    await self.session.refresh(scan)
    return scan
```

---

## Sprint #1 Implementation Scorecard

| Requirement | Status | Tests | Evidence |
|-------------|--------|-------|----------|
| Watchdog Prometheus metrics | ✅ | 2/2 pass | `watchdog_executions_total`, `watchdog_scans_recovered_total` |
| Watchdog logging | ✅ | 0/1 pass | Logging code exists, test fails on setup |
| Watchdog exception handling | ✅ | 0/1 pass | Re-raise exists, test fails on setup |
| Watchdog timezone handling | ⚠️ | 0/1 pass | Migration exists, test fails on setup |
| Watchdog startup verification | ✅ | 1/1 pass | Job registration verified |
| Watchdog stuck scan recovery | ❌ | 0/1 pass | Cannot test without `create_scan` |
| **Issue #1 Total** | **⚠️ PARTIAL** | **2/5 pass** | |
| DLQ monitoring metrics | ⚠️ | 0/5 pass | Code exists, RabbitMQ needed |
| DLQ message inspection | ⚠️ | 0/1 pass | Code exists, RabbitMQ needed |
| DLQ message classification | ⚠️ | 0/1 pass | Code exists, RabbitMQ needed |
| DLQ auto-recovery | ⚠️ | 0/1 pass | Code exists, RabbitMQ needed |
| DLQ scheduled monitoring | ⚠️ | 0/1 pass | Code exists, RabbitMQ needed |
| DLQ API endpoints | ⚠️ | 0/2 pass | Code exists, RabbitMQ needed |
| **Issue #2 Total** | **⚠️ UNVERIFIABLE** | **0/10 pass** | |
| Idempotency table migration | ✅ | N/A | Migration file exists |
| IdempotencyKey model | ✅ | N/A | Model file exists |
| IdempotencyService | ✅ | 3/4 pass | Core methods work |
| with_idempotency decorator | ✅ | 1/1 pass | Decorator works |
| Idempotency cleanup job | ❌ | 0/1 pass | Cleanup not removing keys |
| Idempotency table indexes | ❌ | 0/1 pass | Async context error |
| Worker idempotency integration | ❌ | 0/2 pass | Validation errors |
| **Issue #3 Total** | **⚠️ PARTIAL** | **4/7 pass** | |
| **SPINT #1 TOTAL** | **❌ INCOMPLETE** | **6/22 pass (27%)** | |

---

## Priority Fix List

### 🔴 **BLOCKING (Prevents any Issue #1 testing)**

1. **Add `create_scan()` method to `ScanRepository`**
   - File: `backend/services/core_engine/repository.py`
   - Impact: Unblocks 3 watchdog tests

### 🟡 **HIGH (Prevents Issue #3 validation)**

2. **Fix idempotency cleanup job**
   - File: `backend/shared/idempotency.py`
   - Issue: Keys not being deleted (19 remain when 0 expected)
   - Check: TTL logic, query filter, async context

3. **Fix idempotency table indexes test**
   - File: `tests/verification/sprint_1/test_idempotency.py`
   - Issue: MissingGreenlet error - test needs async context fix

4. **Fix worker idempotency integration**
   - Files: `tests/verification/sprint_1/test_idempotency.py`
   - Issue: Test payloads don't match current schemas
   - Fix: Update test data OR update schemas

5. **Fix duplicate key constraint issue**
   - File: `tests/verification/sprint_1/test_idempotency.py`
   - Issue: Tests trying to insert duplicate primary keys
   - Fix: Ensure unique event_ids in tests

### 🟢 **MEDIUM (Prevents Issue #2 validation)**

6. **Set up RabbitMQ for testing**
   - Run: `docker-compose -f infra/docker-compose.yml up -d rabbitmq`
   - Impact: Unblocks all 10 DLQ tests

### 🔵 **LOW (Documentation/Cleanup)**

7. **Verify timezone migration applied**
   - Run: `alembic current`
   - Expected: 005 or higher

8. **Verify migration 006 applied**
   - Check: `idempotency_keys` table exists in database

---

## Files That Need Attention

| File | Issue | Fix Type | Priority |
|------|-------|----------|----------|
| `backend/services/core_engine/repository.py` | Missing `create_scan()` | Add method | 🔴 BLOCKING |
| `backend/shared/idempotency.py` | Cleanup not working | Fix logic | 🟡 HIGH |
| `tests/verification/sprint_1/test_idempotency.py` | Duplicate keys, async errors | Fix tests | 🟡 HIGH |
| `backend/services/core_engine/worker.py` | Validation errors | Check schemas | 🟡 HIGH |
| `backend/services/reporter/worker.py` | Validation errors | Check schemas | 🟡 HIGH |
| `infra/docker-compose.yml` | RabbitMQ not running | Start service | 🟢 MEDIUM |

---

## Conclusion

**Sprint #1 is NOT properly implemented for production.**

While much of the code exists (watchdog.py, dlq_monitor.py, idempotency.py), critical gaps prevent the sprint from passing verification:

1. **Repository interface incomplete** - Missing methods required by tests
2. **Idempotency has bugs** - Cleanup not working, validation errors
3. **DLQ unverifiable** - Cannot test without RabbitMQ infrastructure
4. **Only 27% of tests pass** - Well below acceptable threshold

**Recommendation:** Do NOT deploy Sprint #1 to production until all BLOCKING and HIGH priority items are resolved and test pass rate exceeds 90%.</p>

---

**Generated:** 2026-03-29  
**Test Run:** `pytest tests/verification/sprint_1/ -v`  
**Pass Rate:** 6/22 (27%)  
