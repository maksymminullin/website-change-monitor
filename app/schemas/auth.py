from pydantic import BaseModel

from app.schemas.user import UserRead


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
