from urllib.parse import parse_qs, urlparse

from src.config import settings
from src.services import spotify


def get_params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def test_spotify_login_authorize_endpoint():
    url = spotify.build_login_authorize_url("test-state")
    parsed_url = urlparse(url)
    
    assert parsed_url.scheme == "https"
    assert parsed_url.netloc == "accounts.spotify.com"
    assert parsed_url.path == "/authorize"


def test_spotify_login_params_all():
    url = spotify.build_login_authorize_url("test-state")
    params = get_params(url)
    
    assert params["client_id"] == settings.spotify_client_id
    assert params["redirect_uri"] == settings.spotify_redirect_uri
    assert params["scope"] == settings.spotify_scopes
    assert params["response_type"] == "code"
    assert params["state"] == "test-state"


def test_client_secret_not_in_url():
    url = spotify.build_login_authorize_url("test-state")
    
    assert settings.spotify_client_secret not in url
