# inspect_scan.ps1
# Usage: .\inspect_scan.ps1
# Shows exactly what the current/last scan found at each stage.

$compose = "docker compose -f infra/docker-compose.yml --env-file .env"
$psql    = "exec postgres psql -U attackbot -d attackbot -c"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ATTACKBOT SCAN INSPECTOR" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ── Latest scan ──────────────────────────────────────────────────────────────
Write-Host "[ LATEST SCAN ]" -ForegroundColor Yellow
Invoke-Expression "$compose $psql `"
SELECT scan_id, status, finding_count, started_at, completed_at, error_detail
FROM scans
ORDER BY created_at DESC LIMIT 1;
`""

# ── Stage progress ────────────────────────────────────────────────────────────
Write-Host "`n[ STAGE PROGRESS ]" -ForegroundColor Yellow
Invoke-Expression "$compose $psql `"
SELECT stage_number, stage_name, status, started_at, completed_at, output_summary, error_detail
FROM scan_stages
WHERE scan_id = (SELECT scan_id FROM scans ORDER BY created_at DESC LIMIT 1)
ORDER BY stage_number;
`""

# ── Assets discovered ─────────────────────────────────────────────────────────
Write-Host "`n[ ASSETS DISCOVERED ]" -ForegroundColor Yellow
Invoke-Expression "$compose $psql `"
SELECT asset_type, value, http_status, waf_detected, discovered_at
FROM assets
WHERE scan_id = (SELECT scan_id FROM scans ORDER BY created_at DESC LIMIT 1)
ORDER BY asset_type, value;
`""

# ── Asset count by type ───────────────────────────────────────────────────────
Write-Host "`n[ ASSET COUNT BY TYPE ]" -ForegroundColor Yellow
Invoke-Expression "$compose $psql `"
SELECT asset_type, COUNT(*) as count
FROM assets
WHERE scan_id = (SELECT scan_id FROM scans ORDER BY created_at DESC LIMIT 1)
GROUP BY asset_type
ORDER BY count DESC;
`""

# ── Endpoints found ───────────────────────────────────────────────────────────
Write-Host "`n[ ENDPOINTS FOUND (top 20) ]" -ForegroundColor Yellow
Invoke-Expression "$compose $psql `"
SELECT method, path, full_url, response_code, content_type
FROM endpoints
WHERE scan_id = (SELECT scan_id FROM scans ORDER BY created_at DESC LIMIT 1)
ORDER BY response_code, full_url
LIMIT 20;
`""

# ── JS assets ─────────────────────────────────────────────────────────────────
Write-Host "`n[ JS ASSETS ]" -ForegroundColor Yellow
Invoke-Expression "$compose $psql `"
SELECT url, size_bytes, analyzed, storage_path
FROM js_assets
WHERE scan_id = (SELECT scan_id FROM scans ORDER BY created_at DESC LIMIT 1)
ORDER BY size_bytes DESC;
`""

# ── Findings ──────────────────────────────────────────────────────────────────
Write-Host "`n[ FINDINGS ]" -ForegroundColor Yellow
Invoke-Expression "$compose $psql `"
SELECT severity, vulnerability_type, title, cvss_score, affected_url, source, is_verified
FROM findings
WHERE scan_id = (SELECT scan_id FROM scans ORDER BY created_at DESC LIMIT 1)
ORDER BY cvss_score DESC NULLS LAST;
`""

# ── Finding count by severity ─────────────────────────────────────────────────
Write-Host "`n[ FINDINGS BY SEVERITY ]" -ForegroundColor Yellow
Invoke-Expression "$compose $psql `"
SELECT severity, COUNT(*) as count
FROM findings
WHERE scan_id = (SELECT scan_id FROM scans ORDER BY created_at DESC LIMIT 1)
GROUP BY severity
ORDER BY count DESC;
`""

# ── Live worker logs ──────────────────────────────────────────────────────────
Write-Host "`n[ LIVE WORKER LOGS (last 15 lines) ]" -ForegroundColor Yellow
Invoke-Expression "$compose logs core-worker --tail 15"

Write-Host "`n========================================`n" -ForegroundColor Cyan