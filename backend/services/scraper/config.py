"""
AttackBot scraper service configuration.
Extends BaseServiceConfig with scraper-specific fields.
"""
from pydantic import Field
from shared.config import BaseServiceConfig


class ScraperConfig(BaseServiceConfig):
    service_name: str = "scraper"

    # ── HackerOne credentials ──────────────────────────────────────
    # These are dev fallbacks. In production, credentials come from Vault.
    hackerone_api_username: str = ""
    hackerone_api_token:    str = ""
    hackerone_scrape_interval_minutes: int = Field(default=60)

    # ── Scraper behaviour ──────────────────────────────────────────
    scrape_page_size:            int = 100
    max_scrape_retries:          int = 3
    reconciler_interval_minutes: int = 5
    reconciler_stale_days:       int = 7
