from models.tracked_page import TrackedPage
from schemas.tracked_page import TrackedPageCreate, TrackedPageUpdate
from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession


class TrackedPageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_internal(self) -> list[TrackedPage]:
        pages = await self.session.execute(select(TrackedPage))
        return list(pages.scalars().all())

    async def get_by_id_internal(self, page_id: int) -> TrackedPage | None:
        page = await self.session.execute(select(TrackedPage).where(TrackedPage.id == page_id))
        return page.scalar_one_or_none()

    async def get_by_id(self, page_id: int, user_id: int) -> TrackedPage | None:
        page = await self.session.execute(
            select(TrackedPage).where(TrackedPage.id == page_id, TrackedPage.user_id == user_id)
        )
        return page.scalar_one_or_none()

    async def get_all_by_user_id(self, user_id: int) -> list[TrackedPage]:
        pages = await self.session.execute(
            select(TrackedPage).where(TrackedPage.user_id == user_id)
        )
        return list(pages.scalars().all())

    async def create(self, user_id: int, page_in: TrackedPageCreate) -> TrackedPage:
        page = TrackedPage(user_id=user_id, url=page_in.url, status="active")
        self.session.add(page)
        return page

    async def update_internal(self, page_id: int, **kwargs) -> None:
        await self.session.execute(
            sa_update(TrackedPage).where(TrackedPage.id == page_id).values(**kwargs)
        )

    async def update(self, page: TrackedPage, page_in: TrackedPageUpdate) -> TrackedPage:
        page.status = page_in.status
        return page

    async def delete(self, page: TrackedPage) -> None:
        await self.session.delete(page)
