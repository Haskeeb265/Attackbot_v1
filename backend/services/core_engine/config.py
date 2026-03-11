from backend.shared.config import BaseServiceConfig


class EngineConfig(BaseServiceConfig):
    service_name: str = "core-engine"
    port: int = 8002

    # Scraper API — used to fetch program scope
    scraper_api_url: str = "http://scraper:8001"
    scraper_api_timeout_seconds: int = 30

    # Subprocess timeouts (seconds)
    subfinder_timeout: int = 1800   # 30 min — large programs have many subdomains
    dnsx_timeout: int = 900
    httpx_timeout: int = 600
    ffuf_timeout: int = 1800
    nuclei_timeout: int = 3600      # 1 hour
    waybackurls_timeout: int = 300

    # Nuclei settings
    nuclei_rate_limit: int = 150    # requests/sec
    nuclei_bulk_size: int = 25
    nuclei_concurrency: int = 25
    nuclei_templates: str = ""      # empty = default template set

    # ffuf settings
    ffuf_wordlist: str = "/wordlists/common.txt"
    ffuf_rate: int = 100
    ffuf_threads: int = 40

    # JS scanning
    js_download_timeout_seconds: int = 30
    js_max_file_size_bytes: int = 5_242_880   # 5 MB

    # Redis lock TTL
    scan_lock_ttl_seconds: int = 14400        # 4 hours

    # Watchdog
    watchdog_interval_seconds: int = 300      # 5 min check
    watchdog_stale_threshold_hours: int = 2

    # Feature flags defaults (can be overridden per scan via message)
    default_sqli_enabled: bool = False
    default_ssrf_enabled: bool = False
    default_crlf_enabled: bool = False