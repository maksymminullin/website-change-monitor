from datetime import UTC, datetime
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.dependencies.auth import get_current_user
from app.dependencies.snapshot import get_snapshot_service
from app.dependencies.tracked_page import get_tracked_page_service
from app.enums.page_status import PageStatus
from app.exceptions.tracked_page import (
    TrackedPageAlreadyExistsError,
    TrackedPageNotFoundError,
)
from app.models.user import User
from app.schemas.snapshot import SnapshotRead
from app.schemas.tracked_page import (
    TrackedPageCreate,
    TrackedPageRead,
    TrackedPageUpdate,
    normalize_url,
)
from main import app


async def test_create_tracked_page_success():

    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))

    fake_created_page = TrackedPageRead(
        id=10, url="https://example.com", status=PageStatus.ACTIVE, created_at=datetime.now(UTC)
    )

    mock_service = AsyncMock()
    mock_service.create.return_value = fake_created_page

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/tracked-pages", json={"url": "https://example.com"})

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
        response = await client.post("/api/v1/tracked-pages", json={"url": "https://example.com"})

    assert response.status_code == 409
    assert response.json()["detail"] == "tracked page already exists"

    app.dependency_overrides.clear()


def test_normalize_url_preserves_query_string_and_canonicalizes_root_and_trailing_slash():
    assert (
        normalize_url(" https://EXAMPLE.com/?utm_source=ads ")
        == "https://example.com/?utm_source=ads"
    )
    assert normalize_url("https://example.com/about/") == "https://example.com/about"
    assert (
        normalize_url("https://example.com/path?cat=1&id=2")
        == "https://example.com/path?cat=1&id=2"
    )


async def test_create_service_rejects_duplicate_after_url_normalization():
    from app.exceptions.tracked_page import TrackedPageAlreadyExistsError
    from app.services.tracked_page import TrackedPageService

    repo = AsyncMock()
    session = AsyncMock()

    service = TrackedPageService(repository=repo, session=session)
    repo.get_by_user_id_and_url.return_value = object()

    try:
        await service.create(
            user_id=1,
            page_in=TrackedPageCreate(url="https://EXAMPLE.com/?utm_source=ads"),
        )
        raise AssertionError("Expected TrackedPageAlreadyExistsError")
    except TrackedPageAlreadyExistsError:
        pass


async def test_create_tracked_page_missing_url():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/tracked-pages", json={})

    assert response.status_code == 422
    mock_service.create.assert_not_called()

    app.dependency_overrides.clear()


async def test_create_tracked_page_htmx_success():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    fake_created_page = TrackedPageRead(
        id=10, url="https://example.com", status=PageStatus.ACTIVE, created_at=datetime.now(UTC)
    )

    mock_service = AsyncMock()
    mock_service.create.return_value = fake_created_page

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/tracked-pages",
            data={"url": "https://example.com"},
        )

    assert response.status_code == 200
    assert "alert alert-success" in response.text
    assert "https://example.com" in response.text

    app.dependency_overrides.clear()


async def test_create_tracked_page_htmx_duplicate():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()
    mock_service.create.side_effect = TrackedPageAlreadyExistsError("Page already tracked")

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/tracked-pages",
            data={"url": "https://example.com"},
        )

    assert response.status_code == 200
    assert "Page already tracked" in response.text

    app.dependency_overrides.clear()


async def test_get_all_tracked_pages():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    fake_pages = [
        TrackedPageRead(
            id=1, url="https://example1.com", status=PageStatus.ACTIVE, created_at=datetime.now(UTC)
        ),
        TrackedPageRead(
            id=2, url="https://example2.com", status=PageStatus.ACTIVE, created_at=datetime.now(UTC)
        ),
    ]

    mock_service = AsyncMock()
    mock_service.get_all.return_value = fake_pages

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/tracked-pages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["url"] == "https://example1.com"
    assert data[0]["status"] == "active"
    assert data[1]["url"] == "https://example2.com"
    assert data[1]["status"] == "active"

    mock_service.get_all.assert_called_once_with(user_id=1)

    app.dependency_overrides.clear()


async def test_get_all_tracked_pages_empty():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()
    mock_service.get_all.return_value = []

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/tracked-pages")

    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()


async def test_update_tracked_page_status():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    updated_page = TrackedPageRead(
        id=10, url="https://example.com", status=PageStatus.ARCHIVED, created_at=datetime.now(UTC)
    )

    mock_service = AsyncMock()
    mock_service.update.return_value = updated_page

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.patch(
            "/api/v1/tracked-pages/10",
            json={"status": "archived"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "archived"

    call_kwargs = mock_service.update.call_args.kwargs
    assert call_kwargs["user_id"] == 1
    assert call_kwargs["page_id"] == 10
    assert isinstance(call_kwargs["page_in"], TrackedPageUpdate)

    app.dependency_overrides.clear()


async def test_update_tracked_page_htmx():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    updated_page = TrackedPageRead(
        id=10, url="https://example.com", status=PageStatus.ARCHIVED, created_at=datetime.now(UTC)
    )

    mock_service = AsyncMock()
    mock_service.update.return_value = updated_page

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.patch(
            "/tracked-pages/10",
            data={"status": "archived"},
        )

    assert response.status_code == 200
    assert response.headers.get("HX-Refresh") == "true"

    app.dependency_overrides.clear()


async def test_update_tracked_page_not_found():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()
    mock_service.update.side_effect = TrackedPageNotFoundError("Page not found")

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.patch(
            "/api/v1/tracked-pages/999",
            json={"status": "archived"},
        )

    assert response.status_code == 404

    app.dependency_overrides.clear()


async def test_update_tracked_page_no_data():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.patch("/api/v1/tracked-pages/10", json={})

    assert response.status_code == 422
    mock_service.update.assert_not_called()

    app.dependency_overrides.clear()


async def test_delete_tracked_page():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.delete("/api/v1/tracked-pages/10")

    assert response.status_code == 204
    mock_service.delete.assert_called_once_with(user_id=1, page_id=10)

    app.dependency_overrides.clear()


async def test_delete_tracked_page_htmx():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.delete("/tracked-pages/10")

    assert response.status_code == 200
    assert response.text == ""

    app.dependency_overrides.clear()


async def test_delete_tracked_page_not_found():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()
    mock_service.delete.side_effect = TrackedPageNotFoundError("Page not found")

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_tracked_page_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.delete("/api/v1/tracked-pages/999")

    assert response.status_code == 404

    app.dependency_overrides.clear()


async def test_get_snapshots_for_page():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    fake_snapshots = [
        SnapshotRead(
            id=1,
            tracked_page_id=10,
            content_hash="abc123",
            content_text="This is page content",
            created_at=datetime.now(UTC),
        ),
        SnapshotRead(
            id=2,
            tracked_page_id=10,
            content_hash="def456",
            content_text="Updated page content",
            created_at=datetime.now(UTC),
        ),
    ]

    mock_service = AsyncMock()
    mock_service.get_all.return_value = fake_snapshots

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_snapshot_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/tracked-pages/10/snapshots")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["content_hash"] == "abc123"
    assert data[1]["id"] == 2

    mock_service.get_all.assert_called_once_with(user_id=1, tracked_page_id=10)

    app.dependency_overrides.clear()


async def test_get_snapshots_empty():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()
    mock_service.get_all.return_value = []

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_snapshot_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/tracked-pages/10/snapshots")

    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()


async def test_get_snapshots_page_not_found():
    fake_user = User(id=1, username="testuser", created_at=datetime.now(UTC))
    mock_service = AsyncMock()
    mock_service.get_all.side_effect = TrackedPageNotFoundError("Page not found")

    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_snapshot_service] = lambda: mock_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/tracked-pages/999/snapshots")

    assert response.status_code == 404

    app.dependency_overrides.clear()
