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


def test_is_expired_respects_buffer(monkeypatch):
    monkeypatch.setattr(token_store, "_now", lambda: 1000)
    tokens = token_store.StoredTokens("a", "r", expires_at=1050)
    
    assert not tokens.is_expired()
    assert tokens.is_expired(buffer=60)


# saving tokens tests
def test_save_then_get_returns_tokens():
    session_id = token_store.save(make_tokens())
    stored = token_store.get(session_id)

    assert isinstance(stored, token_store.StoredTokens)
    assert stored.access_token == "access"
    assert stored.refresh_token == "refresh"
    

def test_save_returns_unique_session_ids():
    session_id_a = token_store.save(make_tokens())
    session_id_b = token_store.save(make_tokens())
    
    assert isinstance(session_id_a, str)
    assert isinstance(session_id_b, str)
    assert session_id_a != session_id_b


def test_save_sets_expiry_from_expires_in(monkeypatch):
    monkeypatch.setattr(token_store, "_now", lambda: 1000)
    
    session_id = token_store.save(make_tokens(expires_in=3600))
    stored = token_store.get(session_id)
    
    assert stored is not None
    assert stored.expires_at == 4600


# get tokens tests
def test_get_unknown_id_returns_none():
    assert token_store.get("does-not-exist") is None


def test_get_none_returns_none():
    assert token_store.get(None) is None


# update tokens tests
def test_update_changes_access_token_and_expires_at():
    session_id = token_store.save(make_tokens())
    old_tokens = token_store.get(session_id)

    token_store.update(session_id, make_tokens(access_token="brand_new_access"))
    new_tokens = token_store.get(session_id)
    
    assert old_tokens is not None
    assert new_tokens is not None
    assert new_tokens.access_token == "brand_new_access"
    assert old_tokens.access_token != new_tokens.access_token


def test_update_keeps_old_refresh_token():
    session_id = token_store.save(make_tokens())
    old_tokens = token_store.get(session_id)
    
    token_store.update(session_id, make_tokens())
    new_tokens = token_store.get(session_id)

    assert old_tokens is not None
    assert new_tokens is not None
    assert old_tokens.refresh_token == new_tokens.refresh_token
    

def test_update_replaces_old_refresh_token_with_new():
    session_id = token_store.save(make_tokens())
    old_tokens = token_store.get(session_id)
    
    token_store.update(session_id, make_tokens(refresh_token="brand_new_refresh"))
    new_tokens = token_store.get(session_id)

    assert old_tokens is not None
    assert new_tokens is not None
    assert new_tokens.refresh_token == "brand_new_refresh"
    assert old_tokens.refresh_token != new_tokens.refresh_token


def test_update_unknown_id_changes_nothing():    
    token_store.update("does-not-exist", make_tokens())


# delete tokens tests
def test_delete_removes_tokens():
    session_id = token_store.save(make_tokens())

    token_store.delete(session_id)

    assert token_store.get(session_id) is None


def test_delete_none_or_unknown_does_nothing():
    token_store.delete(None)
    token_store.delete("does-not-exist")
