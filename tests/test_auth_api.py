import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_full_auth_flow():

    test_username = f"testuser_{uuid.uuid4().hex[:6]}"
    test_password = "securepassword123"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        register_data = {"username": test_username, "password": test_password}

        headers = {"HX-Request": "true"}

        reg_response = await client.post(
            "/api/v1/auth/register", data=register_data, headers=headers
        )

        assert reg_response.status_code == 201, "Server should return 201 Created status"
        assert reg_response.headers.get("hx-redirect") == "/", (
            "Server should instruct HTMX to redirect to the home page ('/')"
        )
        assert "access_token" in reg_response.cookies, "Server should set the 'access_token' cookie"

        login_data = {"username": test_username, "password": test_password}

        login_response = await client.post("/api/v1/auth/login", data=login_data, headers=headers)

        assert login_response.status_code == 200, "Server should return 200 OK status"
        assert login_response.headers.get("hx-redirect") == "/", (
            "Server should instruct HTMX to redirect to the home page ('/')"
        )
        assert "access_token" in login_response.cookies, (
            "Server should set the 'access_token' cookie upon login"
        )


@pytest.mark.asyncio
async def test_register_short_password_returns_html_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        bad_data = {"username": "validusername", "password": "123"}

        response = await client.post(
            "/api/v1/auth/register", data=bad_data, headers={"HX-Request": "true"}
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
