from src.schemas import SpotifyUser
from src.services import spotify

from tests.utils import start_login, fake_exchange


# auth me tests

async def test_me_after_login_returns_user(client, fake_exchange, monkeypatch):
    async def fake_get_current_user(http, access_token):
        assert access_token == "fake-access"
        return SpotifyUser.model_validate(
            {
                "account_id": "test-account-id",
                "id": "user-1",
                "display_name": "Test User",
            }
        )

    monkeypatch.setattr(spotify, "get_current_user", fake_get_current_user)

    state = await start_login(client)
    callback = await client.get(
        "/auth/callback",
        params={"code": "fake-code", "state": state}
    )

    assert callback.status_code == 307

    response = await client.get("/spotify/me")
    data = response.json()

    assert response.status_code == 200
    assert data["account_id"] == "test-account-id"
    assert data["id"] == "user-1"
    assert data["display_name"] == "Test User"


async def test_me_without_login_returns_401(client):
    response = await client.get("/spotify/me")

    assert response.status_code == 401

