import asyncio
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.fetcher import PageFetchError
from app.repositories.snapshot import SnapshotRepository
from app.repositories.tracked_page import TrackedPageRepository
from app.worker.fetcher import PageFetcher


class PageCheckerService:
    def __init__(
        self,
        session: AsyncSession,
        tracked_page_repo: TrackedPageRepository,
        snapshot_repo: SnapshotRepository,
        fetcher: PageFetcher,
    ):
        self.session = session
        self.tracked_page_repo = tracked_page_repo
        self.snapshot_repo = snapshot_repo
        self.fetcher = fetcher

    async def check_page(self, page_id: int) -> None:
        page = await self.tracked_page_repo.get_by_id_internal(page_id)
        if not page:
            return

        now = datetime.now(UTC)

        try:
            fetched_data = await self.fetcher.fetch(page.url)
        except PageFetchError:
            await self.tracked_page_repo.update_internal(page.id, last_checked_at=now)
            await self.session.commit()
            return

        latest_snapshot = await self.snapshot_repo.get_latest_for_page(page.id)

        has_changes = False
        if not latest_snapshot or latest_snapshot.content_hash != fetched_data.content_hash:
            has_changes = True

        if has_changes:
            await self.snapshot_repo.create(
                tracked_page_id=page.id,
                content_hash=fetched_data.content_hash,
                content_text=fetched_data.clean_text,
            )

        update_data = {
            "title": fetched_data.title,
            "last_checked_at": now,
        }
        if has_changes:
            update_data["last_changed_at"] = now

        await self.tracked_page_repo.update_internal(page.id, **update_data)

        await self.session.commit()

    async def check_all_pages(self) -> None:
        pages = await self.tracked_page_repo.get_all_internal()
        tasks = [self.check_page(page.id) for page in pages]
        await asyncio.gather(*tasks, return_exceptions=True)
