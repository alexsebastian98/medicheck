from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Bilingual medication safety platform for pharmacists and patients.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup_event() -> None:
    connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    close_mongo_connection()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
