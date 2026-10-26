from collections.abc import Iterator

import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from src.db import SessionLocal, engine, Base
from src.dependencies import get_http_client
from src.main import create_app


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
def db_schema() -> Iterator[None]:
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def clean_db() -> None:
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
