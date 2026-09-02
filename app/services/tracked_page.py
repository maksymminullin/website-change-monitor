from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.exceptions.tracked_page import (
    TrackedPageAlreadyExistsError,
    TrackedPageNotFoundError,
)
from app.repositories.tracked_page import TrackedPageRepository
from app.schemas.tracked_page import (
    TrackedPageCreate,
    TrackedPageRead,
    TrackedPageUpdate,
    normalize_url,
)

logger = get_logger(__name__)


class TrackedPageService:
    def __init__(self, repository: TrackedPageRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def get_all(self, user_id: int) -> list[TrackedPageRead]:
        pages = await self.repository.get_all_by_user_id(user_id=user_id)
        return [TrackedPageRead.model_validate(page) for page in pages]

    async def create(self, user_id: int, page_in: TrackedPageCreate) -> TrackedPageRead:
        normalized_url = normalize_url(page_in.url)
        existing_page = await self.repository.get_by_user_id_and_url(
            user_id=user_id,
            url=normalized_url,
        )
        if existing_page is not None:
            logger.warning(f"Duplicate tracked page attempt: user={user_id}, url={normalized_url}")
            raise TrackedPageAlreadyExistsError("You already track this URL")

        try:
            page = await self.repository.create(user_id=user_id, page_in=page_in)
            await self.repository.session.commit()
            await self.repository.session.refresh(page)
            logger.info(f"Tracked page created: id={page.id}, user={user_id}, url={normalized_url}")
            return TrackedPageRead.model_validate(page)
        except IntegrityError as e:
            await self.repository.session.rollback()
            logger.error(
                f"Integrity error creating page: user={user_id}, "
                f"url={normalized_url}, error={str(e)}"
            )
            raise TrackedPageAlreadyExistsError("You already track this URL") from e

    async def delete(self, user_id: int, page_id: int) -> None:
        page = await self.repository.get_by_id(user_id=user_id, page_id=page_id)
        if page is None:
            logger.warning(f"Delete attempt for non-existent page: id={page_id}, user={user_id}")
            raise TrackedPageNotFoundError("Tracked page not found")
        await self.repository.delete(page)
        await self.repository.session.commit()
        logger.info(f"Tracked page deleted: id={page_id}, user={user_id}")

    async def update(
        self, user_id: int, page_id: int, page_in: TrackedPageUpdate
    ) -> TrackedPageRead:
        page = await self.repository.get_by_id(user_id=user_id, page_id=page_id)
        if page is None:
            logger.warning(f"Update attempt for non-existent page: id={page_id}, user={user_id}")
            raise TrackedPageNotFoundError("Tracked page not found")

        updated_page = await self.repository.update(page=page, page_in=page_in)

        await self.repository.session.commit()
        await self.repository.session.refresh(updated_page)
        
        logger.info(f"Tracked page updated: id={page_id}, user={user_id}, status={page_in.status}")
        return TrackedPageRead.model_validate(updated_page)
