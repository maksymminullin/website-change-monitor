from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.tracked_page import TrackedPageRepository
from app.services.tracked_page import TrackedPageService


def get_tracked_page_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrackedPageService:
    return TrackedPageService(TrackedPageRepository(session), session)
