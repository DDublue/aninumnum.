import httpx
import pytest
from urllib.parse import parse_qs, urlparse

from src.config import settings
from src.schemas import TokenResponse
from src.services import spotify, token_store


def get_params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def get_error(url: str) -> str | None:
    return parse_qs(urlparse(url).fragment).get("error", [None])[0]


async def start_login(client) -> str:
    response = await client.get("/auth/login")
    return get_params(response.headers["location"])["state"][0]


@pytest.fixture
def fake_exchange(monkeypatch) -> list[str]:
    calls = []
    
    async def fake_exchange_code(client: httpx.AsyncClient, code: str) -> TokenResponse:
        calls.append(code)
        return TokenResponse(
            access_token="fake-access",
            token_type="Bearer",
            expires_in=3600,
            scope=settings.spotify_scopes,
            refresh_token="fake-refresh",
        )
        
    monkeypatch.setattr(spotify, "exchange_code", fake_exchange_code)
    return calls


def fail_exchange(monkeypatch, status_code: int):
    async def failing_exchange(client, code):
        raise spotify.SpotifyAPIError("token exchange", status_code, "boom")
    
    monkeypatch.setattr(spotify, "exchange_code", failing_exchange)

    
# auth login tests

async def test_login_redirects_to_spotify(client):
    response = await client.get("/auth/login")
    location = urlparse(response.headers["location"])
    
    assert response.status_code == 307
    assert location.netloc == "accounts.spotify.com"
    assert location.path == "/authorize"
    

# auth callback tests

async def test_callback_success_redirects_to_frontend(client, fake_exchange):
    state = await start_login(client)
    
    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": state}
    )
    
    assert response.status_code == 307
    assert response.headers["location"].startswith(settings.frontend_url)
    assert get_error(response.headers["location"]) is None
    assert fake_exchange == ["fake-code"]


async def test_callback_success_saves_tokens(client, fake_exchange):
    state = await start_login(client)
    
    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": state}
    )

    assert response.status_code == 307

    stored = list(token_store._tokens.values())
    assert len(stored) == 1
    assert stored[0].access_token == "fake-access"
    assert stored[0].refresh_token == "fake-refresh"
    assert "session" in client.cookies


async def test_callback_wrong_state_is_rejected(client, fake_exchange):
    await start_login(client)
    
    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": "wrong"}
    )
    
    assert response.status_code == 307
    assert get_error(response.headers["location"]) == "state_mismatch"
    assert fake_exchange == []
    assert token_store._tokens == {}


async def test_callback_without_login_is_rejected(client, fake_exchange):
    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": "anything"}
    )
    
    assert response.status_code == 307
    assert get_error(response.headers["location"]) == "state_mismatch"
    assert fake_exchange == []
    assert token_store._tokens == {}

    
async def test_callback_cancelled_redirects_to_frontend(client, fake_exchange):
    state = await start_login(client)

    response = await client.get(
        "/auth/callback",
        params={"error": "access_denied", "state": state}
    )

    assert response.status_code == 307
    assert response.headers["location"].startswith(settings.frontend_url)
    assert get_error(response.headers["location"]) == "access_denied"
    assert fake_exchange == []
    assert token_store._tokens == {}


async def test_callback_missing_code_is_rejected(client, fake_exchange):
    state = await start_login(client)

    response = await client.get(
        "/auth/callback",
        params={"state": state}
    )

    assert response.status_code == 307
    assert get_error(response.headers["location"]) == "missing_code"
    assert fake_exchange == []
    assert token_store._tokens == {}


async def test_callback_spotify_server_error_returns_502(client, monkeypatch):
    fail_exchange(monkeypatch, 503)
    state = await start_login(client)

    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": state}
    )

    assert response.status_code == 502
    assert token_store._tokens == {}
