from fastapi import APIRouter, Depends, HTTPException, Request
from httpx import AsyncClient

from src.dependencies import get_access_token, get_http_client
from src.schemas import SpotifyUser
from src.services import spotify as spotify_service, token_store


router = APIRouter(prefix="/spotify", tags=["spotify"])


@router.get("/me")
async def me(
    request: Request,
    http: AsyncClient = Depends(get_http_client),
    access_token: str = Depends(get_access_token),
) -> SpotifyUser:
    try:
        return await spotify_service.get_current_user(http, access_token)
    except spotify_service.SpotifyAPIError as e:
        if e.status_code == 401:
            token_store.delete(request.session.pop("session_id", None))
            raise HTTPException(status_code=401, detail="session expired")
        raise HTTPException(status_code=502, detail="Spotify request failed")
