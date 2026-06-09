"""
Application entry point.

Run:    uvicorn main:app --reload
Open:   http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings

# Import models so SQLAlchemy registers them
from models import blocks  # noqa: F401

# Import routers
from routers import blocks as blocks_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend for the Smart Community Waste Overflow Monitoring System",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(blocks_router.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }