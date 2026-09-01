from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.page_status import PageStatus


def normalize_url(raw_url: str) -> str:
    value = raw_url.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must include scheme and domain, for example https://example.com")

    netloc = parsed.netloc.lower().rstrip("/")
    if parsed.path in ("", "/"):
        path = "" if not parsed.query else "/"
    else:
        path = parsed.path.rstrip("/")
    query = parsed.query
    fragment = ""
    return parsed._replace(netloc=netloc, path=path, query=query, fragment=fragment).geturl()


class TrackedPageCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return normalize_url(value)


class TrackedPageRead(BaseModel):
    id: int
    url: str = Field(min_length=1, max_length=2048)
    title: str | None = None
    status: PageStatus
    created_at: datetime
    last_checked_at: datetime | None = None
    last_changed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TrackedPageUpdate(BaseModel):
    status: PageStatus
