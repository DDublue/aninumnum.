import httpx
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from src.config import settings
from src.db import Base, engine
from src.routers import auth, spotify
from src.services import spotify as spotify_service, token_store


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.http = httpx.AsyncClient(timeout=10)
        Base.metadata.create_all(engine)
        yield
        await app.state.http.aclose()

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        same_site="lax",
        https_only=settings.session_https_only,
        max_age=settings.session_ttl_seconds,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(spotify.router)

    @app.exception_handler(spotify_service.SpotifyAPIError)
    async def spotify_error(
        request: Request,
        e: spotify_service.SpotifyAPIError
    ) -> JSONResponse:
        logger.warning("%s", e)
        if e.status_code == 401:
            token_store.delete(request.session.pop("session_id", None))
            return JSONResponse({"detail": "session expired"}, status_code=401)
        if e.status_code == 429:
            return JSONResponse({"detail": "rate limited"}, status_code=503)
        return JSONResponse({"detail": "Spotify request failed"}, status_code=502)

    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
