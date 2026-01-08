from fastapi import FastAPI
from .routes.health import router as health_router
from .routes.events import router as events_router
from .db import init_db

app = FastAPI(title="QuietEye Backend", version="0.1.0")

@app.on_event("startup")
def _startup():
    init_db()

app.include_router(health_router)
app.include_router(events_router)
