from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env")

    session_secret_key: str
    spotify_client_id: str
    spotify_client_secret: str

    spotify_redirect_uri: str
    spotify_scopes: str = "playlist-modify-private playlist-modify-public"

    session_ttl_seconds: int = 14 * 24 * 3600
    token_encryption_key: str

    frontend_url: str = "http://127.0.0.1:5173"
    cors_origins: list[str] = ["http://127.0.0.1:5173"]
    session_https_only: bool = True

    database_url: str = f"sqlite:///{BACKEND_DIR / "aninumnum.db"}"


settings = Settings()  # pyright: ignore[reportCallIssue]
