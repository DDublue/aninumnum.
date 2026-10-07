from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    refresh_token: str | None = None


class SpotifyUser(BaseModel):
    account_id: str
    id: str
    display_name: str | None = None
