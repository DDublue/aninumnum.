import httpx
import logging
from fastapi import Depends, HTTPException, Request

from src.services import spotify, token_store


logger = logging.getLogger(__name__)

EXPIRY_BUFFER_SECONDS = 60


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


async def get_access_token(
    request: Request,
    http: httpx.AsyncClient = Depends(get_http_client)
) -> str:
    session_id = request.session.get("session_id")
    tokens = token_store.get(session_id)
    if session_id is None or tokens is None:
        request.session.pop("session_id", None)
        raise HTTPException(status_code=401, detail="not logged in")

    if not tokens.is_expired(buffer=EXPIRY_BUFFER_SECONDS):
        return tokens.access_token

    async with token_store.lock(session_id):
        tokens = token_store.get(session_id)
        if tokens is None:
            request.session.pop("session_id", None)
            raise HTTPException(status_code=401, detail="login expired")
        if not tokens.is_expired(buffer=EXPIRY_BUFFER_SECONDS):
            return tokens.access_token
        
        if tokens.refresh_token is None:
            token_store.delete(session_id)
            request.session.pop("session_id", None)
            raise HTTPException(status_code=401, detail="login expired")

        try:
            new = await spotify.refresh_access_token(http, tokens.refresh_token)
        except spotify.SpotifyAPIError as e:
            logger.warning("%s", e)
            if e.status_code == 400 and "invalid_grant" in e.body:
                token_store.delete(session_id)
                request.session.pop("session_id", None)
                raise HTTPException(status_code=401, detail="login expired")
            if e.status_code == 429:
                raise HTTPException(status_code=503, detail="spotify rate limit")
            raise HTTPException(status_code=502, detail="spotify is unavailable")

        token_store.update(session_id, new)
    return new.access_token
