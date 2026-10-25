from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class StoredSession(Base):
    __tablename__ = "session"
    
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    access_token: Mapped[str]
    refresh_token: Mapped[str | None]
    expires_at: Mapped[int]
    created_at: Mapped[int]
    last_used_at: Mapped[int]
