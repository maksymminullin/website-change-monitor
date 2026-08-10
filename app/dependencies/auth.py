from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import decode_access_token
from app.repositories.user import UserRepository
from app.services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise credentials_exception

        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (
        jwt.InvalidTokenError,
        ValueError,
    ) as e:
        raise credentials_exception from e

    user = await UserRepository(session).get_by_id(user_id)

    if user is None:
        raise credentials_exception

    return user


def get_auth_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AuthService:
    return AuthService(UserRepository(session), session)
