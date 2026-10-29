import httpx
import pytest
from urllib.parse import parse_qs, urlparse
from sqlalchemy import func, select

from src.config import settings
from src.models import StoredSession
from src.schemas import TokenResponse
from src.services import spotify



# helper functions

def get_params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def get_error(url: str) -> str | None:
    return parse_qs(urlparse(url).fragment).get("error", [None])[0]


async def start_login(client) -> str:
    response = await client.get("/auth/login")
    return get_params(response.headers["location"])["state"][0]


def session_count(db) -> int:
    return db.scalar(select(func.count()).select_from(StoredSession)) or 0


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
