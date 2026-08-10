from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SnapshotRead(BaseModel):
    id: int
    tracked_page_id: int
    content_hash: str
    content_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
