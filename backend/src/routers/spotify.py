from fastapi import APIRouter, Depends
from httpx import AsyncClient

from src.dependencies import get_access_token, get_http_client
from src.schemas import SpotifyUser
from src.services import spotify as spotify_service


router = APIRouter(prefix="/spotify", tags=["spotify"])


@router.get("/me")
async def me(
    http: AsyncClient = Depends(get_http_client),
    access_token: str = Depends(get_access_token),
) -> SpotifyUser:
    return await spotify_service.get_current_user(http, access_token)
