import secrets
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from src.config import settings
from src.services import spotify


router = APIRouter(prefix="/auth", tags=["auth"])

@router.get('/login')
async def login(request: Request):
    state = secrets.token_urlsafe()
    request.session["oauth_state"] = state
    return RedirectResponse(spotify.build_login_authorize_url(state))

@router.get('/callback')
async def callback(request: Request):
    pass
