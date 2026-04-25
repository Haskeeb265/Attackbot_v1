"""
Verification Tests for Attackbot v1 Issue Resolution

This module contains test suites to verify that all issues identified in:
- docs/Temp-Docs/Issues#1.md
- docs/Temp-Docs/Issues#2.md

And documented in:
- docs/Temp-Docs/Issue_Sprints.md

Have been properly resolved by the sprint implementations:
- Sprint 1: P0 - Data Integrity (Issues #1, #2, #3)
- Sprint 2: P0/P1 - Resilience Foundation (Issues #4, #5)
- Sprint 3: P1 - Architecture Modernization (Issues #6, #7)
- Sprint 4: P2 - Operational Excellence (Issues #8, #9, #10, #11)

Test Organization:
-----------------
verification/
├── __init__.py                 # This file
├── sprint_1/                   # Sprint 1: Data Integrity
│   ├── __init__.py
│   ├── test_watchdog_recovery.py  # Issue #1
│   ├── test_dlq_monitoring.py     # Issue #2
│   └── test_idempotency.py         # Issue #3
├── sprint_2/                   # Sprint 2: Resilience Foundation
│   ├── __init__.py
│   ├── test_circuit_breaker.py     # Issue #4
│   └── test_tracing.py             # Issue #5
├── sprint_3/                   # Sprint 3: Architecture Modernization
│   ├── __init__.py
│   ├── test_reporter_decoupling.py # Issue #6
│   └── test_event_sourcing.py       # Issue #7
└── sprint_4/                   # Sprint 4: Operational Excellence
    ├── __init__.py
    ├── test_health_checks.py       # Issue #8
    ├── test_rate_limiting.py       # Issue #9
    ├── test_backpressure.py        # Issue #10
    └── test_pool_monitoring.py     # Issue #11

Usage:
------
# Run all verification tests
pytest tests/verification/ -v

# Run tests for a specific sprint
pytest tests/verification/sprint_1/ -v

# Run tests for a specific issue
pytest tests/verification/sprint_1/test_watchdog_recovery.py -v

# Run only fast tests (skip slow performance tests)
pytest tests/verification/ -v -m "not slow"

# Run only slow tests (performance tests)
pytest tests/verification/ -v -m "slow"

Test Categories:
----------------
1. Unit Tests: Test individual functions and classes
2. Integration Tests: Test component interactions
3. API Tests: Test HTTP endpoints
4. Performance Tests: Test speed and scalability (marked with @pytest.mark.slow)

Note:
-----
Some tests require specific infrastructure (RabbitMQ, PostgreSQL, MinIO, Jaeger)
to be running. These tests may be skipped if dependencies are not available.
"""

# Import sprint test modules to make them discoverable
# This is not strictly necessary as pytest will discover them anyway,
# but it makes IDE navigation easier
try:
    from . import sprint_1
    from . import sprint_2
    from . import sprint_3
    from . import sprint_4
except ImportError:
    # Some dependencies may not be available in all environments
    pass
