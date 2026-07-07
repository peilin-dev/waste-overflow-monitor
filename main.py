"""
Application entry point.

Run:    uvicorn main:app --reload
Open:   http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import Base, async_engine

# Import models so SQLAlchemy registers them
from models import block, bin, user, cleaner_block, task, role, attendance      # noqa: F401

# Import routers
from routers import blocks as blocks_router
from routers import bins as bins_router
from routers import users as users_router
from routers import auth as auth_router
from routers import cleaners as cleaners_router
from routers import tasks as tasks_router
from routers import roles as roles_router
from routers import attendance as attendance_router
app = FastAPI(
    docs_url="/docs",
    redoc_url=None,
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend for the Smart Community Waste Overflow Monitoring System",
)

@app.on_event("startup")
async def startup():
    """Auto-create all tables on first launch."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# CORS — origins configured via settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router.router)
app.include_router(blocks_router.router)
app.include_router(bins_router.router)
app.include_router(users_router.router)
app.include_router(cleaners_router.router)
app.include_router(tasks_router.router)
app.include_router(roles_router.router)
app.include_router(attendance_router.router)
@app.get("/", tags=["health"])
async def root():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }