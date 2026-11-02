import logging
import secrets
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from httpx import AsyncClient

from src.dependencies import get_http_client
from src.services import spotify, token_store
from src.utils import frontend_redirect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(
    request: Request,
    switch: bool = False
) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    return RedirectResponse(spotify.build_login_authorize_url(state, show_dialog=switch))


@router.get("/callback")
async def callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    http: AsyncClient = Depends(get_http_client),
) -> RedirectResponse:
    stored_state = request.session.pop("oauth_state", None)
    if state is None or stored_state is None or not secrets.compare_digest(
        stored_state.encode(), state.encode()
    ):
        return frontend_redirect(error="state_mismatch")

    if error:
        if error != "access_denied":
            logger.warning("spotify authorization error: %s", error)
            error = "authorization_failed"
        return frontend_redirect(error=error)
        
    if not code:
        return frontend_redirect(error="missing_code")

    try:
        tokens = await spotify.exchange_code(http, code)
    except spotify.SpotifyAPIError as e:
        logger.warning("%s", e)
        if e.status_code >= 500 or e.status_code == 429:
            return frontend_redirect(error="spotify_unavailable")
        return frontend_redirect(error="token_exchange_failed")

    token_store.delete(request.session.get("session_id"))
    request.session["session_id"] = token_store.save(tokens)
    return frontend_redirect()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
) -> None:
    token_store.delete(request.session.get("session_id"))
    request.session.clear()
