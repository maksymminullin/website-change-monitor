from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.enums.page_status import PageStatus
from app.models.base import Base


class TrackedPage(Base):
    __tablename__ = "tracked_pages"

    __table_args__ = (UniqueConstraint("user_id", "url", name="uq_tracked_pages_user_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    requires_js: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PageStatus] = mapped_column(
        String(50), default=PageStatus.ACTIVE, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
