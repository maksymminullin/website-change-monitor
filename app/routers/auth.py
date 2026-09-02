from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies.auth import get_auth_service
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    response: Response,
    user_in: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    token_data = await auth_service.register(user_in)
    response.set_cookie("access_token", token_data.access_token, httponly=True, samesite="lax")
    return token_data


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    token_data = await auth_service.login(username=form_data.username, password=form_data.password)
    response.set_cookie("access_token", token_data.access_token, httponly=True, samesite="lax")
    return token_data


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token_in: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await auth_service.refresh(refresh_token_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie("access_token")
    return None
