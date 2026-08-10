from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.snapshot import SnapshotRepository
from app.repositories.tracked_page import TrackedPageRepository
from app.services.snapshot import SnapshotService


def get_snapshot_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SnapshotService:
    return SnapshotService(
        snapshot_repo=SnapshotRepository(session), tracked_page_repo=TrackedPageRepository(session)
    )
