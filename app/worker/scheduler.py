from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.database import async_session_factory
from app.services.page_checker import PageCheckerService
from app.worker.fetcher import PageFetcher


async def run_page_check_job() -> None:
    fetcher = PageFetcher(timeout=15)

    try:
        service = PageCheckerService(
            session_factory=async_session_factory,
            fetcher=fetcher,
        )

        await service.check_all_pages()
    finally:
        await fetcher.aclose()


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

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

    return scheduler
