from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrackedPageCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        result = urlparse(value)
        if result.scheme not in {"http", "https"} or not result.netloc:
            raise ValueError("URL must include scheme and domain, for example https://example.com")
        return value


class TrackedPageRead(BaseModel):
    id: int
    url: str = Field(min_length=1, max_length=2048)
    title: str | None = None
    status: str
    created_at: datetime
    last_checked_at: datetime | None = None
    last_changed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TrackedPageUpdate(BaseModel):
    status: Literal["active", "archived"]
