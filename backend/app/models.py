from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    event_type: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    site_id: Mapped[str] = mapped_column(String(128), index=True)
    device_id: Mapped[str] = mapped_column(String(128), index=True)
    camera_id: Mapped[str] = mapped_column(String(128), index=True)
    zone: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    confidence: Mapped[float] = mapped_column(Float)
    snapshot_ref: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    extra: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
