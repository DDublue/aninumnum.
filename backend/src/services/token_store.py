import secrets
import time
from dataclasses import dataclass

from src.db import SessionLocal
from src.models import StoredSession
from src.schemas import TokenResponse


@dataclass(frozen=True)
class StoredTokens:
    access_token: str
    refresh_token: str | None
    expires_at: int
    
    def is_expired(self, buffer: int = 0) -> bool:
        return time.time() >= self.expires_at - buffer


def _now() -> int:
    return int(time.time())


def _to_stored(row: StoredSession) -> StoredTokens:
    return StoredTokens(
        access_token=row.access_token,
        refresh_token=row.refresh_token,
        expires_at=row.expires_at,
    )


def save(tokens: TokenResponse) -> str:
    session_id = secrets.token_urlsafe(32)
    current_time = _now()
    
    with SessionLocal() as db:
        db.add(
            StoredSession(
                session_id=session_id,
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                expires_at=current_time,
                created_at=current_time,
                last_used_at=current_time,
            )
        )
        db.commit()
    
    return session_id


def get(session_id: str | None) -> StoredTokens | None:
    with SessionLocal() as db:
        row = db.get(StoredSession, session_id)
        if row is None:
            return None
        
        row.last_used_at = _now()
        db.commit()
        return _to_stored(row)


def update(session_id: str, new: TokenResponse) -> None:
    with SessionLocal() as db:
        row = db.get(StoredSession, session_id)
        if row is None:
            return
        
    row.access_token = new.access_token
    row.expires_at = _now() + new.expires_in
    if new.refresh_token:
        row.refresh_token = new.refresh_token
    row.last_used_at = _now()
    db.commit()


def delete(session_id: str | None) -> None:
    with SessionLocal() as db:
        row = db.get(StoredSession, session_id)
        if row is not None:
            db.delete(row)
            db.commit()
