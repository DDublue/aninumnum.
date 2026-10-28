import httpx
import pytest
import respx
from base64 import b64decode
from httpx import Response
from urllib.parse import parse_qs, urlparse

from src.config import settings
from src.services import spotify


TOKEN_JSON = {
    "access_token": "fake-access",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "playlist-modify-private playlist-modify-public",
    "refresh_token": "fake-refresh",
}


# Helper functions
def get_params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


# build_login_authorize_url tests
def test_spotify_login_authorize_endpoint():
    url = spotify.build_login_authorize_url("test-state")
    parsed_url = urlparse(url)

    assert parsed_url.scheme == "https"
    assert parsed_url.netloc == "accounts.spotify.com"
    assert parsed_url.path == "/authorize"


def test_spotify_login_params_all():
    url = spotify.build_login_authorize_url("test-state")
    params = get_params(url)

    assert params["client_id"] == [settings.spotify_client_id]
    assert params["redirect_uri"] == [settings.spotify_redirect_uri]
    assert params["scope"] == [settings.spotify_scopes]
    assert params["response_type"] == ["code"]
    assert params["state"] == ["test-state"]


def test_client_secret_not_in_url():
    url = spotify.build_login_authorize_url("test-state")

    assert settings.spotify_client_secret not in url


# exchange_code tests

@respx.mock
async def test_exchange_code_returns_tokens(http):
    respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    tokens = await spotify.exchange_code(http, "fake-code")

    assert tokens.access_token == "fake-access"
    assert tokens.refresh_token == "fake-refresh"
    assert tokens.expires_in == 3600


@respx.mock
async def test_exchange_code_raises_on_error(http):
    respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            400,
            json={"error": "invalid_grant"}
        )
    )

    with pytest.raises(spotify.SpotifyAPIError) as exc_info:
        await spotify.exchange_code(http, "bad-code")

    assert exc_info.value.status_code == 400


@respx.mock
async def test_exchange_code_sends_correct_body(http):
    route = respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    await spotify.exchange_code(http, "fake-code")

    body = parse_qs(route.calls.last.request.content.decode())
    assert body["grant_type"] == ["authorization_code"]
    assert body["code"] == ["fake-code"]
    assert body["redirect_uri"] == [settings.spotify_redirect_uri]


@respx.mock
async def test_exchange_code_sends_basic_auth(http):
    route = respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    await spotify.exchange_code(http, "fake-code")

    header = route.calls.last.request.headers["authorization"]
    assert header.startswith("Basic ")
    decoded = b64decode(header.removeprefix("Basic ")).decode()
    assert decoded == f"{settings.spotify_client_id}:{settings.spotify_client_secret}"


@respx.mock
async def test_exchange_code_network_error_is_503(http):
    respx.post(spotify.TOKEN_URL).mock(side_effect=httpx.ConnectError("down"))

    with pytest.raises(spotify.SpotifyAPIError) as exc_info:
        await spotify.exchange_code(http, "fake-code")

    assert exc_info.value.status_code == 503
    

# refresh_access_token tests

@respx.mock
async def test_refresh_access_token_sends_correct_body(http):
    route = respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    tokens = await spotify.refresh_access_token(http, "old-refresh")

    body = parse_qs(route.calls.last.request.content.decode())
    assert body["grant_type"] == ["refresh_token"]
    assert body["refresh_token"] == ["old-refresh"]


@respx.mock
async def test_refresh_access_token_uses_rotated_refresh_token(http):
    respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    tokens = await spotify.refresh_access_token(http, "old-refresh")

    assert tokens.refresh_token == "fake-refresh"


@respx.mock
async def test_refresh_access_token_keeps_old_refresh_token_when_omitted(http):
    token_json = {k: v for k, v in TOKEN_JSON.items() if k != "refresh_token"}
    respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=token_json
        )
    )

    tokens = await spotify.refresh_access_token(http, "old-refresh")

    assert tokens.access_token == "fake-access"
    assert tokens.refresh_token == "old-refresh"


@pytest.mark.parametrize("status", [400, 401, 429, 500, 503])
@respx.mock
async def test_refresh_access_token_raises_with_status(http, status):
    respx.post(spotify.TOKEN_URL).mock(return_value=Response(status, text="boom"))

    with pytest.raises(spotify.SpotifyAPIError) as exc_info:
        await spotify.refresh_access_token(http, "old-refresh")

    assert exc_info.value.status_code == status


# get_current_user tests

@respx.mock
async def test_get_current_user_sends_bearer_and_parses_user(http):
    user_json = {
        "account_id": "acc-1",
        "id": "user-1",
        "display_name": "fake-display-name",
    }

    route = respx.get(spotify.V1_URL + "/me").mock(
        return_value=Response(
            200,
            json=user_json
        )
    )

    user = await spotify.get_current_user(http, "fake-access")

    assert route.calls.last.request.headers["authorization"] == "Bearer fake-access"
    assert user.id == "user-1"
