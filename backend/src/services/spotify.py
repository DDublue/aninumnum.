import httpx
from urllib.parse import urlencode

from src.config import settings


AUTHORIZE_URL = "https://accounts.spotify.com/authorize?"
TOKEN_URL = "https://accounts.spotify.com/api/token"
V1_URL = "https://api.spotify.com/v1"


def build_login_authorize_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.spotify_client_id,
        "scope": settings.spotify_scopes,
        "redirect_uri": settings.spotify_redirect_uri,
        "state": state
    }

    return AUTHORIZE_URL + urlencode(params)
