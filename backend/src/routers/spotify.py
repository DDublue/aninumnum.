from fastapi import APIRouter, Depends, HTTPException
from httpx import AsyncClient

from src.dependencies import get_access_token, get_http_client
from src.schemas import SpotifyUser
from src.services import spotify


router = APIRouter(prefix="/spotify", tags=["spotify"])


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
