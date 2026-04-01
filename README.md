# AttackBot — Infrastructure

## Cold Boot

```bash
# 1. Copy and edit the environment file
cp .env.example .env

# 2. Start everything
docker compose -f infra/docker-compose.yml --env-file .env up -d

# 3. Wait ~3–4 minutes, then validate
./scripts/healthcheck_all.sh
```

Expected cold boot time: **3–4 minutes** from `docker compose up` to all services healthy.

## Startup Order

Six phases execute sequentially via `depends_on` + `healthcheck` conditions:

| Phase | Services | Wait condition |
|-------|----------|----------------|
| 1 | postgres, redis, rabbitmq, neo4j, minio, vault | None (start unconditionally) |
| 2 | migrate, minio-init, vault-init | `service_healthy` on upstream infra |
| 3 | scraper, core-engine, reporter, attack-graph-engine | `service_completed_successfully` on Phase 2 |
| 4 | core-worker, reporter-worker | `service_healthy` on their API service |
| 5 | browser-worker, api-fuzzer-worker, js-analysis-worker, scenario-runner, exploit-verifier, ai-analysis-worker | `service_healthy` on rabbitmq |
| 6 | api-gateway | `service_healthy` on all Phase 3 services |

## Service Ports

| Service | Port | Notes |
|---------|------|-------|
| api-gateway | 8000 | Single external entry point |
| scraper | 8001 | Internal only |
| core-engine | 8002 | Internal only |
| reporter | 8003 | Internal only |
| attack-graph-engine | 8006 | Internal only |
| RabbitMQ Management UI | 15672 | dev only |
| Grafana | 3000 | dev only |

## Triggering a Manual Scan

```bash
# Via API Gateway (M2+ required)
curl -X POST http://localhost:8000/scraper/api/v1/scrape/trigger \
  -H "X-API-Key: <your-key>"
```

## Inspecting the DLQ

```bash
# Via Core Engine API
curl http://localhost:8002/api/v1/queue/dlq/inspect
```

## Replaying a DLQ Message

```bash
curl -X POST http://localhost:8002/api/v1/queue/dlq/replay \
  -H "Content-Type: application/json" \
  -d '{"event_id": "<message-event-id>"}'
```

## Adding a New Platform Collector (M2+)

1. Create `backend/services/scraper/collectors/<platform>.py`
2. Subclass `BaseCollector` and implement `fetch_listing()`, `fetch_details()`, `normalize()`
3. Register in `CollectorRegistry` in `backend/services/scraper/collectors/__init__.py`
4. Add platform credentials to Vault: `secret/attackbot/platform/<platform_name>`

## Writing a New YAML Scenario (M9+)

1. Create `backend/services/scenario_runner/scenarios/<name>.yaml`
2. Follow the schema in `backend/shared/schemas/scenario.py`
3. Test against a local vulnerable target before deploying

## Vault Operations

Dev mode does **not** persist secrets across container restarts. After every restart:
- `vault-init` re-seeds placeholder paths automatically
- Platform API keys must be re-added manually or via a bootstrap script

To rotate a secret:
```bash
docker compose -f infra/docker-compose.yml exec vault \
  vault kv put secret/attackbot/platform/hackerone \
    api_username=<user> api_token=<new-token>
```

## Known Operational Constraints

| Constraint | Detail |
|-----------|--------|
| **Neo4j startup** | Takes 30–60s. `start_period: 60s` on the healthcheck is mandatory — do NOT reduce it. |
| **Vault dev mode** | Does not persist secrets across restarts. Acceptable locally. **Never use in production.** |
| **h2spacex (M9+)** | Requires raw socket access. Works in standard Docker. **Silently fails** in AWS Fargate and some GCP Cloud Run configurations. |
| **MinIO public access** | Intentionally disabled. All report access goes through pre-signed URLs via the Reporter API. Never run `mc anonymous set download`. |
| **Cold boot time** | Allow 3–4 minutes. Neo4j and Vault drive the long tail. |

## Checking Logs

```bash
# All services
docker compose -f infra/docker-compose.yml logs -f

# Single service
docker compose -f infra/docker-compose.yml logs -f scraper

# Last 100 lines
docker compose -f infra/docker-compose.yml logs --tail=100 core-engine
```