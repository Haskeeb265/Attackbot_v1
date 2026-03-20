# AttackBot - Infrastructure

> Last updated: 2026-03-17

**Dev**
1. `docker compose -f infra/docker-compose.yml --env-file .env up -d`
1. Exposes local ports for convenience: `8000` (api-gateway), `8001` (scraper), `8002` (core-engine), `15672` (RabbitMQ UI), `3000` (Grafana)

**Prod Overlay**
1. `docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml --env-file .env up -d`
1. Removes dev-only port mappings so only `api-gateway` is exposed externally
