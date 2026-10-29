from urllib.parse import urlparse
from sqlalchemy import select, update

from src.config import settings
from src.models import StoredSession
from src.schemas import SpotifyUser, TokenResponse
from src.services import spotify

from tests.utils import get_error, start_login, session_count, fake_exchange, fail_exchange


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


async def test_callback_success_saves_tokens(client, fake_exchange, db):
    state = await start_login(client)

    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": state}
    )

    assert response.status_code == 307

    stored = db.scalars(select(StoredSession)).all()
    assert len(stored) == 1
    assert stored[0].access_token == "fake-access"
    assert stored[0].refresh_token == "fake-refresh"
    assert "session" in client.cookies


async def test_callback_wrong_state_is_rejected(client, fake_exchange, db):
    await start_login(client)

    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": "wrong"}
    )

    assert response.status_code == 307
    assert get_error(response.headers["location"]) == "state_mismatch"
    assert fake_exchange == []
    assert session_count(db) == 0


async def test_callback_without_login_is_rejected(client, fake_exchange, db):
    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": "anything"}
    )

    assert response.status_code == 307
    assert get_error(response.headers["location"]) == "state_mismatch"
    assert fake_exchange == []
    assert session_count(db) == 0


async def test_callback_cancelled_redirects_to_frontend(client, fake_exchange, db):
    state = await start_login(client)

    response = await client.get(
        "/auth/callback",
        params={"error": "access_denied", "state": state}
    )

    assert response.status_code == 307
    assert response.headers["location"].startswith(settings.frontend_url)
    assert get_error(response.headers["location"]) == "access_denied"
    assert fake_exchange == []
    assert session_count(db) == 0


async def test_callback_missing_code_is_rejected(client, fake_exchange, db):
    state = await start_login(client)

    response = await client.get(
        "/auth/callback",
        params={"state": state}
    )

    assert response.status_code == 307
    assert get_error(response.headers["location"]) == "missing_code"
    assert fake_exchange == []
    assert session_count(db) == 0


async def test_callback_spotify_server_redirects_to_frontend(client, monkeypatch, db):
    fail_exchange(monkeypatch, 503)
    state = await start_login(client)

    response = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": state}
    )

    assert response.status_code == 307
    assert get_error(response.headers["location"]) == "spotify_unavailable"
    assert session_count(db) == 0


# token refresh tests

async def login_with_expired_token(client, db):
    state = await start_login(client)
    await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": state}
    )
    db.execute(update(StoredSession).values(expires_at=0))
    db.commit()


async def test_expired_token_is_refreshed_once(client, fake_exchange, monkeypatch, db):
    refreshes = []
    seen_tokens = []

    async def fake_refresh(http, refresh_token):
        refreshes.append(refresh_token)
        return TokenResponse(
            access_token="new-access",
            token_type="Bearer",
            expires_in=3600,
            scope=settings.spotify_scopes,
            refresh_token="fake-refresh",
        )

    async def fake_get_current_user(http, access_token):
        seen_tokens.append(access_token)
        return SpotifyUser.model_validate(
            {"account_id": "test-account-id", "id": "user-1"}
        )

    monkeypatch.setattr(spotify, "refresh_access_token", fake_refresh)
    monkeypatch.setattr(spotify, "get_current_user", fake_get_current_user)

    await login_with_expired_token(client, db)
    await client.get("/spotify/me")
    await client.get("/spotify/me")

    assert refreshes == ["fake-refresh"]
    assert seen_tokens == ["new-access", "new-access"]


async def test_rejected_refresh_logs_out(client, fake_exchange, monkeypatch, db):
    async def failing_refresh(http, refresh_token):
        raise spotify.SpotifyAPIError(
            "refresh access token", 400, "invalid_grant")

    monkeypatch.setattr(spotify, "refresh_access_token", failing_refresh)

    await login_with_expired_token(client, db)
    response = await client.get("/spotify/me")

    assert response.status_code == 401
    assert session_count(db) == 0


# auth logout test

async def test_logout_ends_session(client, fake_exchange, db):
    state = await start_login(client)
    await client.get("/auth/callback", params={"code": "fake-code", "state": state})

    response = await client.post("/auth/logout")

    assert response.status_code == 200
    assert session_count(db) == 0
    assert (await client.get("/spotify/me")).status_code == 401
