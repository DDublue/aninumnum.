import time

from src.schemas import TokenResponse
from src.services import token_store


def make_tokens(**overrides) -> TokenResponse:
    data = {
        "access_token": "access",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "",
        "refresh_token": "refresh",
    }
    return TokenResponse(**(data | overrides))


async def test_save_then_get_returns_tokens():
    session_id = token_store.save(make_tokens())
    stored = token_store.get(session_id)
    
    assert stored is not None
    assert stored.access_token == "access"
    assert stored.refresh_token == "refresh"


async def test_get_unknown_id_returns_none():
    assert token_store.get("does-not-exist") is None


async def test_delete_removes_tokens():
    session_id = token_store.save(make_tokens())
    
    token_store.delete(session_id)
    
    assert token_store.get(session_id) is None

