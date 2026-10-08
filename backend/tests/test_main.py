from src.config import settings

async def test_health(client):
    response = await client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unknown_route(client):
    response = await client.get("/unknown-route-please-do-not-use")

    assert response.status_code == 404


async def test_cors_allows_frontend(client):
    response = await client.options(
        "/health",
        headers={
            "Origin": settings.cors_origins[0],
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers["access-control-allow-origin"] == settings.cors_origins[0]
    assert response.headers["access-control-allow-credentials"] == "true"
    
    
async def test_cors_rejects_unknown_origin(client):
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://not.allowed.origin.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    
    assert "access-control-allow-origin" not in response.headers
