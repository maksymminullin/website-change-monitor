from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enums.page_status import PageStatus
from app.exceptions.fetcher import PageFetchError
from app.models.snapshot import Snapshot
from app.models.tracked_page import TrackedPage
from app.schemas.fetcher import FetchedPage
from app.services.page_checker import PageCheckerService
from app.worker.fetcher import PageFetcher


@pytest.fixture
def mock_fetcher():
    fetcher = AsyncMock(spec=PageFetcher)
    return fetcher


@pytest.fixture
def mock_session_factory():
    session = AsyncMock()
    # Support async with session_factory():
    session_factory = MagicMock()
    session_factory.return_value.__aenter__.return_value = session
    return session_factory


@pytest.fixture
def checker_service(mock_session_factory, mock_fetcher):
    return PageCheckerService(session_factory=mock_session_factory, fetcher=mock_fetcher)


@pytest.mark.asyncio
async def test_check_page_not_found(checker_service, mock_session_factory, mock_fetcher):

    with patch("app.services.page_checker.TrackedPageRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_repo.get_by_id_internal.return_value = None

        await checker_service._check_page_task(1)

        mock_repo.get_by_id_internal.assert_called_once_with(1)
        mock_fetcher.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_check_page_not_active(checker_service, mock_session_factory, mock_fetcher):
    page = TrackedPage(id=1, url="http://example.com", status=PageStatus.ARCHIVED)

    with patch("app.services.page_checker.TrackedPageRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_repo.get_by_id_internal.return_value = page

        await checker_service._check_page_task(1)

        mock_fetcher.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_check_page_fetch_error(checker_service, mock_session_factory, mock_fetcher):
    session = mock_session_factory.return_value.__aenter__.return_value
    page = TrackedPage(id=1, url="http://example.com", status=PageStatus.ACTIVE)

    with (
        patch("app.services.page_checker.TrackedPageRepository") as mock_repo_class,
        patch("app.services.page_checker.SnapshotRepository"),
    ):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id_internal.return_value = page

        mock_fetcher.fetch.side_effect = PageFetchError("Failed")

        await checker_service._check_page_task(1)

        # It should update last_checked_at and commit
        mock_repo.update_internal.assert_called_once()
        assert "last_checked_at" in mock_repo.update_internal.call_args.kwargs
        session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_page_no_changes(checker_service, mock_session_factory, mock_fetcher):
    page = TrackedPage(id=1, url="http://example.com", status=PageStatus.ACTIVE)

    fetched = FetchedPage(
        url="http://example.com", title="Test", clean_text="Test content", content_hash="hash123"
    )

    latest_snap = Snapshot(content_hash="hash123")

    with (
        patch("app.services.page_checker.TrackedPageRepository") as mock_repo_class,
        patch("app.services.page_checker.SnapshotRepository") as mock_snap_class,
    ):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id_internal.return_value = page

        mock_snap = AsyncMock()
        mock_snap_class.return_value = mock_snap
        mock_snap.get_latest_for_page.return_value = latest_snap

        mock_fetcher.fetch.return_value = fetched

        await checker_service._check_page_task(1)

        # Snapshot repo shouldn't create a new one
        mock_snap.create.assert_not_called()

        # Should update last_checked_at but NOT last_changed_at
        update_kwargs = mock_repo.update_internal.call_args.kwargs
        assert "last_checked_at" in update_kwargs
        assert "last_changed_at" not in update_kwargs
        assert update_kwargs["title"] == "Test"


@pytest.mark.asyncio
async def test_check_page_with_changes(checker_service, mock_session_factory, mock_fetcher):
    page = TrackedPage(id=1, url="http://example.com", status=PageStatus.ACTIVE)

    fetched = FetchedPage(
        url="http://example.com",
        title="New Title",
        clean_text="New content",
        content_hash="newhash456",
    )

    # Old snapshot hash
    latest_snap = Snapshot(content_hash="oldhash123")

    with (
        patch("app.services.page_checker.TrackedPageRepository") as mock_repo_class,
        patch("app.services.page_checker.SnapshotRepository") as mock_snap_class,
    ):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id_internal.return_value = page

        mock_snap = AsyncMock()
        mock_snap_class.return_value = mock_snap
        mock_snap.get_latest_for_page.return_value = latest_snap

        mock_fetcher.fetch.return_value = fetched

        await checker_service._check_page_task(1)

        # Should create new snapshot
        mock_snap.create.assert_called_once_with(
            tracked_page_id=1, content_hash="newhash456", content_text="New content"
        )

        # Should update both last_checked_at and last_changed_at
        update_kwargs = mock_repo.update_internal.call_args.kwargs
        assert "last_checked_at" in update_kwargs
        assert "last_changed_at" in update_kwargs
        assert update_kwargs["title"] == "New Title"


@pytest.mark.asyncio
async def test_check_page_needs_js_upgrade(checker_service, mock_session_factory, mock_fetcher):
    page = TrackedPage(id=1, url="http://example.com", status=PageStatus.ACTIVE, requires_js=False)

    fetched = FetchedPage(
        url="http://example.com",
        title="JS App",
        clean_text="JS content",
        content_hash="jshash123",
        needs_js_upgrade=True,
    )

    with (
        patch("app.services.page_checker.TrackedPageRepository") as mock_repo_class,
        patch("app.services.page_checker.SnapshotRepository") as mock_snap_class,
    ):
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id_internal.return_value = page

        mock_snap = AsyncMock()
        mock_snap_class.return_value = mock_snap
        mock_snap.get_latest_for_page.return_value = None

        mock_fetcher.fetch.return_value = fetched

        await checker_service._check_page_task(1)

        # Should update requires_js
        update_kwargs = mock_repo.update_internal.call_args.kwargs
        assert "requires_js" in update_kwargs
        assert update_kwargs["requires_js"] is True


@pytest.mark.asyncio
async def test_check_all_pages(checker_service, mock_session_factory):
    page1 = TrackedPage(id=1)
    page2 = TrackedPage(id=2)

    with patch("app.services.page_checker.TrackedPageRepository") as mock_repo_class:
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_all_internal.return_value = [page1, page2]

        with patch.object(checker_service, "_check_page_task", new_callable=AsyncMock) as mock_task:
            await checker_service.check_all_pages()

            assert mock_task.call_count == 2
            mock_task.assert_any_call(1)
            mock_task.assert_any_call(2)
