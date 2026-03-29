from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import Source
from app.pipeline.runner import run_ingestion

scheduler = AsyncIOScheduler(timezone="UTC")


async def _job_task(source_id: str):
    async with AsyncSessionLocal() as db:
        await run_ingestion(source_id, db)


async def register_source(source_id: str, interval_minutes: int):
    scheduler.add_job(
        _job_task,
        trigger=IntervalTrigger(minutes=interval_minutes),
        args=[source_id],
        id=source_id,
        replace_existing=True,
    )


async def unregister_source(source_id: str):
    if scheduler.get_job(source_id):
        scheduler.remove_job(source_id)


async def bootstrap_scheduler():
    """Load all active sources from DB and register their tasks on startup."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Source).where(Source.is_active == True)
        )
        sources = result.scalars().all()

    for source in sources:
        await register_source(str(source.id), source.fetch_interval_minutes)

    scheduler.start()