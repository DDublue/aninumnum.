import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from urllib.parse import urlencode

from src.config import settings
from src.dependencies import get_access_token, get_http_client
from src.schemas import SpotifyUser
from src.services import spotify, token_store
from src.utils import frontend_direct


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(
    request: Request,
):
    state = secrets.token_urlsafe() # 32 bytes default
    request.session["oauth_state"] = state
    return RedirectResponse(spotify.build_login_authorize_url(state))


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    http: AsyncClient = Depends(get_http_client),
):
    stored_state = request.session.pop("oauth_state", None)
    if state is None or stored_state is None or not secrets.compare_digest(stored_state, state):
        return frontend_direct(error="state_mismatch")
    
    if error or not code:
        return frontend_direct(error=error or "missing_code")
    
    try:
        tokens = await spotify.exchange_code(http, code)
        request.session["session_id"] = token_store.save(tokens)
    except spotify.SpotifyAPIError as e:
        if e.status_code >= 500:
            raise HTTPException(status_code=502, detail="Spotify is unavailable")
        return frontend_direct(error="token_exchange_failed")
    
    return frontend_direct()


@router.get("/me")
async def me(
    http: AsyncClient = Depends(get_http_client),
    access_token: str = Depends(get_access_token),
) -> SpotifyUser:
    try:
        return await spotify.get_current_user(http, access_token)
    except spotify.SpotifyAPIError as e:
        if e.status_code == 401:
            raise HTTPException(status_code=401, detail="session expired")
        raise HTTPException(status_code=502, detail="Spotify request failed")


@router.post("/logout")
async def logout(
    request: Request,
):
    session_id = request.session.get("session_id")
    token_store.delete(session_id)
    request.session.clear()
    
    return {"status": "logged out"}
    
