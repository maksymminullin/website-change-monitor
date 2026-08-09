from typing import Annotated

from core.database import get_db_session
from fastapi import Depends
from repositories.snapshot import SnapshotRepository
from repositories.tracked_page import TrackedPageRepository
from services.snapshot import SnapshotService
from sqlalchemy.ext.asyncio import AsyncSession


def get_snapshot_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SnapshotService:
    return SnapshotService(
        snapshot_repo=SnapshotRepository(session), tracked_page_repo=TrackedPageRepository(session)
    )
