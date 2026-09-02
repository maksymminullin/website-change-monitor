from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.enums.page_status import PageStatus
from app.exceptions.tracked_page import TrackedPageAlreadyExistsError, TrackedPageNotFoundError
from app.models.tracked_page import TrackedPage
from app.schemas.tracked_page import TrackedPageCreate, TrackedPageUpdate
from app.services.tracked_page import TrackedPageService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.session = AsyncMock()
    return repo


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def tracked_page_service(mock_repo, mock_session):
    return TrackedPageService(repository=mock_repo, session=mock_session)


@pytest.mark.asyncio
async def test_get_all(tracked_page_service, mock_repo):
    page1 = TrackedPage(
        id=1,
        url="http://example.com",
        status=PageStatus.ACTIVE,
        requires_js=False,
        created_at=datetime.now(UTC),
    )
    mock_repo.get_all_by_user_id.return_value = [page1]

    result = await tracked_page_service.get_all(user_id=1)

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].url == "http://example.com"
    mock_repo.get_all_by_user_id.assert_called_once_with(user_id=1)


@pytest.mark.asyncio
async def test_create_success(tracked_page_service, mock_repo):
    mock_repo.get_by_user_id_and_url.return_value = None
    mock_page = TrackedPage(
        id=1,
        url="http://example.com",
        status=PageStatus.ACTIVE,
        requires_js=False,
        created_at=datetime.now(UTC),
    )
    mock_repo.create.return_value = mock_page

    page_in = TrackedPageCreate(url="http://example.com")
    result = await tracked_page_service.create(user_id=1, page_in=page_in)

    assert result.id == 1
    assert result.url == "http://example.com"
    mock_repo.create.assert_called_once()
    mock_repo.session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_duplicate_check(tracked_page_service, mock_repo):
    mock_repo.get_by_user_id_and_url.return_value = TrackedPage(
        id=1, url="http://example.com", requires_js=False, created_at=datetime.now(UTC)
    )

    page_in = TrackedPageCreate(url="http://example.com")
    with pytest.raises(TrackedPageAlreadyExistsError):
        await tracked_page_service.create(user_id=1, page_in=page_in)


@pytest.mark.asyncio
async def test_create_integrity_error(tracked_page_service, mock_repo):
    mock_repo.get_by_user_id_and_url.return_value = None
    mock_repo.create.side_effect = IntegrityError("test", "test", "test")

    page_in = TrackedPageCreate(url="http://example.com")
    with pytest.raises(TrackedPageAlreadyExistsError):
        await tracked_page_service.create(user_id=1, page_in=page_in)
    mock_repo.session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_delete_success(tracked_page_service, mock_repo):
    mock_page = TrackedPage(id=1)
    mock_repo.get_by_id.return_value = mock_page

    await tracked_page_service.delete(user_id=1, page_id=1)

    mock_repo.delete.assert_called_once_with(mock_page)
    mock_repo.session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_not_found(tracked_page_service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(TrackedPageNotFoundError):
        await tracked_page_service.delete(user_id=1, page_id=1)


@pytest.mark.asyncio
async def test_update_success(tracked_page_service, mock_repo):
    mock_page = TrackedPage(
        id=1,
        url="http://example.com",
        status=PageStatus.ACTIVE,
        requires_js=False,
        created_at=datetime.now(UTC),
    )
    mock_repo.get_by_id.return_value = mock_page

    updated_page = TrackedPage(
        id=1,
        url="http://example.com",
        status=PageStatus.ARCHIVED,
        requires_js=False,
        created_at=datetime.now(UTC),
    )
    mock_repo.update.return_value = updated_page

    update_in = TrackedPageUpdate(status=PageStatus.ARCHIVED)
    result = await tracked_page_service.update(user_id=1, page_id=1, page_in=update_in)

    assert result.status == PageStatus.ARCHIVED
    mock_repo.update.assert_called_once_with(page=mock_page, page_in=update_in)
    mock_repo.session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_not_found(tracked_page_service, mock_repo):
    mock_repo.get_by_id.return_value = None

    update_in = TrackedPageUpdate(status=PageStatus.ARCHIVED)
    with pytest.raises(TrackedPageNotFoundError):
        await tracked_page_service.update(user_id=1, page_id=1, page_in=update_in)
