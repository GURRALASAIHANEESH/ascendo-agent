from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import Source
from app.schemas.source import SourceCreate, SourceRead
from app.core.scheduler import register_source, unregister_source
from app.pipeline.runner import run_ingestion

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=SourceRead, status_code=201)
async def add_source(payload: SourceCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Source).where(Source.url == payload.url)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Source with this URL already exists")

    source = Source(**payload.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    await register_source(str(source.id), source.fetch_interval_minutes)
    return source


@router.post("/{source_id}/refresh", status_code=200)
async def refresh_source(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    run = await run_ingestion(source_id, db)
    return {
        "status": run.status,
        "jobs_fetched": run.jobs_fetched,
        "jobs_new": run.jobs_new,
        "jobs_updated": run.jobs_updated,
        "error": run.error_message,
    }


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await unregister_source(source_id)
    await db.delete(source)
    await db.commit()