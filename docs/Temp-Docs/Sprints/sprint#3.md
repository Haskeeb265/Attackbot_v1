# Sprint #3: P1 - Architecture Modernization

> **Document Type:** Implementation Guide  
> **Target Audience:** Senior Engineers, Architects, QA Team  
> **Date:** 2026-04-22  
> **Branch:** M4_ReadTheRoom  
> **Duration:** Weeks 5-6  
> **Status:** Ready for Implementation  

---

## Sprint Overview

**Theme:** *Decouple services and enable event-driven architecture*  
**Business Impact:** **Medium** — Improves scalability and reduces tight coupling  
**Sprint Goal:** Reporter is self-contained, scan state changes are auditable

### Key Outcomes

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Reporter Core Engine calls | 300+/report | **0** | Code audit |
| Report generation time (100 findings) | 15-60s | **<500ms** | Prometheus: report_generation_duration |
| Audit trail | Limited | **Complete event history** | API: /scans/{id}/events |
| State reconstruction | Impossible | **Replay from events** | Test: rebuild scan state |

---

## Sprint Statistics

| Attribute | Value |
|-----------|-------|
| **Priority** | P1 (Medium) |
| **Effort** | 14-21 hours |
| **Issues** | 2 |
| **Team Weeks** | 2 weeks |
| **Assignees** | 2 Engineers |

---

## Issues Included

| # | Issue | Category | Severity | Effort | Assignee | Days |
|---|-------|----------|----------|--------|----------|-------|
| **6** | Synchronous Inter-Service Dependencies | Architectural | 🟡 | 4-6h | Engineer A | Day 1-3 |
| **7** | Absence of Event Sourcing | Strategic | 🟢 | 10-15h | Engineer B | Day 1-6 |

---

## Prerequisites

Before starting Sprint 3, ensure:
- [ ] Sprint 1: Issue #1 (Watchdog), Issue #3 (Idempotency) - **CRITICAL**
- [ ] Sprint 2: Issue #4 (Circuit Breaker), Issue #5 (Distributed Tracing) - **RECOMMENDED**
- [ ] Verified: No stuck scans in production
- [ ] Verified: Idempotency working for scan messages

---
---

## Issue #6: Synchronous Inter-Service Dependencies

### Objective
Eliminate Reporter's HTTP calls to Core Engine by embedding data in messages.

### Problem Statement
Reporter Worker makes 300+ synchronous HTTP calls to Core Engine per report (one per finding/evidence). This causes: high latency (15-60s), tight coupling, resource waste, and cascading failures.

**Evidence:** Report generation for 100 findings takes 45-60 seconds, 90% spent on HTTP.

### Root Causes
1. ReportJobsPayload only contains scan_id, not actual data
2. Reporter is passive consumer, not self-contained
3. Same data refetched via HTTP that was already available

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 1 | Extend ReportJobsPayload schema | `shared/schemas/report_jobs.py` | 4h | Engineer A |
| 2 | Update Aggregator (Stage 10) | `core_engine/pipeline/aggregator.py` | 3h | Engineer A |
| 3 | Remove HTTP calls from Reporter | `reporter/clients/core_engine.py` | 1h | Engineer A |
| 3 | Update Reporter Worker | `reporter/worker.py` | 2h | Engineer A |
| 3 | Performance testing | Benchmark scripts | 2h | Engineer A |

### Solution Code

#### 1. Enhanced Payload Schema

```python
# File: backend/shared/schemas/report_jobs.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class FindingData(BaseModel):
    finding_id: UUID
    title: str
    severity: str
    # ... other fields

class EvidenceData(BaseModel):
    evidence_id: UUID
    finding_id: UUID
    title: str
    severity: str
    # ... other fields

class ScanSummary(BaseModel):
    scan_id: UUID
    program_id: UUID
    started_at: datetime
    status: str
    total_findings: int
    severity_breakdown: Dict[str, int]

class ReportJobsPayload(BaseModel):
    scan_id: UUID
    program_id: UUID
    formats: List[str] = ["pdf"]
    
    # NEW in v2:
    payload_version: int = Field(default=2, ge=1)
    scan_summary: Optional[ScanSummary] = None
    findings: List[FindingData] = Field(default_factory=list)
    evidence: List[EvidenceData] = Field(default_factory=list)
    
    def is_legacy(self) -> bool:
        return self.payload_version < 2
    
    def has_embedded_data(self) -> bool:
        return self.payload_version >= 2 and len(self.findings) > 0
```

#### 2. Aggregator Updates

```python
# File: backend/services/core_engine/pipeline/aggregator.py
from backend.shared.schemas.report_jobs import (
    ReportJobsPayload, ScanSummary, FindingData, EvidenceData
)

class ReportAggregator:
    async def aggregate_and_publish(self, scan_id, program_id, formats):
        # Get scan data
        scan = await self.repo.get_scan(scan_id)
        
        # Build full payload with embedded data
        payload = ReportJobsPayload(
            scan_id=scan_id,
            program_id=program_id,
            formats=formats,
            payload_version=2,
            scan_summary=ScanSummary(
                scan_id=scan.scan_id,
                program_id=scan.program_id,
                started_at=scan.started_at,
                status=scan.status,
                total_findings=len(scan.findings),
                severity_breakdown=self._calc_breakdown(scan)
            ),
            findings=[self._to_finding_data(f) for f in scan.findings],
            evidence=[self._to_evidence_data(f, e) for f in scan.findings for e in f.evidence]
        )
        return payload
```

#### 3. Updated Reporter Worker

```python
# File: backend/services/reporter/worker.py
class ReportWorker:
    async def process_report_job(self, envelope, payload_dict):
        payload = ReportJobsPayload.model_validate(payload_dict)
        
        if payload.has_embedded_data():
            # Use embedded data - no HTTP calls
            result = await self._generate_report(payload)
        elif payload.is_legacy():
            # Fallback for backward compatibility
            await self._legacy_http_fetch(payload)
        
        return result
    
    async def _generate_report(self, payload):
        # Direct access to embedded data
        findings = payload.findings
        evidence = payload.evidence
        scan_summary = payload.scan_summary
        
        # Generate report without HTTP calls
        # ...
```

#### 4. Performance Test

```python
# File: tests/performance/test_reporter_performance.py
import asyncio
import time
from typing import List
from uuid import uuid4
import pytest

class TestReporterPerformance:
    async def test_embedded_data_performance(self):
        # Create test payload with 100 findings, 500 evidence
        payload = self._create_test_payload(100)
        
        worker = ReportWorker()
        start = time.time()
        await worker._generate_report(payload, "json")
        elapsed = time.time() - start
        
        print(f"Report generation: {elapsed:.2f}s")
        assert elapsed < 0.5, f"Too slow: {elapsed:.2f}s"
```

### Acceptance Criteria

- [ ] ReportJobsPayload includes: scan_summary, findings, evidence
- [ ] Core Engine populates embedded data in Stage 10
- [ ] Reporter Worker uses embedded data (no HTTP calls)
- [ ] Performance: 100 findings = <500ms (vs 15s with HTTP)
- [ ] Backward compatibility: Old messages still work
- [ ] Test: Generate report with embedded data, verify correctness

### Rollback Strategy

**Time:** <15 minutes

```bash
# Revert all changes
git checkout HEAD~1 -- backend/shared/schemas/report_jobs.py
git checkout HEAD~1 -- backend/services/core_engine/pipeline/aggregator.py
git checkout HEAD~1 -- backend/services/reporter/worker.py
git checkout HEAD~1 -- backend/services/reporter/clients/core_engine.py
```

### Testing Checklist

- [ ] Unit test: Payload schema validation
- [ ] Unit test: Aggregator data embedding
- [ ] Unit test: Reporter Worker embedded data usage
- [ ] Integration test: End-to-end report generation
- [ ] Performance test: 100 findings <500ms
- [ ] Manual test: Backward compatibility

---

## Issue #7: Absence of Event Sourcing

### Objective
Persist all domain events for audit trail and state reconstruction.

### Problem Statement
Without event sourcing: no audit trail, no state reconstruction, no temporal queries, no compliance support.

**Evidence:** Scan data corruption incident (2026-03-15) required 6 hours manual reconstruction.

### Root Causes
1. Current architecture stores state directly, not events
2. No Event Store mechanism
3. Repository doesn't record events with state changes

### Implementation Plan

| Day | Task | Files | Effort | Owner |
|-----|------|-------|--------|-------|
| 1 | Create domain_events table migration | `alembic/versions/007_...py` | 2h | Engineer B |
| 2 | Implement EventStore service | `shared/event_sourcing/event_store.py` | 3h | Engineer B |
| 3 | Add event recording to ScanRepository | `core_engine/repository.py` | 3h | Engineer B |
| 4 | Add audit endpoints | `core_engine/main.py` | 2h | Engineer B |
| 5 | Add temporal query support | `core_engine/main.py` | 2h | Engineer B |
| 6 | Test state reconstruction | Test scripts | 3h | Engineer B |

### Solution Code

#### 1. Event Model

```python
# File: backend/shared/models/event_store.py
from sqlalchemy import Column, String, DateTime, Index, JSONB, BigInteger
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from backend.shared.db import Base

class EventType(str):
    SCAN_CREATED = "scan.created"
    SCAN_STARTED = "scan.started"
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"
    STAGE_COMPLETED = "stage.completed"
    FINDING_CREATED = "finding.created"

class DomainEvent(Base):
    __tablename__ = "domain_events"
    __table_args__ = (
        Index('idx_domain_events_entity', 'entity_type', 'entity_id'),
        Index('idx_domain_events_aggregate', 'aggregate_type', 'aggregate_id'),
        Index('idx_domain_events_sequence', 'sequence'),
        Index('idx_domain_events_timestamp', 'timestamp'),
    )
    
    event_id = Column(PGUUID(as_uuid=True), primary_key=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(PGUUID(as_uuid=True), nullable=False)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    sequence = Column(BigInteger, nullable=False)
    data = Column(JSONB, nullable=False)
    metadata = Column(JSONB, nullable=True)
    triggered_by = Column(String(255), nullable=True)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(PGUUID(as_uuid=True), nullable=False)
```

#### 2. Database Migration

```python
# File: alembic/versions/007_add_domain_events.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('domain_events', ...)
    op.create_index('idx_domain_events_entity', ...)
    op.create_index('idx_domain_events_aggregate', ...)
    op.execute("CREATE SEQUENCE domain_event_sequence_seq INCREMENT BY 1")

def downgrade():
    op.drop_table('domain_events')
    op.execute("DROP SEQUENCE IF EXISTS domain_event_sequence_seq")
```

#### 3. EventStore Service

```python
# File: backend/shared/event_sourcing/event_store.py
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.shared.models.event_store import DomainEvent

class EventStore:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def append_event(self, entity_type, entity_id, event_type, data, 
                          metadata=None, triggered_by=None, 
                          aggregate_type=None, aggregate_id=None):
        result = await self.session.execute(
            text("SELECT nextval('domain_event_sequence_seq')")
        )
        sequence = result.scalar()
        
        event = DomainEvent(
            event_id=uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            sequence=sequence,
            data=data,
            metadata=metadata,
            triggered_by=triggered_by,
            aggregate_type=aggregate_type or entity_type,
            aggregate_id=aggregate_id or entity_id
        )
        self.session.add(event)
        return event
    
    async def get_events_for_aggregate(self, aggregate_type, aggregate_id, 
                                       since=None, until=None):
        query = select(DomainEvent).where(
            and_(DomainEvent.aggregate_type == aggregate_type,
                 DomainEvent.aggregate_id == aggregate_id)
        ).order_by(DomainEvent.sequence)
        return (await self.session.execute(query)).scalars().all()
```

#### 4. Enhanced ScanRepository

```python
# File: backend/services/core_engine/repository.py
from backend.shared.event_sourcing.event_store import EventStore
from backend.shared.models.event_store import EventType

class ScanRepository:
    def __init__(self, session):
        self.session = session
        self.events = EventStore(session)
    
    async def create_scan(self, program_id, config, triggered_by=None):
        # ... existing create logic ...
        
        # Record event
        await self.events.append_event(
            entity_type="scan",
            entity_id=scan.scan_id,
            event_type=EventType.SCAN_CREATED,
            data={"scan_id": str(scan.scan_id), "status": "pending"},
            triggered_by=triggered_by,
            aggregate_type="scan",
            aggregate_id=scan.scan_id
        )
        return scan
    
    async def start_scan(self, scan_id, triggered_by=None):
        # ... existing update logic ...
        await self.events.append_event(
            entity_type="scan",
            entity_id=scan_id,
            event_type=EventType.SCAN_STARTED,
            data={"previous": "pending", "new": "running"},
            triggered_by=triggered_by,
            aggregate_type="scan",
            aggregate_id=scan_id
        )
    
    async def mark_scan_complete(self, scan_id, status, finding_count, 
                                  severity_breakdown, error_detail=None, 
                                  triggered_by=None):
        # ... existing update logic ...
        event_type = EventType.SCAN_COMPLETED if status == "completed" else EventType.SCAN_FAILED
        await self.events.append_event(
            entity_type="scan",
            entity_id=scan_id,
            event_type=event_type,
            data={"status": status, "finding_count": finding_count, 
                  "severity_breakdown": severity_breakdown},
            triggered_by=triggered_by,
            aggregate_type="scan",
            aggregate_id=scan_id
        )
    
    async def rebuild_scan_state(self, scan_id):
        """Rebuild state from events for disaster recovery."""
        events = await self.events.get_events_for_aggregate("scan", scan_id)
        state = {"scan_id": str(scan_id), "status": None, "events": []}
        
        for event in events:
            if event.event_type == EventType.SCAN_CREATED.value:
                state["status"] = "pending"
            elif event.event_type == EventType.SCAN_STARTED.value:
                state["status"] = "running"
            elif event.event_type == EventType.SCAN_COMPLETED.value:
                state["status"] = "completed"
                state.update(event.data)
        
        return state
```

#### 5. API Endpoints

```python
# File: backend/services/core_engine/main.py (additions)
from fastapi import APIRouter, Query
from uuid import UUID
from datetime import datetime

router = APIRouter(prefix="/api/v1")

@router.get("/scans/{scan_id}/events")
async def get_scan_events(scan_id: UUID, limit: int = 100, offset: int = 0):
    """Get event history for a scan."""
    events = await store.get_events_for_aggregate("scan", scan_id)
    return {"events": events[offset:offset+limit], "total": len(events)}

@router.get("/scans/{scan_id}/state-at")
async def get_scan_state_at(scan_id: UUID, at_time: datetime = Query(...)):
    """Get scan state at a specific point in time."""
    state = await repo.rebuild_scan_state(scan_id)
    return {"scan_id": str(scan_id), "at_time": at_time, "state": state}

@router.get("/audit/findings-created")
async def audit_findings_created(
    from_time: datetime = Query(default=None),
    to_time: datetime = Query(default=None)
):
    """Audit trail for finding creation events."""
    events = await store.get_events_by_type(EventType.FINDING_CREATED, 
                                            since=from_time, limit=1000)
    return {"events": events, "total": len(events)}
```

#### 6. Integration Test

```python
# File: tests/integration/test_event_sourcing.py
from uuid import uuid4
from datetime import datetime, timezone
import pytest

class TestEventSourcing:
    async def test_scan_lifecycle_events(self):
        async with get_session() as session:
            repo = ScanRepository(session)
            scan = await repo.create_scan(uuid4(), {}, "test")
            await repo.start_scan(scan.scan_id, "test")
            await repo.mark_scan_complete(scan.scan_id, "completed", 10, {})
            
            events = await store.get_events_for_aggregate("scan", scan.scan_id)
            assert len(events) >= 3
    
    async def test_state_reconstruction(self):
        async with get_session() as session:
            repo = ScanRepository(session)
            scan = await repo.create_scan(uuid4(), {}, "test")
            await repo.start_scan(scan.scan_id)
            await repo.mark_scan_complete(scan.scan_id, "completed", 5, {})
            
            state = await repo.rebuild_scan_state(scan.scan_id)
            assert state["status"] == "completed"
            assert state["finding_count"] == 5
```

### Acceptance Criteria

- [ ] domain_events table exists with proper indexes
- [ ] EventStore.append_event() persists events with sequence numbers
- [ ] ScanRepository records events for all state changes
- [ ] API: GET /api/v1/scans/{scan_id}/events returns event history
- [ ] API: GET /api/v1/scans/{scan_id}/state-at returns historical state
- [ ] API: GET /api/v1/audit/findings-created returns audit trail
- [ ] Test: Delete scan row, rebuild from events

### Rollback Strategy

**Time:** <10 minutes

```bash
# Drop table and revert changes
psql -h postgres -U attackbot -c "DROP TABLE IF EXISTS domain_events;"
psql -h postgres -U attackbot -c "DROP SEQUENCE IF EXISTS domain_event_sequence_seq;"
git checkout HEAD~1 -- backend/shared/models/event_store.py
git checkout HEAD~1 -- backend/shared/event_sourcing/event_store.py
git checkout HEAD~1 -- backend/services/core_engine/repository.py
```

### Testing Checklist

- [ ] Unit test: DomainEvent model
- [ ] Unit test: EventStore methods
- [ ] Integration test: Scan lifecycle events
- [ ] Integration test: State reconstruction
- [ ] Integration test: API endpoints
- [ ] E2E test: Delete scan, rebuild from events

---

## Sprint Timeline

| Day | Engineer A | Engineer B | Activities |
|-----|------------|------------|------------|
| 1 | Payload schema | Event model + migration | Core setup |
| 2 | Aggregator updates | EventStore service | Implementation |
| 3 | Reporter updates | Repository events | Integration |
| 4 | Performance testing | Audit API endpoints | Testing |
| 5 | Tuning | Temporal queries | Optimization |
| 6 | Documentation | State reconstruction test | Final verification |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Event Sourcing scope too large | High | High | Focus on Scans only, expand later |
| Schema breaks compatibility | Medium | High | Backward compatibility with payload_version |
| Performance issues | Low | Medium | Proper indexing |
| Data inconsistency | Low | High | All changes go through repository |

---

## Rollback & Contingency

| Issue | Rollback | Time | Contingency |
|-------|----------|------|-------------|
| #6 | Revert schema + restore HTTP | <15min | Partial rollback possible |
| #7 | Drop table + revert repo | <10min | **Spill to Sprint 4** |

**If Sprint 3 at risk:** Prioritize #6, move #7 to Sprint 4 with reduced scope.

---

## Success Criteria

- [ ] Reporter generates reports without HTTP calls to Core Engine
- [ ] Report generation time for 100 findings <500ms
- [ ] Scan event history queryable via API
- [ ] Scan state rebuildable from events (test verified)

---

## Dependencies

### Internal
- #6: Independent
- #7: Depends on #3 (Idempotency) for reliable processing

### External
- PostgreSQL (event store)
- Existing message queue

---

## Integration Points

### Modified (Issue #6)
1. `backend/shared/schemas/report_jobs.py` - Extended schema
2. `backend/services/core_engine/pipeline/aggregator.py` - Embed data
3. `backend/services/reporter/worker.py` - Use embedded data
4. `backend/services/reporter/clients/core_engine.py` - Deprecated

### New (Issue #7)
1. `backend/shared/models/event_store.py` - DomainEvent
2. `backend/shared/event_sourcing/event_store.py` - EventStore
3. `alembic/versions/007_add_domain_events.py` - Migration

### Modified (Issue #7)
1. `backend/services/core_engine/repository.py` - Event recording
2. `backend/services/core_engine/main.py` - API endpoints

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-22 | Mistral Vibe | Initial Sprint 3 implementation guide |

---

**Generated by Mistral Vibe.**
**Co-Authored-By: Mistral Vibe <vibe@mistral.ai>**

---

**Next:** [Sprint #4: P2 - Operational Excellence](./sprint#4.md)  
**Previous:** [Sprint #2: P0/P1 - Resilience Foundation](./sprint#2.md)  
**Related:** [Issue_Sprints.md](./Issue_Sprints.md), [Issues#1.md](./Issues#1.md), [Issues#2.md](./Issues#2.md)
