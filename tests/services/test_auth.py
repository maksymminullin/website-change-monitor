from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.auth import InvalidCredentialsError, InvalidRefreshTokenError
from app.exceptions.user import UserAlreadyExistsError
from app.models.user import User
from app.schemas.auth import RefreshTokenRequest
from app.schemas.user import UserCreate
from app.services.auth import AuthService


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def auth_service(mock_user_repo, mock_session):
    return AuthService(user_repo=mock_user_repo, session=mock_session)


@pytest.mark.asyncio
async def test_register_success(auth_service, mock_user_repo, mock_session):
    mock_user_repo.get_by_username.return_value = None
    mock_user = User(id=1, username="testuser", password_hash="hashed_pw")
    mock_user_repo.create.return_value = mock_user

    with patch("app.services.auth.hash_password", return_value="hashed_pw"):
        with patch.object(auth_service, "_create_token_response") as mock_create_token:
            mock_create_token.return_value = "TokenResponse"

            user_create = UserCreate(username="testuser", password="password")
            response = await auth_service.register(user_create)

            assert response == "TokenResponse"
            mock_user_repo.get_by_username.assert_called_once_with("testuser")
            mock_user_repo.create.assert_called_once_with(
                username="testuser", password_hash="hashed_pw"
            )
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_user)


@pytest.mark.asyncio
async def test_register_user_exists(auth_service, mock_user_repo):
    mock_user_repo.get_by_username.return_value = User(id=1, username="testuser")

    user_create = UserCreate(username="testuser", password="password")
    with pytest.raises(UserAlreadyExistsError, match="Username already exists"):
        await auth_service.register(user_create)


@pytest.mark.asyncio
async def test_login_success(auth_service, mock_user_repo):
    mock_user = User(id=1, username="testuser", password_hash="hashed_pw")
    mock_user_repo.get_by_username.return_value = mock_user

    with patch("app.services.auth.verify_password", return_value=True):
        with patch.object(auth_service, "_create_token_response") as mock_create_token:
            mock_create_token.return_value = "TokenResponse"

            response = await auth_service.login("testuser", "password")

            assert response == "TokenResponse"


@pytest.mark.asyncio
async def test_login_invalid_password(auth_service, mock_user_repo):
    mock_user = User(id=1, username="testuser", password_hash="hashed_pw")
    mock_user_repo.get_by_username.return_value = mock_user

    with patch("app.services.auth.verify_password", return_value=False):
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login("testuser", "wrong_password")


@pytest.mark.asyncio
async def test_login_user_not_found(auth_service, mock_user_repo):
    mock_user_repo.get_by_username.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await auth_service.login("unknown", "password")


@pytest.mark.asyncio
async def test_refresh_success(auth_service, mock_user_repo):
    mock_user = User(id=1, username="testuser")
    mock_user_repo.get_by_id.return_value = mock_user

    with patch(
        "app.services.auth.decode_refresh_token", return_value={"type": "refresh", "sub": "1"}
    ):
        with patch.object(auth_service, "_create_token_response") as mock_create_token:
            mock_create_token.return_value = "TokenResponse"

            response = await auth_service.refresh(RefreshTokenRequest(refresh_token="valid_token"))

            assert response == "TokenResponse"
            mock_user_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_refresh_invalid_type(auth_service):
    with patch(
        "app.services.auth.decode_refresh_token", return_value={"type": "access", "sub": "1"}
    ):
        with pytest.raises(InvalidRefreshTokenError, match="Failed to decode or validate token"):
            await auth_service.refresh(RefreshTokenRequest(refresh_token="invalid_token"))


@pytest.mark.asyncio
async def test_refresh_user_not_found(auth_service, mock_user_repo):
    mock_user_repo.get_by_id.return_value = None

    with patch(
        "app.services.auth.decode_refresh_token", return_value={"type": "refresh", "sub": "1"}
    ):
        with pytest.raises(
            InvalidRefreshTokenError, match="User associated with token no longer exists"
        ):
            await auth_service.refresh(RefreshTokenRequest(refresh_token="valid_token"))
