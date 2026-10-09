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
    "scope": "playlist-modify-private",
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
async def test_exchange_code_returns_tokens():
    respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    async with httpx.AsyncClient() as http:
        tokens = await spotify.exchange_code(http, "fake-code")

    assert tokens.access_token == "fake-access"
    assert tokens.refresh_token == "fake-refresh"
    assert tokens.expires_in == 3600


@respx.mock
async def test_exchange_code_raises_on_error():
    respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            400,
            json={"error": "invalid_grant"}
        )
    )

    with pytest.raises(spotify.SpotifyAPIError):
        async with httpx.AsyncClient() as http:
            await spotify.exchange_code(http, "bad-code")


@respx.mock
async def test_exchange_code_sends_correct_body():
    route = respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    async with httpx.AsyncClient() as http:
        await spotify.exchange_code(http, "fake-code")

    body = parse_qs(route.calls.last.request.content.decode())
    assert body["grant_type"] == ["authorization_code"]
    assert body["code"] == ["fake-code"]
    assert body["redirect_uri"] == [settings.spotify_redirect_uri]


@respx.mock
async def test_exchange_code_sends_basic_auth():
    route = respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    async with httpx.AsyncClient() as http:
        await spotify.exchange_code(http, "fake-code")

    header = route.calls.last.request.headers["authorization"]
    assert header.startswith("Basic ")
    decoded = b64decode(header.removeprefix("Basic ")).decode()
    assert decoded == f"{settings.spotify_client_id}:{settings.spotify_client_secret}"


# refresh_access_token tests

@respx.mock
async def test_refresh_access_token_sends_correct_body():
    route = respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=TOKEN_JSON
        )
    )

    async with httpx.AsyncClient() as http:
        await spotify.refresh_access_token(http, "old-refresh")

    body = parse_qs(route.calls.last.request.content.decode())
    assert body["grant_type"] == ["refresh_token"]
    assert body["refresh_token"] == ["old-refresh"]


@respx.mock
async def test_refresh_access_token_keeps_old_refresh_token_when_omitted():
    token_json = {k: v for k, v in TOKEN_JSON.items() if k != "refresh_token"}
    respx.post(spotify.TOKEN_URL).mock(
        return_value=Response(
            200,
            json=token_json
        )
    )

    async with httpx.AsyncClient() as http:
        tokens = await spotify.refresh_access_token(http, "old-refresh")

    assert tokens.access_token == "fake-access"
    assert tokens.refresh_token == "old-refresh"
