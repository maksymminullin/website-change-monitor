import asyncio
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.enums.page_status import PageStatus
from app.exceptions.fetcher import PageFetchError
from app.repositories.snapshot import SnapshotRepository
from app.repositories.tracked_page import TrackedPageRepository
from app.worker.fetcher import PageFetcher

logger = get_logger(__name__)


class PageCheckerService:
    def __init__(
        self,
        session_factory,
        fetcher: PageFetcher,
    ):
        self.session_factory = session_factory
        self.fetcher = fetcher
        self.semaphore = asyncio.Semaphore(20)

    async def _check_page_task(self, page_id: int) -> None:
        async with self.semaphore:
            async with self.session_factory() as session:
                tracked_page_repo = TrackedPageRepository(session)
                snapshot_repo = SnapshotRepository(session)

                page = await tracked_page_repo.get_by_id_internal(page_id)
                if not page:
                    logger.warning(f"Page {page_id} not found during check")
                    return

                if page.status != PageStatus.ACTIVE:
                    logger.debug(f"Skipping page {page_id} with status {page.status}")
                    return

                now = datetime.now(UTC)
                logger.info(f"Starting check for page {page_id} ({page.url})")

                try:
                    fetched_data = await self.fetcher.fetch(page.url)
                except PageFetchError as e:
                    logger.error(f"Failed to fetch page {page_id}: {str(e)}")
                    await tracked_page_repo.update_internal(page.id, last_checked_at=now)
                    await session.commit()
                    return

                if not fetched_data.clean_text.strip():
                    logger.warning(f"Page {page_id} returned empty content")
                    await tracked_page_repo.update_internal(
                        page.id,
                        title=fetched_data.title,
                        last_checked_at=now,
                    )
                    await session.commit()
                    return

                latest_snapshot = await snapshot_repo.get_latest_for_page(page.id)

                has_changes = False
                if not latest_snapshot or latest_snapshot.content_hash != fetched_data.content_hash:
                    has_changes = True
                    logger.info(f"Changes detected for page {page_id}")

                if has_changes:
                    await snapshot_repo.create(
                        tracked_page_id=page.id,
                        content_hash=fetched_data.content_hash,
                        content_text=fetched_data.clean_text,
                    )
                    logger.debug(f"Snapshot created for page {page_id}")

                update_data = {
                    "title": fetched_data.title,
                    "last_checked_at": now,
                }
                if has_changes:
                    update_data["last_changed_at"] = now

                await tracked_page_repo.update_internal(page.id, **update_data)

                await session.commit()
                logger.info(f"Check completed for page {page_id}, changes={has_changes}")

    async def check_all_pages(self) -> None:
        async with self.session_factory() as session:
            tracked_page_repo = TrackedPageRepository(session)
            pages = await tracked_page_repo.get_all_internal()

        logger.info(f"Starting check cycle for {len(pages)} active pages")

        tasks = [self._check_page_task(page.id) for page in pages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        error_count = sum(1 for r in results if isinstance(r, Exception))
        if error_count:
            logger.warning(f"Check cycle completed with {error_count} errors")
        else:
            logger.info("Check cycle completed successfully")
