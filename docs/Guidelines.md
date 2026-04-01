# AttackBot — Development Guidelines
> Born from M3 debugging. Every rule here was learned the hard way.
> Read this before writing a single line of code in any new milestone.

---

## 1. Docker: Always Rebuild After Editing Files

Docker bakes files into images at build time. Editing a file on disk has **zero effect**
on a running container until you rebuild the image.

| What you changed | Command |
|------------------|---------|
| Any Python service file | `docker compose ... build --no-cache <service>` |
| Shared library (`backend/shared/`) | `docker compose ... build --no-cache core-engine core-worker` (all services that use it) |
| Migration file | `docker compose ... build --no-cache migrate` |
| Dockerfile itself | `docker compose ... build --no-cache <service>` |

**Rule:** If the error message quotes old code after you already fixed it, you forgot `--no-cache`.

**How to confirm the container has your file:**
```powershell
docker compose ... run --rm <service> cat /app/path/to/your/file.py
```

---

## 2. Migrations: Never Duplicate Indexes Across Versions

If migration `002` creates an index on a table, migration `003` must NOT create it again —
even if `003` extends that same table.

**Before adding any `op.create_index()` call, check all previous migrations:**
```powershell
findstr /r "create_index.*ix_scans" backend\migrations\versions\*.py
```

If the index already exists in an earlier migration, delete the line from the new one.
Add a comment instead:
```python
# NOTE: ix_scans_program_id already created in 002 — do not recreate
```

**Rule:** One index, one migration. Never recreate.

---

## 3. Migrations: Always Rebuild the Migrate Container

The migrate container is also a baked image. Editing a migration file on disk does nothing
until you rebuild:

```powershell
# Edit migration file on disk first, then:
docker compose ... build migrate
docker compose ... run --rm migrate alembic -c /app/backend/migrations/alembic.ini upgrade head
docker compose ... run --rm migrate alembic -c /app/backend/migrations/alembic.ini current
# Expected: 00X (head)
```

**Verify the file change actually landed in the container before running:**
```powershell
findstr /n "the_thing_you_removed" backend\migrations\versions\003_engine.py
# Expected: no output (zero matches means the line is gone)
```

---

## 4. Shared Library: Check Before Using

Before calling any function from `backend/shared/`, verify:

- Is the function `async` or sync? (`async def` vs `def`)
- Does the class have the attribute you're referencing?
- What are the required constructor fields?

**Specific things to always verify:**

| File | What to check |
|------|---------------|
| `shared/db.py` | `init_db()` is **sync** — never `await` it |
| `shared/config.py` | RabbitMQ is `rabbitmq_url` (full URL) — no separate user/password/host fields |
| `shared/health.py` | `HealthStatus` enum is **UPPERCASE** — `HEALTHY`, `DEGRADED`, `UNHEALTHY` |
| `shared/health.py` | `HealthResponse` requires `timestamp` field — pass `datetime.now(timezone.utc)` |
| `shared/exceptions.py` | Check if your exception class exists before importing it |

**Quick check command:**
```powershell
type backend\shared\<file>.py
```

---

## 5. Shared Exceptions: Add Missing Ones to the Right Place

All exceptions live in `backend/shared/exceptions.py`. Nowhere else.

If a service needs a new exception type, add it to `shared/exceptions.py` first,
then import it in the service.

**Never define exceptions inside a service module.**

When adding a new exception, follow the hierarchy:
```python
class ScanTimeoutError(ScanError):    # child of the appropriate base
    """One clear sentence describing when this is raised."""
```

---

## 6. Dockerfile: Use Pinned URLs for GitHub Downloads

GitHub `/releases/latest/download/` URLs use redirect chains that fail inside Docker
build networks with exit code 8.

**Always use pinned version direct URLs:**
```dockerfile
# WRONG — fails with exit code 8
wget https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip

# CORRECT — direct URL, no redirects
wget https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_linux_amd64.zip
```

**Also: use exact filenames in `rm`, not globs:**
```dockerfile
# WRONG — glob can match unexpected files
rm nuclei_*.zip

# CORRECT — exact filename
rm nuclei_3.3.9_linux_amd64.zip
```

**Current pinned versions (update when upgrading):**
| Tool | Version | URL pattern |
|------|---------|-------------|
| nuclei | v3.3.9 | `nuclei_3.3.9_linux_amd64.zip` |
| httpx | v1.6.10 | `httpx_1.6.10_linux_amd64.zip` |
| subfinder | v2.6.6 | `subfinder_2.6.6_linux_amd64.zip` |
| dnsx | v1.2.1 | `dnsx_1.2.1_linux_amd64.zip` |
| alterx | v0.0.4 | `alterx_0.0.4_linux_amd64.zip` |
| ffuf | v2.1.0 | `ffuf_2.1.0_linux_amd64.tar.gz` |

---

## 7. docker-compose.yml: Property Placement

YAML indentation errors cause silent misconfigurations. Properties must be at the
correct nesting level.

```yaml
# WRONG — ports nested inside build
  core-engine:
    build:
      context: ..
      dockerfile: ...
      ports:          # ← WRONG: this is a build property, not valid
        - "8002:8002"

# CORRECT — ports at service level
  core-engine:
    build:
      context: ..
      dockerfile: ...
    ports:            # ← CORRECT: sibling of build, not child
      - "8002:8002"
    environment:
      ...
```

**Rule:** `ports`, `environment`, `networks`, `volumes`, `depends_on`, `healthcheck`
are always siblings of `build` — never children of it.

---

## 8. Celery Workers: Use rabbitmq_url Directly

`BaseServiceConfig` exposes RabbitMQ as a single URL field `rabbitmq_url`.
There are no separate `rabbitmq_user`, `rabbitmq_password`, `rabbitmq_host` fields.

```python
# WRONG
app = Celery(
    "worker",
    broker=f"amqp://{config.rabbitmq_user}:{config.rabbitmq_password}@{config.rabbitmq_host}/"
)

# CORRECT
app = Celery(
    "worker",
    broker=config.rabbitmq_url,
)
```

---

## 9. Port Exposure: Services Are Internal by Default

Services inside Docker Compose can reach each other by service name on their internal port.
They are NOT reachable from your host machine unless you add a `ports` mapping.

**Internal only (default):**
```
core-engine:8002  →  reachable by other containers as http://core-engine:8002
                  →  NOT reachable from your laptop as http://localhost:8002
```

**Exposed to host (add ports mapping):**
```yaml
ports:
  - "8002:8002"   # host:container
```

Only expose ports you actually need to call from outside Docker (for dev/testing).
In production, only the API gateway should be exposed.

---

## 10. General Debugging Workflow

When a container fails to start, follow this sequence every time:

```powershell
# 1. Check what the error actually is
docker compose ... logs <service> --tail 30

# 2. Find the exact line in the error traceback
# 3. Locate the file on disk
# 4. Fix the file
# 5. Rebuild with --no-cache (NOT without it)
docker compose ... build --no-cache <service>
# 6. Restart
docker compose ... up -d <service>
# 7. Check logs again
docker compose ... logs <service> --tail 20
```

**Never skip step 5.** The most common wasted time in M3 was fixing a file
and restarting without rebuilding. The old cached image ran every time.

---

## 11. Checklist Before Starting Each New Milestone

Before writing any M(N) code, verify M(N-1) is intact:

```powershell
# All containers healthy
docker compose ... ps

# Migration at correct head
docker compose ... run --rm migrate alembic ... current

# Previous service health endpoints responding
curl http://localhost:8001/api/v1/health   # scraper
curl http://localhost:8002/api/v1/health   # core-engine

# No workers in crash loop
docker compose ... logs core-worker --tail 10
```

If anything is broken, fix it before touching new code.
Debugging two milestones simultaneously is significantly harder than one.