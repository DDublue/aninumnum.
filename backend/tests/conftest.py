import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from src.services import token_store
from src.main import create_app
from src.dependencies import get_http_client


@pytest.fixture
def app():
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient() as http:
        app.dependency_overrides[get_http_client] = lambda: http
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture(scope="session", autouse=True)
def empty_token_store():
    token_store._tokens.clear()
    yield
    token_store._tokens.clear()
