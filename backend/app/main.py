from fastapi import FastAPI
from .routes.health import router as health_router
from .routes.events import router as events_router

app = FastAPI(title="QuietEye Backend", version="0.1.0")

app.include_router(health_router)
app.include_router(events_router)
