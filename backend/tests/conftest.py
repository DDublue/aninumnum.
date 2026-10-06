import httpx
import os
import pytest_asyncio

os.environ["SPOTIFY_CLIENT_ID"] = "test-client-id"
os.environ["SPOTIFY_CLIENT_SECRET"] = "test-client-secret"
os.environ["SESSION_SECRET_KEY"] = "test-session-secret"
os.environ["SPOTIFY_REDIRECT_URI"] = "http://127.0.0.1:8000/auth/callback"

from src.dependencies import get_http_client
from src.main import app


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient() as http:
        app.dependency_overrides[get_http_client] = lambda: http
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()
