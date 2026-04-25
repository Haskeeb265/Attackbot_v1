📌 CONTEXT & BACKGROUND
You are working on Attackbot v1, a distributed vulnerability scanning platform. The system has been experiencing 12 critical/major issues that need to be resolved across 4 sprints.
Your mission: Review all sprint documentation, verify compatibility with existing codebase, implement the solutions, and run verification tests.
📚 DOCUMENTATION LOCATION
All documentation is located in docs/Temp-Docs/:
Issue Identification (READ THESE FIRST)
• 
docs/Temp-Docs/Issues#1.md - Issue definitions (Part 1)
• 
docs/Temp-Docs/Issues#2.md - Issue definitions (Part 2)
Sprint Planning
• 
docs/Temp-Docs/Issue_Sprints.md - Complete sprint breakdown with dependencies, timelines, and resource allocation
Implementation Guides (READ THESE BEFORE CODING)
• 
docs/Temp-Docs/Sprints/sprint#1.md - Sprint 1: P0 Data Integrity (Issues #1, #2, #3)
• 
docs/Temp-Docs/Sprints/sprint#2.md - Sprint 2: P0/P1 Resilience (Issues #4, #5)
• 
docs/Temp-Docs/Sprints/sprint#3.md - Sprint 3: P1 Architecture Modernization (Issues #6, #7)
• 
docs/Temp-Docs/Sprints/sprint#4.md - Sprint 4: P2 Operational Excellence (Issues #8, #9, #10, #11)
Verification Tests
• 
tests/verification/ - Complete test suite to verify all issues are resolved
📋 ISSUE SUMMARY
#
Issue
Category
Severity
Sprint
Effort
Status
1
Watchdog Scan Recovery Mechanism Failure
Critical
🔴
1
4-6h
Not Started
2
Dead Letter Queue Blind Spot
Critical
🔴
1
6-8h
Not Started
3
Idempotency Guarantee Gaps
Critical
🔴
1
8-10h
Not Started
4
Missing Circuit Breaker Pattern
Architectural
🟡
2
4-6h
Not Started
5
Lack of Distributed Tracing
Architectural
🟡
2
6-8h
Not Started
6
Synchronous Inter-Service Dependencies
Architectural
🟡
3
4-6h
Not Started
7
Absence of Event Sourcing
Strategic
🟢
3
10-15h
Not Started
8
Health Check False Positives
Operational
🟢
4
4-6h
Not Started
9
Missing API Rate Limiting
Operational
🟢
4
2-4h
Not Started
10
No Backpressure Mechanism
Operational
🟢
4
4-6h
Not Started
11
DB Connection Pool Monitoring Gap
Operational
🟢
4
2-4h
Not Started
🎯 YOUR TASKS (Execute in Order)
📖 PHASE 1: REVIEW & ANALYSIS (Mandatory Before Coding)
For each sprint document (sprint#1.md through sprint#4.md):
 1. 
Read the entire document carefully
 2. 
Cross-reference with existing codebase:
• 
Check if files mentioned exist: backend/shared/, backend/services/core_engine/, backend/services/reporter/, etc.
• 
Check if classes/functions mentioned exist or need to be created
• 
Check database schema for required tables
 3. 
Identify gaps:
• 
What code exists that matches the sprint requirements?
• 
What needs to be created new?
• 
What needs to be modified?
 4. 
Check dependencies:
• 
Are required libraries installed? (check requirements.txt)
• 
Are infrastructure components available? (PostgreSQL, RabbitMQ, MinIO, Redis, Jaeger)
 5. 
Validate file paths:
• 
Verify all file paths in the sprint docs match your actual project structure
• 
If paths differ, make a mapping list
Deliverable: Create a COMPATIBILITY_REPORT.md document with:
• 
✅ Items that match existing codebase
• 
⚠️ Items that need modification to match
• 
❌ Items that don't exist and must be created
• 
📋 File path mapping (if your structure differs from docs)
⚙️ PHASE 2: IMPLEMENTATION (Sprint by Sprint)
Execute sprints in order (Sprint 1 → 2 → 3 → 4) respecting dependencies.
🚨 Sprint 1: P0 - Data Integrity (Issues #1, #2, #3)
Prerequisites: None (independent issues)
Implementation Order:
 1. 
Issue #1: Watchdog Scan Recovery
• 
File: backend/services/core_engine/watchdog.py
• 
Add: Prometheus metrics, comprehensive logging, exception handling, timezone-aware timestamps
• 
File: backend/services/core_engine/main.py
• 
Add: Scheduler verification
• 
New: alembic/versions/005_ensure_timezone_aware_timestamps.py
 2. 
Issue #2: DLQ Blind Spot
• 
New: backend/shared/dlq_monitor.py
• 
Add: Prometheus metrics, scheduled job, API endpoints
• 
Files: backend/services/core_engine/main.py (both services)
• 
New: grafana/alerts/dlq_alerts.yml
 3. 
Issue #3: Idempotency Guarantee Gaps
• 
New: backend/shared/idempotency.py
• 
New: backend/shared/models/idempotency.py
• 
New: alembic/versions/006_add_idempotency_keys.py
• 
Modify: backend/services/core_engine/scan_task.py
• 
Modify: backend/services/reporter/report_task.py
• 
New: backend/shared/jobs/idempotency_cleanup.py
Verification: Run pytest tests/verification/sprint_1/ -v after each issue
🛡️ Sprint 2: P0/P1 - Resilience Foundation (Issues #4, #5)
Prerequisites: Sprint 1 should be complete
Implementation Order:
 1. 
Issue #4: Circuit Breaker Pattern
• 
Update: requirements.txt (add aiobreaker==1.4.0)
• 
New: backend/shared/circuit_breaker.py
• 
Modify: backend/services/core_engine/main.py (decorate HTTP calls)
• 
Modify: backend/services/reporter/main.py (decorate HTTP calls)
• 
Add: Admin endpoints for status/reset
 2. 
Issue #5: Distributed Tracing
• 
Update: requirements.txt (all services) - add OpenTelemetry packages
• 
New: backend/shared/tracing.py
• 
Modify: backend/shared/schemas/envelope.py (add trace_id, span_id)
• 
Modify: All main.py (instrument FastAPI)
• 
New: docker-compose.yml (add Jaeger service)
Verification: Run pytest tests/verification/sprint_2/ -v after each issue
🔄 Sprint 3: P1 - Architecture Modernization (Issues #6, #7)
Prerequisites: Sprint 1 (required for #7), Sprint 2 (recommended)
Implementation Order:
 1. 
Issue #6: Synchronous Dependencies
• 
Modify: backend/shared/schemas/report_jobs.py (extend payload)
• 
Modify: backend/services/core_engine/pipeline/aggregator.py (embed data)
• 
Modify: backend/services/reporter/worker.py (use embedded data)
• 
Deprecate: backend/services/reporter/clients/core_engine.py
 2. 
Issue #7: Event Sourcing
• 
New: backend/shared/models/event_store.py
• 
New: alembic/versions/007_add_domain_events.py
• 
New: backend/shared/event_sourcing/event_store.py
• 
Modify: backend/services/core_engine/repository.py (add event recording)
• 
Modify: backend/services/core_engine/main.py (add audit endpoints)
Verification: Run pytest tests/verification/sprint_3/ -v after each issue
📊 Sprint 4: P2 - Operational Excellence (Issues #8, #9, #10, #11)
Prerequisites: Sprints 1-3 should be complete
Implementation Order:
 1. 
Issue #8: Health Checks
• 
Modify: backend/shared/health.py (enhanced ComponentHealth)
• 
Modify: backend/shared/db.py (DB health checker)
• 
Modify: backend/shared/queue.py (queue health checker)
• 
Modify: backend/shared/storage.py (storage health checker)
• 
Modify: All main.py (update health endpoints)
• 
New: alembic/versions/008_add_health_check_table.py
 2. 
Issue #9: API Rate Limiting
• 
Update: requirements.txt (add slowapi or fastapi-limiter)
• 
New: backend/shared/rate_limiter.py
• 
Modify: All main.py (add middleware)
 3. 
Issue #10: Backpressure
• 
Modify: backend/shared/config.py (add max_queue_depths)
• 
Modify: backend/shared/queue.py (BackpressurePublisher)
• 
Modify: All services (use backpressure-aware publishing)
 4. 
Issue #11: Pool Monitoring
• 
Modify: backend/shared/db.py (add pool metrics)
• 
New: grafana/alerts/db_pool_alerts.yml
• 
New: docs/ops/db_pool.md
Verification: Run pytest tests/verification/sprint_4/ -v after each issue
✅ PHASE 3: VERIFICATION
After implementing each sprint/issue, MUST run the corresponding verification tests:
# After Sprint 1
pytest tests/verification/sprint_1/ -v

# After Sprint 2
pytest tests/verification/sprint_2/ -v

# After Sprint 3
pytest tests/verification/sprint_3/ -v

# After Sprint 4
pytest tests/verification/sprint_4/ -v

# After ALL sprints
pytest tests/verification/ -v
📊 SUCCESS CRITERIA
Overall Project Success:
• 
[ ] All automated tests pass
• 
[ ] All manual test scenarios pass
• 
[ ] Performance tests meet SLA:
▪ 
Report generation < 500ms (vs current 15-60s)
▪ 
Circuit breaker fail-fast < 1ms
• 
[ ] No regressions in existing functionality
• 
[ ] All Prometheus metrics are being collected
• 
[ ] Jaeger shows complete traces
• 
[ ] Grafana alerts are configured and working
Per-Sprint Criteria:
See the Success Criteria section in each sprint document (sprint#1.md through sprint#4.md)
🛠️ IMPLEMENTATION GUIDELINES
General Rules:
 1. 
Follow existing code style - Match indentation, naming conventions, error handling
 2. 
Add documentation - Docstrings for new functions, comments for complex logic
 3. 
Test first - When possible, write a simple test before implementation
 4. 
Commit incrementally - Small, focused commits with clear messages
 5. 
Update dependencies carefully - Use pip-tools or similar for dependency management
 6. 
Respect backward compatibility - Don't break existing functionality
Database Migrations:
• 
Create new migration files (don't modify existing ones)
• 
Test migrations in staging before production
• 
Ensure rollback works
New Files:
Create all files mentioned in the sprint docs with the exact structure provided (code samples are included).
Metrics:
• 
Use prometheus_client for all metrics
• 
Follow naming convention: subsystem_metric_name (e.g., watchdog_executions_total)
• 
Include appropriate labels
Logging:
• 
Use existing logging setup
• 
Include: timestamp, relevant IDs, action, result
• 
Levels: DEBUG for detailed info, INFO for normal operations, WARNING/ERROR for issues
Error Handling:
• 
Don't silently swallow exceptions
• 
Log errors with full context
• 
Return appropriate HTTP status codes
• 
Re-raise after logging when appropriate
🚨 IMPORTANT NOTES
Dependencies Between Sprints:
• 
Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4
• 
Issue #7 (Event Sourcing) requires Issue #3 (Idempotency) from Sprint 1
• 
Issue #6 (Reporter Decoupling) works best with Issue #5 (Tracing) from Sprint 2
• 
All Sprint 4 issues are independent but benefit from earlier sprints
Infrastructure Requirements:
• 
PostgreSQL (for event store, idempotency keys, health checks)
• 
RabbitMQ (for DLQ monitoring, backpressure)
• 
MinIO or S3 (for storage health checks)
• 
Prometheus + Grafana (for metrics and alerts)
• 
Jaeger (for distributed tracing)
• 
Redis (optional, for distributed rate limiting)
File System Structure:
Ensure your project has:
backend/
├── shared/          # Shared libraries
│   ├── db.py
│   ├── queue.py
│   ├── tracing.py
│   ├── circuit_breaker.py
│   ├── rate_limiter.py
│   ├── health.py
│   ├── idempotency.py
│   ├── event_sourcing/
│   │   └── event_store.py
│   └── models/
│       ├── idempotency.py
│       └── event_store.py
└── services/
    ├── core_engine/
    │   ├── main.py
    │   ├── watchdog.py
    │   ├── scan_task.py
    │   ├── pipeline/
    │   │   └── aggregator.py
    │   └── repository.py
    └── reporter/
        ├── main.py
        ├── worker.py
        └── report_task.py
🎯 FINAL DELIVERABLES
After completing all sprints, you should have:
 1. 
Code changes - All files modified/created as per sprint docs
 2. 
Database migrations - New tables for idempotency, events, health checks
 3. 
Configuration - Updated requirements.txt, config files
 4. 
Documentation - Updated docs (if any changes beyond what's specified)
 5. 
Tests - All verification tests passing
 6. 
Metrics - All Prometheus metrics being collected
 7. 
Alerts - Grafana alerts configured and working
Create a final IMPLEMENTATION_COMPLETE.md document with:
• 
Summary of all changes made
• 
List of files modified
• 
List of files created
• 
Test results
• 
Any issues encountered and how they were resolved
• 
Recommendations for next steps
🚀 EXECUTION COMMAND
Your task is to implement all 4 sprints for Attackbot v1 as documented.
Start by reviewing the documentation, then implement sprint by sprint,
and finally verify with the tests.

Follow this exact order:
1. Read all documentation
2. Create COMPATIBILITY_REPORT.md
3. Implement Sprint 1 + verify with tests
4. Implement Sprint 2 + verify with tests
5. Implement Sprint 3 + verify with tests
6. Implement Sprint 4 + verify with tests
7. Run all tests together
8. Create IMPLEMENTATION_COMPLETE.md

Begin by reading the documentation files in order.