import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.exceptions.auth import InvalidCredentialsError, InvalidRefreshTokenError
from app.exceptions.user import UserAlreadyExistsError
from app.repositories.user import UserRepository
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead


class AuthService:
    def __init__(self, user_repo: UserRepository, session: AsyncSession) -> None:
        self.user_repo = user_repo
        self.session = session

    async def register(self, user_in: UserCreate) -> TokenResponse:
        existing_user = await self.user_repo.get_by_username(user_in.username)
        if existing_user is not None:
            raise UserAlreadyExistsError("Username already exists")

        password_hash = hash_password(user_in.password)

        user = await self.user_repo.create(username=user_in.username, password_hash=password_hash)

        await self.session.commit()
        await self.session.refresh(user)

        return self._create_token_response(user)

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_username(username)
        if user is None:
            raise InvalidCredentialsError("Incorrect username or password")

        is_password_valid = verify_password(
            plain_password=password, hashed_password=user.password_hash
        )
        if not is_password_valid:
            raise InvalidCredentialsError("Incorrect username or password")

        return self._create_token_response(user)

    async def refresh(self, refresh_token_in: RefreshTokenRequest) -> TokenResponse:
        try:
            payload = decode_refresh_token(refresh_token_in.refresh_token)
            if payload.get("type") != "refresh":
                raise InvalidRefreshTokenError("Token type is not 'refresh'")

            subject = payload.get("sub")
            if subject is None:
                raise InvalidRefreshTokenError("Token payload is missing 'sub'")

            user_id = int(subject)

        except (
            jwt.InvalidTokenError,
            InvalidRefreshTokenError,
            ValueError,
        ) as e:
            raise InvalidRefreshTokenError("Failed to decode or validate token") from e

        user = await self.user_repo.get_by_id(user_id)

        if user is None:
            raise InvalidRefreshTokenError("User associated with token no longer exists")

        return self._create_token_response(user)

    @staticmethod
    def _create_token_response(user) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            user=UserRead.model_validate(user),
        )
