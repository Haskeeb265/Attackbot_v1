"""
Scraper service configuration.

Extends BaseServiceConfig with HackerOne credentials,
schedule intervals, and reconciler settings.
All values can be overridden via environment variables or .env file.
"""

from backend.shared.config import BaseServiceConfig


class ScraperConfig(BaseServiceConfig):
    service_name: str = "scraper"
    port: int = 8001

    # HackerOne credentials — loaded from .env or Vault
    # Generated from HackerOne Settings > API Tokens
    hackerone_api_username: str = ""
    hackerone_api_token: str = ""

    # Per-platform scrape intervals (seconds)
    hackerone_scrape_interval_seconds: int = 21600   # 6 hours

    # Collector settings
    collector_max_retries: int = 3
    collector_page_size: int = 100

    # Reconciler — republishes programs with queued_for_scan=True
    reconciler_interval_seconds: int = 300           # 5 minutes
    reconciler_max_age_days: int = 7

    # Background scan publish scheduler (decoupled from metadata sync)
    scraper_scan_publish_interval_minutes: int = 60
    scraper_scan_publish_batch_size: int = 10
    e2e_pause_reconciler: bool = False

    # Redis distributed lock TTL to prevent concurrent scrapes of same platform
    platform_lock_ttl_seconds: int = 7200            # 2 hours
