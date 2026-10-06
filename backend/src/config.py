from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    session_secret_key: str
    spotify_client_id: str
    spotify_client_secret: str
    
    spotify_redirect_uri: str
    spotify_scopes: str = "playlist-modify-private playlist-modify-public"
    
    frontend_url: str = "http://127.0.0.1:5173"
    cors_origins: list[str] = ["http://127.0.0.1:5173"]
    environment: str = "local"


settings = Settings()  # pyright: ignore[reportCallIssue]
