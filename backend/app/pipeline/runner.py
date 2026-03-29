from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.models import Job, IngestionRun, Source, SourceLog
from app.pipeline.normalizer import normalize_job
from app.ingestion.remotive import fetch_remotive_jobs
from app.ingestion.rss import fetch_rss_jobs


async def run_ingestion(source_id: str, db: AsyncSession) -> IngestionRun:
    # Load source
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source or not source.is_active:
        raise ValueError(f"Source {source_id} not found or inactive")

    # Open ingestion run
    run = IngestionRun(source_id=source.id, status="running")
    db.add(run)
    await db.flush()

    jobs_fetched = 0
    jobs_new = 0
    jobs_updated = 0

    try:
        # Fetch raw jobs from the right adapter
        raw_jobs = await _fetch(source)
        jobs_fetched = len(raw_jobs)

        for raw in raw_jobs:
            try:
                normalized = normalize_job(raw, str(source.id))
            except ValueError as e:
                await _log(db, run.id, "warn", str(e), {"raw": raw})
                continue

            # Upsert: insert or update on fingerprint conflict
            stmt = insert(Job).values(**normalized)
            stmt = stmt.on_conflict_do_update(
                index_elements=["fingerprint"],
                set_={
                    "last_seen_at": datetime.now(timezone.utc),
                    "source_ids": Job.source_ids + normalized["source_ids"],
                    "is_active": True,
                }
            )
            result = await db.execute(stmt)

            if result.inserted_primary_key is not None:
                jobs_new += 1
            else:
                jobs_updated += 1

        # Mark source as fetched
        source.last_fetched_at = datetime.now(timezone.utc)

        run.status = "success"
        run.finished_at = datetime.now(timezone.utc)
        run.jobs_fetched = jobs_fetched
        run.jobs_new = jobs_new
        run.jobs_updated = jobs_updated

        await _log(db, run.id, "info", f"Completed: {jobs_new} new, {jobs_updated} updated")

    except Exception as e:
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = str(e)
        await _log(db, run.id, "error", str(e))

    await db.commit()
    return run


async def _fetch(source: Source) -> list[dict]:
    if source.source_type == "api" and "remotive" in source.url:
        return await fetch_remotive_jobs(str(source.id))

    elif source.source_type == "api" and "usajobs" in source.url:
        from app.ingestion.usajobs import fetch_usajobs_jobs
        return await fetch_usajobs_jobs(str(source.id))

    elif source.source_type == "rss":
        return await fetch_rss_jobs(str(source.id), source.url)

    else:
        raise NotImplementedError(f"No adapter for source_type='{source.source_type}'")


async def _log(db: AsyncSession, run_id, level: str, message: str, context: dict = {}):
    log = SourceLog(run_id=run_id, level=level, message=message, context=context)
    db.add(log)
    await db.flush()