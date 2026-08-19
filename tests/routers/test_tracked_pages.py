from datetime import UTC, datetime
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user
from app.dependencies.tracked_page import get_tracked_page_service
from app.models.user import User
from app.schemas.tracked_page import TrackedPageCreate, TrackedPageRead
from app.exceptions.tracked_page import TrackedPageAlreadyExistsError
from main import app


async def test_create_tracked_page_success():

    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))

    fake_created_page = TrackedPageRead(
        id=10, url="https://example.com", status="active", created_at=datetime.now(UTC)
    )

    mock_service = AsyncMock()
    mock_service.create.return_value = fake_created_page

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/tracked-pages", data={"url": "https://example.com"})

    assert response.status_code == 201
    assert response.json()["id"] == 10
    assert response.json()["url"] == "https://example.com"

    mock_service.create.assert_called_once()

    call_kwargs = mock_service.create.call_args.kwargs
    assert call_kwargs["user_id"] == 1
    assert isinstance(call_kwargs["page_in"], TrackedPageCreate)
    assert call_kwargs["page_in"].url == "https://example.com"

    app.dependency_overrides.clear()


async def test_create_tracked_page_already_exists():

    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))

    mock_service = AsyncMock()
    mock_service.create.side_effect = TrackedPageAlreadyExistsError("tracked page already exists")

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/tracked-pages", data={"url": "https://example.com"})

    assert response.status_code == 409
    assert response.json()["detail"] == "tracked page already exists"

    app.dependency_overrides.clear()
