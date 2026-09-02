from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from app.dependencies.auth import get_auth_service
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        user_in = UserCreate(username=username, password=password)
    except ValidationError as e:
        if request.headers.get("hx-request"):
            error_msg = (
                "Invalid input: Username must be at least 3 characters "
                "and password at least 6 characters."
            )
            return HTMLResponse(
                f"<span class='text-error'>{error_msg}</span>", status_code=status.HTTP_200_OK
            )
        raise HTTPException(status_code=400, detail="Invalid input") from e

    token_data = await auth_service.register(user_in)

    response.set_cookie("access_token", token_data.access_token, httponly=True, samesite="lax")

    if request.headers.get("hx-request"):
        response.headers["HX-Redirect"] = "/"

    return token_data


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    token_data = await auth_service.login(username=form_data.username, password=form_data.password)

    response.set_cookie("access_token", token_data.access_token, httponly=True, samesite="lax")

    if request.headers.get("hx-request"):
        response.headers["HX-Redirect"] = "/"

    return token_data


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token_in: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return await auth_service.refresh(refresh_token_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    response.delete_cookie("access_token")

    if request.headers.get("hx-request"):
        response.headers["HX-Redirect"] = "/login"

    return None
