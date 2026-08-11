from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import decode_access_token
from app.repositories.user import UserRepository
from app.services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    if not token:
        token = request.cookies.get("access_token")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if not token:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise credentials_exception

        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (jwt.InvalidTokenError, ValueError) as e:
        raise credentials_exception from e

    user = await UserRepository(session).get_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_optional_web_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            return None

        subject = payload.get("sub")
        if subject is None:
            return None

        user_id = int(subject)

    except (jwt.InvalidTokenError, ValueError):
        return None

    user = await UserRepository(session).get_by_id(user_id)
    return user


def get_auth_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AuthService:
    return AuthService(UserRepository(session), session)
