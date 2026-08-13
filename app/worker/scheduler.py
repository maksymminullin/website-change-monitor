from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import async_session_factory
from app.repositories.snapshot import SnapshotRepository
from app.repositories.tracked_page import TrackedPageRepository
from app.services.page_checker import PageCheckerService
from app.worker.fetcher import PageFetcher


async def run_page_check_job() -> None:
    async with async_session_factory() as session:
        tracked_page_repo = TrackedPageRepository(session)
        snapshot_repo = SnapshotRepository(session)
        fetcher = PageFetcher(timeout=15)

        service = PageCheckerService(
            session=session,
            tracked_page_repo=tracked_page_repo,
            snapshot_repo=snapshot_repo,
            fetcher=fetcher,
        )

        await service.check_all_pages()


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduler.add_job(
            run_page_check_job,
            "interval",
            minutes=60,
            id="check_pages",
            replace_existing=True,
            next_run_time=datetime.now(),
            max_instances=1,
            coalesce=True,
        )
    )
    return scheduler
