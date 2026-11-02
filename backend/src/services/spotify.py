import httpx
from pydantic import BaseModel, ValidationError
from urllib.parse import urlencode

from src.config import settings
from src.schemas import TokenResponse, SpotifyUser


AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
V1_URL = "https://api.spotify.com/v1"


class SpotifyAPIError(Exception):
    def __init__(self, operation: str, status_code: int, body: str):
        self.operation = operation
        self.status_code = status_code
        self.body = body
        super().__init__(f"{operation} failed: {status_code} {body[:500]}")


# helper functions
def _json_or_raise(
    response: httpx.Response,
    operation: str
) -> dict:
    if response.status_code != 200:
        raise SpotifyAPIError(operation, response.status_code, response.text)
    
    try:
        data = response.json()
    except ValueError as e:
        raise SpotifyAPIError(operation, 502, "response was not JSON") from e
    
    if not isinstance(data, dict):
        raise SpotifyAPIError(operation, 502, "response was not a JSON object")
    
    return data


def _parse[T: BaseModel](
    model: type[T],
    data: dict,
    operation: str
) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as e:
        details = e.errors(include_input=False, include_url=False)
        raise SpotifyAPIError(operation, 502, str(details)) from e


async def _token_request(
    client: httpx.AsyncClient,
    form: dict,
    operation: str
) -> dict:
    try:
        response = await client.post(
            url=TOKEN_URL,
            data=form,
            auth=(settings.spotify_client_id, settings.spotify_client_secret)
        )
    except httpx.RequestError as e:
        raise SpotifyAPIError(operation, 503, repr(e)) from e
    
    return _json_or_raise(response, operation)


async def _api_get(
    client: httpx.AsyncClient,
    path: str,
    access_token: str,
    operation: str
) -> dict:
    try:
        response = await client.get(
            url=f"{V1_URL}{path}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    except httpx.RequestError as e:
        raise SpotifyAPIError(operation, 503, repr(e)) from e
    
    return _json_or_raise(response, operation)


# spotify services


def build_login_authorize_url(
    state: str,
    show_dialog: bool = False
) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.spotify_client_id,
        "scope": settings.spotify_scopes,
        "redirect_uri": settings.spotify_redirect_uri,
        "state": state,
        "show_dialog": str(show_dialog).lower(),
    }

    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(
    client: httpx.AsyncClient,
    code: str
) -> TokenResponse:
    operation = "token exchange"
    data = await _token_request(
        client,
        {
            "code": code,
            "redirect_uri": settings.spotify_redirect_uri,
            "grant_type": "authorization_code"
        },
        operation
    )

    return _parse(TokenResponse, data, operation)


async def get_current_user(
    client: httpx.AsyncClient,
    access_token: str
) -> SpotifyUser:
    operation = "get current user"
    data = await _api_get(client, "/me", access_token, operation)
    
    return _parse(SpotifyUser, data, operation)


async def refresh_access_token(
    client: httpx.AsyncClient,
    refresh_token: str
) -> TokenResponse:
    operation = "refresh access token"
    data = await _token_request(
        client,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        },
        operation
    )
    data.setdefault("refresh_token", refresh_token)

    return _parse(TokenResponse, data, operation)
