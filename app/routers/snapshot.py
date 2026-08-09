from typing import Annotated

from dependencies.snapshot import get_snapshot_service
from exceptions.snapshot import SnapshotNotFoundError
from exceptions.tracked_page import TrackedPageNotFoundError
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.snapshot import SnapshotCreate, SnapshotRead
from services.snapshot import SnapshotService

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.post("", response_model=SnapshotRead, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    snapshot_in: SnapshotCreate,
    user_id: int,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> SnapshotRead:
    try:
        return await service.create_snapshot(user_id=user_id, snapshot_in=snapshot_in)

    except TrackedPageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/tracked-page/{tracked_page_id}", response_model=list[SnapshotRead])
async def get_all_snapshots(
    tracked_page_id: int,
    user_id: int,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> list[SnapshotRead]:
    try:
        return await service.get_all_snapshots(user_id=user_id, tracked_page_id=tracked_page_id)

    except TrackedPageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/tracked-page/{tracked_page_id}/{snapshot_id}", response_model=SnapshotRead)
async def get_snapshot(
    tracked_page_id: int,
    snapshot_id: int,
    user_id: int,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> SnapshotRead:
    try:
        return await service.get_snapshot(
            user_id=user_id,
            tracked_page_id=tracked_page_id,
            snapshot_id=snapshot_id,
        )

    except TrackedPageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    except SnapshotNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/tracked-page/{tracked_page_id}/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_snapshot(
    tracked_page_id: int,
    snapshot_id: int,
    user_id: int,
    service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> None:
    try:
        await service.delete_snapshot(
            user_id=user_id,
            tracked_page_id=tracked_page_id,
            snapshot_id=snapshot_id,
        )

    except TrackedPageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    except SnapshotNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
