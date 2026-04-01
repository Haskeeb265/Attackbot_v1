# tests/conftest.py
import pytest


@pytest.fixture(autouse=True)
def reset_shared_state():
    """
    Reset module-level singletons in shared library between tests.
    Prevents state leakage across test cases.
    """
    import backend.shared.db as db_module
    import backend.shared.storage as storage_module
    import backend.shared.vault as vault_module

    # Reset before test
    db_module._engine = None
    db_module._session_factory = None
    storage_module._client = None
    vault_module._client = None

    yield

    # Reset after test
    db_module._engine = None
    db_module._session_factory = None
    storage_module._client = None
    vault_module._client = None