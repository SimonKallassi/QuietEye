from fastapi import APIRouter
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, Literal

router = APIRouter(prefix="/v1", tags=["events"])

EventType = Literal[
    "AFTER_HOURS_PRESENCE",
    "PERSON_IN_RESTRICTED_ZONE",
    "SMOKING_IN_RESTRICTED_ZONE",
    "FIRE_DETECTED",
    "FIRE_IN_RESTRICTED_ZONE",
    "ATTENDANCE_CHECKIN",
]

class EventIn(BaseModel):
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    site_id: str
    device_id: str
    camera_id: str
    zone: Optional[str] = None

    confidence: float = Field(ge=0.0, le=1.0)
    snapshot_ref: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)

@router.post("/events")
def ingest_event(payload: EventIn):
    # MVP stub: later we'll store to Postgres
    return {"accepted": True, "event": payload.model_dump()}
