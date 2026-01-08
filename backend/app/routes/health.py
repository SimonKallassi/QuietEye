from fastapi import APIRouter
from ..db import db_ping

router = APIRouter()

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "quieteye-backend",
        "db_ok": db_ping()
    }
