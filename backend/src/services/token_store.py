import secrets
import time
from dataclasses import dataclass

from src.schemas import TokenResponse


@dataclass
class StoredTokens:
    access_token: str
    refresh_token: str | None
    expires_at: float


_tokens: dict[str, StoredTokens] = {}


def save(tokens: TokenResponse) -> str:
    session_id = secrets.token_urlsafe()
    update(session_id, tokens)
    return session_id


def update(session_id: str, tokens: TokenResponse) -> None:
    _tokens[session_id] = StoredTokens(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_at=time.time() + tokens.expires_in,
    )


def get(session_id: str | None) -> StoredTokens | None:
    return _tokens.get(session_id) if session_id else None


def delete(session_id: str | None) -> None:
    if session_id:
        _tokens.pop(session_id, None)

