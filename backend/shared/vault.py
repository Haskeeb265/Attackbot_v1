# backend/shared/vault.py
import hvac

from backend.shared.logging import get_logger

log = get_logger(__name__)

_client: hvac.Client | None = None


def init_vault(vault_url: str, vault_token: str) -> None:
    """
    Initialize the Vault client. Call once at service startup.
    Raises RuntimeError if authentication fails.
    """
    global _client
    _client = hvac.Client(url=vault_url, token=vault_token)
    if not _client.is_authenticated():
        raise RuntimeError(f"Vault authentication failed. URL: {vault_url}")
    log.info("vault_connected", url=vault_url)


def get_secret(path: str, key: str) -> str:
    """
    Read a single key from a KV v2 secret path.

    Args:
        path: Vault KV path (e.g. "attackbot/platform/hackerone")
        key:  Key within the secret (e.g. "api_token")

    Returns:
        The secret value as a string.
    """
    if _client is None:
        raise RuntimeError("Vault not initialized. Call init_vault() first.")
    response = _client.secrets.kv.read_secret_version(path=path)
    return str(response["data"]["data"][key])


def put_secret(path: str, data: dict[str, str]) -> None:
    """
    Write a set of key-value pairs to a KV v2 path.
    Creates or overwrites the secret at the given path.
    """
    if _client is None:
        raise RuntimeError("Vault not initialized. Call init_vault() first.")
    _client.secrets.kv.create_or_update_secret(path=path, secret=data)
    log.info("vault_secret_written", path=path)