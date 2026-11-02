from typing import Any

from cryptography.fernet import Fernet
from sqlalchemy import Dialect, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from src.config import settings
from src.db import Base


_fernet = Fernet(settings.token_encryption_key)

class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True
    
    def process_bind_param(
        self,
        value: Any | None,
        dialect: Dialect
    ) -> Any | None:
        return None if value is None else _fernet.encrypt(value.encode()).decode()
    
    def process_result_value(
        self,
        value: Any | None,
        dialect: Dialect
    ) -> Any | None:
        return None if value is None else _fernet.decrypt(value.encode()).decode()


class StoredSession(Base):
    __tablename__ = "session"
    
    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    access_token: Mapped[str] = mapped_column(EncryptedString)
    refresh_token: Mapped[str | None] = mapped_column(EncryptedString)
    expires_at: Mapped[int]
    created_at: Mapped[int]
    last_used_at: Mapped[int]
