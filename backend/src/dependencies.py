import httpx
from fastapi import HTTPException, Request

from src.services import token_store


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


async def get_access_token(request: Request) -> str:
    session_id = request.session.get("session_id")
    tokens = token_store.get(session_id)
    if tokens is None:
        request.session.pop("session_id", None)
        raise HTTPException(status_code=401, detail="not logged in")
    
    return tokens.access_token
