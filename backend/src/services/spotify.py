import httpx
from urllib.parse import urlencode

from src.config import settings
from src.schemas import TokenResponse, SpotifyUser


AUTHORIZE_URL = "https://accounts.spotify.com/authorize?"
TOKEN_URL = "https://accounts.spotify.com/api/token"
V1_URL = "https://api.spotify.com/v1"


class SpotifyAPIError(Exception):
    def __init__(self, operation: str, status_code: int, body: str):
        self.operation = operation
        self.status_code = status_code
        self.body = body
        super().__init__(f"{operation} failed: {status_code} {body}")


def build_login_authorize_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.spotify_client_id,
        "scope": settings.spotify_scopes,
        "redirect_uri": settings.spotify_redirect_uri,
        "state": state
    }

    return AUTHORIZE_URL + urlencode(params)


async def exchange_code(client: httpx.AsyncClient, code: str) -> TokenResponse:
    form = {
        "code": code,
        "redirect_uri": settings.spotify_redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        response = await client.post(
            url=TOKEN_URL,
            data=form,
            auth=(settings.spotify_client_id, settings.spotify_client_secret)
        )
    except httpx.RequestError as e:
        raise SpotifyAPIError("token exchange", 503, repr(e)) from e
        
    if response.status_code != 200:
        raise SpotifyAPIError("token exchange", response.status_code, response.text)
    
    return TokenResponse.model_validate(response.json())


async def get_current_user(client: httpx.AsyncClient, access_token: str) -> SpotifyUser:
    headers = {
        "Authorization": f"Bearer {access_token}" 
    }
    
    try:
        response = await client.get(
            url=V1_URL + "/me",
            headers=headers,
        )
    except httpx.RequestError as e:
        raise SpotifyAPIError("get current user", 503, repr(e)) from e

    if response.status_code != 200:
        raise SpotifyAPIError("get current user", response.status_code, response.text)
    
    return SpotifyUser.model_validate(response.json())
