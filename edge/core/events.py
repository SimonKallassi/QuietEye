from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

EventType = Literal[
    "AFTER_HOURS_PRESENCE",
    "PERSON_IN_RESTRICTED_ZONE",
    "SMOKING_IN_RESTRICTED_ZONE",
    "FIRE_DETECTED",
    "FIRE_IN_RESTRICTED_ZONE",
    "ATTENDANCE_CHECKIN",
]

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class QuietEyeEvent(BaseModel):
    # Mirror backend schema (keep in sync!)
    event_type: EventType
    timestamp: datetime = Field(default_factory=utc_now)

    site_id: str
    device_id: str
    camera_id: str
    zone: Optional[str] = None

    confidence: float = Field(ge=0.0, le=1.0)
    snapshot_ref: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)
