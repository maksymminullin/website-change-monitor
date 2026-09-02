from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.exceptions.tracked_page import TrackedPageNotFoundError
from app.models.snapshot import Snapshot
from app.models.tracked_page import TrackedPage
from app.services.snapshot import SnapshotService


@pytest.fixture
def mock_snapshot_repo():
    return AsyncMock()


@pytest.fixture
def mock_tracked_page_repo():
    return AsyncMock()


@pytest.fixture
def snapshot_service(mock_snapshot_repo, mock_tracked_page_repo):
    return SnapshotService(
        snapshot_repo=mock_snapshot_repo, tracked_page_repo=mock_tracked_page_repo
    )


@pytest.mark.asyncio
async def test_get_all_success(snapshot_service, mock_snapshot_repo, mock_tracked_page_repo):
    mock_tracked_page_repo.get_by_id.return_value = TrackedPage(
        id=1, user_id=1, url="http://example.com"
    )

    snap = Snapshot(
        id=1,
        tracked_page_id=1,
        content_hash="hash",
        content_text="text",
        created_at=datetime.now(UTC),
    )
    mock_snapshot_repo.get_all_by_tracked_page_id.return_value = [snap]

    result = await snapshot_service.get_all(user_id=1, tracked_page_id=1)

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].content_hash == "hash"
    assert result[0].content_text == "text"

    mock_tracked_page_repo.get_by_id.assert_called_once_with(user_id=1, page_id=1)
    mock_snapshot_repo.get_all_by_tracked_page_id.assert_called_once_with(tracked_page_id=1)


@pytest.mark.asyncio
async def test_get_all_page_not_found(snapshot_service, mock_tracked_page_repo):
    mock_tracked_page_repo.get_by_id.return_value = None

    with pytest.raises(TrackedPageNotFoundError):
        await snapshot_service.get_all(user_id=1, tracked_page_id=1)


@pytest.mark.asyncio
async def test_create(snapshot_service, mock_snapshot_repo):
    snap = Snapshot(
        id=1,
        tracked_page_id=1,
        content_hash="hash",
        content_text="text",
        created_at=datetime.now(UTC),
    )
    mock_snapshot_repo.create.return_value = snap

    result = await snapshot_service.create(
        tracked_page_id=1, content_hash="hash", content_text="text"
    )

    assert result == snap
    mock_snapshot_repo.create.assert_called_once_with(
        tracked_page_id=1, content_hash="hash", content_text="text"
    )
