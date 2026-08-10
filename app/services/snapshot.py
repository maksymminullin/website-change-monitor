from app.exceptions.tracked_page import TrackedPageNotFoundError
from app.models.snapshot import Snapshot
from app.repositories.snapshot import SnapshotRepository
from app.repositories.tracked_page import TrackedPageRepository
from app.schemas.snapshot import SnapshotRead


class SnapshotService:
    def __init__(
        self, snapshot_repo: SnapshotRepository, tracked_page_repo: TrackedPageRepository
    ) -> None:
        self.snapshot_repo = snapshot_repo
        self.tracked_page_repo = tracked_page_repo

    async def get_all(self, user_id: int, tracked_page_id: int) -> list[SnapshotRead]:
        tracked_page = await self.tracked_page_repo.get_by_id(
            user_id=user_id, page_id=tracked_page_id
        )
        if tracked_page is None:
            raise TrackedPageNotFoundError("Tracked page not found")
        snapshots = await self.snapshot_repo.get_all_by_tracked_page_id(
            tracked_page_id=tracked_page_id
        )
        return [SnapshotRead.model_validate(snapshot) for snapshot in snapshots]

    async def create(self, tracked_page_id: int, content_hash: str, content_text: str) -> Snapshot:
        snapshot = await self.snapshot_repo.create(
            tracked_page_id=tracked_page_id, content_hash=content_hash, content_text=content_text
        )
        return snapshot
