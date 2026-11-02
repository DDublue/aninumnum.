import asyncio
import secrets
import time
from cryptography.fernet import InvalidToken
from dataclasses import dataclass
from sqlalchemy import delete as sql_delete, select
from sqlalchemy.orm import Session

from src.config import settings
from src.db import SessionLocal
from src.models import StoredSession
from src.schemas import TokenResponse


_locks: dict[str, asyncio.Lock] = {}


def lock(session_id: str) -> asyncio.Lock:
    return _locks.setdefault(session_id, asyncio.Lock())


# helper functions

def _purge_stale(db: Session) -> None:
    cutoff = _now() - settings.session_ttl_seconds
    stale = db.scalars(
        select(StoredSession.session_id)
            .where(StoredSession.last_used_at < cutoff)
    ).all()
    if not stale:
        return
    
    db.execute(
        sql_delete(StoredSession)
            .where(StoredSession.session_id.in_(stale))
    )
    for session_id in stale:
        _locks.pop(session_id, None)



@dataclass(frozen=True)
class StoredTokens:
    access_token: str
    refresh_token: str | None
    expires_at: int
    
    def is_expired(self, buffer: int = 0) -> bool:
        return _now() >= self.expires_at - buffer


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
        _purge_stale(db)
        db.add(
            StoredSession(
                session_id=session_id,
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                expires_at=current_time + tokens.expires_in,
                created_at=current_time,
                last_used_at=current_time,
            )
        )
        db.commit()
    
    return session_id


def get(session_id: str | None) -> StoredTokens | None:
    if not session_id:
        return None
    
    with SessionLocal() as db:
        try:
            row = db.get(StoredSession, session_id)
        except InvalidToken:
            # encrypted with a different key, so this login can't be used
            db.execute(sql_delete(StoredSession).where(StoredSession.session_id == session_id))
            db.commit()
            return None

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
    if not session_id:
        return None
    
    _locks.pop(session_id, None)
    with SessionLocal() as db:
        db.execute(
            sql_delete(StoredSession)
                .where(StoredSession.session_id == session_id)
        )
        db.commit()
