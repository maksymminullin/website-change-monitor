from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.snapshot import Snapshot


class SnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_by_tracked_page_id(self, tracked_page_id: int) -> list[Snapshot]:
        snapshots = await self.session.execute(
            select(Snapshot)
            .where(Snapshot.tracked_page_id == tracked_page_id)
            .order_by(Snapshot.created_at.desc())
        )

        return list(snapshots.scalars().all())

    async def get_latest_for_page(self, tracked_page_id: int) -> Snapshot | None:
        result = await self.session.execute(
            select(Snapshot)
            .where(Snapshot.tracked_page_id == tracked_page_id)
            .order_by(Snapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, tracked_page_id: int, content_hash: str, content_text: str) -> Snapshot:
        snapshot = Snapshot(
            tracked_page_id=tracked_page_id, content_hash=content_hash, content_text=content_text
        )
        self.session.add(snapshot)
        return snapshot

    async def delete(self, snapshot: Snapshot) -> None:
        await self.session.delete(snapshot)
