from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.session import engine, Base
from app.models import models  # noqa: F401
from app.api.jobs import router as jobs_router
from app.api.sources import router as sources_router
from app.core.scheduler import scheduler, bootstrap_scheduler
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await bootstrap_scheduler()
    yield
    scheduler.shutdown()
    await engine.dispose()


app = FastAPI(
    title="Ascendo AI Community Jobs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
     allow_origins=["http://localhost:3000", "http://localhost:3002", "http://10.100.254.138:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(sources_router)


@app.get("/health")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}