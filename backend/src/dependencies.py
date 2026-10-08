import httpx
import time
from fastapi import Depends, HTTPException, Request

from src.services import spotify, token_store


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
    
    if int(time.time()) < tokens.expires_at - EXPIRY_BUFFER_SECONDS:
        return tokens.access_token
    
    if tokens.refresh_token is None:
        raise HTTPException(status_code=401, detail="login expired")
    
    try:
        new = await spotify.refresh_access_token(http, tokens.refresh_token)
    except spotify.SpotifyAPIError as e:
        if 400 <= e.status_code < 500:
            token_store.delete(session_id)
            request.session.pop("session_id", None)
            raise HTTPException(status_code=401, detail="login expired")
        raise HTTPException(status_code=502, detail="spotify is unavailable")
            
    token_store.update(session_id, new)
    return new.access_token
