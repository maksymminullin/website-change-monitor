import uuid

from httpx import ASGITransport, AsyncClient

from main import app


import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.schemas.auth import TokenResponse
from app.dependencies.auth import get_auth_service
from main import app


async def test_full_auth_flow():

    test_username = f"testuser_{uuid.uuid4().hex[:6]}"
    test_password = "securepassword123"

    from app.schemas.user import UserRead
    
    mock_auth = AsyncMock()
    mock_user = UserRead(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_auth.register.return_value = TokenResponse(
        access_token="fake_token", 
        token_type="bearer",
        refresh_token="fake_refresh",
        user=mock_user
    )
    mock_auth.login.return_value = TokenResponse(
        access_token="fake_token", 
        token_type="bearer",
        refresh_token="fake_refresh",
        user=mock_user
    )

    app.dependency_overrides[get_auth_service] = lambda: mock_auth

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        register_data = {"username": test_username, "password": test_password}

        reg_response = await client.post(
            "/api/v1/auth/register", json=register_data
        )

        assert reg_response.status_code == 201, "Server should return 201 Created status"
        data = reg_response.json()
        assert "access_token" in data
        assert "access_token" in reg_response.cookies, "Server should set the 'access_token' cookie"

        login_data = {"username": test_username, "password": test_password}

        login_response = await client.post("/api/v1/auth/login", data=login_data)

        assert login_response.status_code == 200, "Server should return 200 OK status"
        data = login_response.json()
        assert "access_token" in data
        assert "access_token" in login_response.cookies, (
            "Server should set the 'access_token' cookie upon login"
        )
        
    app.dependency_overrides.clear()


async def test_register_short_password_returns_html_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        bad_data = {"username": "validusername", "password": "123"}

        response = await client.post(
            "/register", data=bad_data
        )

        assert response.status_code == 200, (
            "Server should catch the error and return 200 OK for HTMX"
        )
        assert "class='text-error'" in response.text, (
            "Response should contain the HTML span with 'text-error' class"
        )
        assert "invalid input" in response.text.lower(), (
            "Response should contain the validation error message"
        )
