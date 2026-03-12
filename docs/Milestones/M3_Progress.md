# AttackBot M3 — Debug Progress Log
> Last updated: 2026-03-12

---

## Current Status: ALL SYSTEMS UP

| Component | Status |
|-----------|--------|
| Migration 003 (head) | DONE |
| All 12 tables in DB | DONE |
| Tools in Docker image | DONE — nuclei, subfinder, ffuf, httpx, dnsx, alterx |
| core-engine health | DONE — 200 OK on :8002/api/v1/health |
| core-worker Celery | DONE — connected to RabbitMQ, scan_task registered |
| Test scan | NEXT |

---

## Errors Fixed (Full Log)

1. Migration duplicate index — removed ix_scans_program_id and ix_scans_status from 003_engine.py
2. Docker image stale — must use --no-cache when editing Python files
3. Dockerfile wget exit code 8 — replaced /latest/ URLs with pinned version direct URLs
4. await init_db() TypeError — init_db is sync, removed await
5. Typo database_ur — fixed to database_url, forced --no-cache rebuild
6. HealthStatus.healthy — enum is uppercase (HEALTHY), fixed all references
7. HealthResponse missing timestamp — added datetime.now(timezone.utc)
8. ScanTimeoutError missing — added to backend/shared/exceptions.py
9. rabbitmq_user not on EngineConfig — worker.py now uses config.rabbitmq_url directly

---

## Next: Trigger a Test Scan

Get a program_id:
```powershell
docker compose -f infra/docker-compose.yml --env-file .env exec postgres psql -U attackbot -d attackbot -c "SELECT program_id, handle FROM programs LIMIT 5;"
```

Trigger a scan:
```powershell
curl -X POST http://localhost:8002/api/v1/scans/start `
  -H "Content-Type: application/json" `
  -d '{"program_id":"<uuid>","scope":{"in_scope":["*.example.com"],"out_of_scope":[]},"feature_flags":{"sqli":false,"ssrf":false,"crlf":false}}'
```

Poll status:
```powershell
curl http://localhost:8002/api/v1/scans
```

Check findings:
```powershell
curl http://localhost:8002/api/v1/scans/<scan_id>/findings
```

Verify RabbitMQ report.jobs queue at http://localhost:15672