"""
AttackBot shared Vault integration.
Wraps hvac for KV v2 secret access.
"""
import hvac
from shared.logging import get_logger

log = get_logger(__name__)

_client: hvac.Client | None = None


def init_vault(vault_url: str, vault_token: str) -> None:
    """Initialise the Vault client. Call once during service startup."""
    global _client
    _client = hvac.Client(url=vault_url, token=vault_token)
    try:
        if _client.is_authenticated():
            log.info("vault_connected", url=vault_url)
        else:
            log.warning("vault_not_authenticated", url=vault_url)
    except Exception as e:
        log.warning("vault_connect_warning", url=vault_url, error=str(e))


def get_secret(path: str, key: str) -> str:
    """
    Read a secret value from Vault KV v2.
    path: e.g. "attackbot/platform/hackerone"
    key:  e.g. "api_token"
    Raises KeyError if path or key not found.
    """
    if _client is None:
        raise RuntimeError("Vault not initialised. Call init_vault() first.")
    response = _client.secrets.kv.v2.read_secret_version(path=path)
    data = response["data"]["data"]
    if key not in data:
        raise KeyError(f"Key {key!r} not found at Vault path {path!r}")
    return data[key]


def put_secret(path: str, values: dict[str, str]) -> None:
    """Write secret values to Vault KV v2."""
    if _client is None:
        raise RuntimeError("Vault not initialised. Call init_vault() first.")
    _client.secrets.kv.v2.create_or_update_secret(path=path, secret=values)
    log.info("vault_secret_written", path=path)
