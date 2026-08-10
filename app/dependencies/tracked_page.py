from typing import Annotated

from core.database import get_db_session
from fastapi import Depends
from repositories.tracked_page import TrackedPageRepository
from services.tracked_page import TrackedPageService
from sqlalchemy.ext.asyncio import AsyncSession


def get_tracked_page_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrackedPageService:
    return TrackedPageService(TrackedPageRepository(session), session)
