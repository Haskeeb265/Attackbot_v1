#!/usr/bin/env bash
# scripts/healthcheck_all.sh
# Run after: docker compose -f infra/docker-compose.yml up -d
# Waits for all services to report healthy and validates init containers.

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No colour

COMPOSE_FILE="${COMPOSE_FILE:-infra/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-.env}"

echo -e "${YELLOW}AttackBot — Startup Validation${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Phase 1: FastAPI service health ───────────────────────────────────

declare -A SERVICES=(
    ["scraper"]="http://localhost:8001/api/v1/health"
    ["core-engine"]="http://localhost:8002/api/v1/health"
    ["reporter"]="http://localhost:8003/api/v1/health"
    ["attack-graph-engine"]="http://localhost:8006/api/v1/health"
    ["api-gateway"]="http://localhost:8000/api/v1/health"
)

echo ""
echo "Checking FastAPI service health..."
FAILED=0

for service in "${!SERVICES[@]}"; do
    url="${SERVICES[$service]}"
    echo -n "  ${service}... "
    for i in $(seq 1 36); do  # 36 * 5s = 3 minutes
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}healthy${NC}"
            break
        fi
        if [ "$i" -eq 36 ]; then
            echo -e "${RED}TIMEOUT after 3 minutes${NC}"
            FAILED=1
        fi
        sleep 5
    done
done

# ── Phase 2: MinIO bucket verification ────────────────────────────────

echo ""
echo "Checking MinIO buckets..."
REQUIRED_BUCKETS=("reports" "evidence" "js-assets" "summaries")
for bucket in "${REQUIRED_BUCKETS[@]}"; do
    echo -n "  bucket/${bucket}... "
    if docker compose -f "$COMPOSE_FILE" run --rm --no-deps minio-init \
        sh -c "mc alias set local http://minio:9000 \$MINIO_ROOT_USER \$MINIO_ROOT_PASSWORD > /dev/null 2>&1 && mc ls local/${bucket}" > /dev/null 2>&1; then
        echo -e "${GREEN}exists${NC}"
    else
        echo -e "${RED}MISSING${NC}"
        FAILED=1
    fi
done

# ── Phase 3: Alembic migration ────────────────────────────────────────

echo ""
echo "Checking Alembic migration state..."
echo -n "  alembic current... "
REVISION=$(docker compose -f "$COMPOSE_FILE" run --rm --no-deps migrate \
    alembic --config backend/migrations/alembic.ini current 2>&1 | tail -1)
if echo "$REVISION" | grep -q "001"; then
    echo -e "${GREEN}revision 001 applied${NC}"
else
    echo -e "${RED}unexpected revision: ${REVISION}${NC}"
    FAILED=1
fi

# ── Phase 4: Grafana ──────────────────────────────────────────────────

echo ""
echo -n "Checking Grafana... "
if curl -sf "http://localhost:3000/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}healthy${NC}"
else
    echo -e "${YELLOW}not ready (non-fatal)${NC}"
fi

# ── Summary ───────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}All checks passed. System is ready. 🚀${NC}"
    echo ""
    echo "  API Gateway:  http://localhost:8000"
    echo "  Grafana:      http://localhost:3000"
    echo "  RabbitMQ UI:  http://localhost:15672"
    exit 0
else
    echo -e "${RED}One or more checks failed. Review logs above.${NC}"
    echo "  Run: docker compose -f infra/docker-compose.yml logs <service>"
    exit 1
fi