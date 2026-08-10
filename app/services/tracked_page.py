from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.tracked_page import TrackedPageAlreadyExistsError, TrackedPageNotFoundError
from app.repositories.tracked_page import TrackedPageRepository
from app.schemas.tracked_page import TrackedPageCreate, TrackedPageRead, TrackedPageUpdate


class TrackedPageService:
    def __init__(self, repository: TrackedPageRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def get_all(self, user_id: int) -> list[TrackedPageRead]:
        pages = await self.repository.get_all_by_user_id(user_id=user_id)
        return [TrackedPageRead.model_validate(page) for page in pages]

    async def create(self, user_id: int, page_in: TrackedPageCreate) -> TrackedPageRead:
        try:
            page = await self.repository.create(user_id=user_id, page_in=page_in)
            await self.repository.session.commit()
            await self.repository.session.refresh(page)
            return TrackedPageRead.model_validate(page)
        except IntegrityError as e:
            await self.repository.session.rollback()
            raise TrackedPageAlreadyExistsError("You already track this URL") from e

    async def delete(self, user_id: int, page_id: int) -> None:
        page = await self.repository.get_by_id(user_id=user_id, page_id=page_id)
        if page is None:
            raise TrackedPageNotFoundError("Tracked page not found")
        await self.repository.delete(page)
        await self.repository.session.commit()

    async def update(
        self, user_id: int, page_id: int, page_in: TrackedPageUpdate
    ) -> TrackedPageRead:
        page = await self.repository.get_by_id(user_id=user_id, page_id=page_id)
        if page is None:
            raise TrackedPageNotFoundError("Tracked page not found")
        updated_page = await self.repository.update(page=page, page_in=page_in)
        return TrackedPageRead.model_validate(updated_page)
