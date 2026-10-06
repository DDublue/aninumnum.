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
    _tokens[session_id] = StoredTokens(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_at=time.time() + tokens.expires_in,
    )
    return session_id


def get(session_id: str | None) -> StoredTokens | None:
    return _tokens[session_id] if session_id else None


def delete(session_id: str | None) -> None:
    if session_id:
        _tokens.pop(session_id, None)

