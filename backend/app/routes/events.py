from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal, List

from sqlalchemy import select, desc

from ..db import SessionLocal
from ..models import Event as EventRow

router = APIRouter(prefix="/v1", tags=["events"])

EventType = Literal[
    "AFTER_HOURS_PRESENCE",
    "PERSON_IN_RESTRICTED_ZONE",
    "SMOKING_IN_RESTRICTED_ZONE",
    "FIRE_DETECTED",
    "FIRE_IN_RESTRICTED_ZONE",
    "ATTENDANCE_CHECKIN",
]

def utc_now_naive() -> datetime:
    # Backend previously used naive utcnow; we accept both.
    # We'll store timezone-aware UTC going forward.
    return datetime.now(timezone.utc)

class EventIn(BaseModel):
    event_type: EventType
    timestamp: datetime = Field(default_factory=utc_now_naive)

    site_id: str
    device_id: str
    camera_id: str
    zone: Optional[str] = None

    confidence: float = Field(ge=0.0, le=1.0)
    snapshot_ref: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

class EventOut(BaseModel):
    id: int
    event_type: str
    timestamp: datetime
    site_id: str
    device_id: str
    camera_id: str
    zone: Optional[str]
    confidence: float
    snapshot_ref: Optional[str]
    extra: Dict[str, Any]

@router.post("/events", response_model=EventOut)
def ingest_event(payload: EventIn):
    # Ensure timestamp is timezone-aware UTC
    ts = payload.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    db = SessionLocal()
    try:
        row = EventRow(
            event_type=payload.event_type,
            timestamp=ts,
            site_id=payload.site_id,
            device_id=payload.device_id,
            camera_id=payload.camera_id,
            zone=payload.zone,
            confidence=float(payload.confidence),
            snapshot_ref=payload.snapshot_ref,
            extra=payload.extra,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        return EventOut(
            id=row.id,
            event_type=row.event_type,
            timestamp=row.timestamp,
            site_id=row.site_id,
            device_id=row.device_id,
            camera_id=row.camera_id,
            zone=row.zone,
            confidence=row.confidence,
            snapshot_ref=row.snapshot_ref,
            extra=row.extra or {},
        )
    finally:
        db.close()

@router.get("/events", response_model=List[EventOut])
def list_events(limit: int = Query(default=50, ge=1, le=500)):
    db = SessionLocal()
    try:
        stmt = select(EventRow).order_by(desc(EventRow.timestamp)).limit(limit)
        rows = db.execute(stmt).scalars().all()

        return [
            EventOut(
                id=r.id,
                event_type=r.event_type,
                timestamp=r.timestamp,
                site_id=r.site_id,
                device_id=r.device_id,
                camera_id=r.camera_id,
                zone=r.zone,
                confidence=r.confidence,
                snapshot_ref=r.snapshot_ref,
                extra=r.extra or {},
            )
            for r in rows
        ]
    finally:
        db.close()
