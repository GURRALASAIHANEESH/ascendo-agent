from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db.session import get_db
from app.models.models import Job, IngestionRun
from app.schemas.job import JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=dict)
async def list_jobs(
    search: str | None = Query(None),
    seniority: str | None = Query(None),
    location: str | None = Query(None),
    job_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Job).where(Job.is_active == True)

    if search:
        term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Job.title).like(term),
                func.lower(Job.company).like(term),
                func.lower(Job.location).like(term),
            )
        )

    if seniority:
        stmt = stmt.where(Job.seniority == seniority)

    if location:
        stmt = stmt.where(func.lower(Job.location).like(f"%{location.lower()}%"))

    if job_type:
        stmt = stmt.where(Job.job_type == job_type)

    # total count
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    # pagination
    stmt = stmt.order_by(Job.last_seen_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    # last refresh time
    last_run = await db.execute(
        select(IngestionRun.finished_at)
        .where(IngestionRun.status == "success")
        .order_by(IngestionRun.finished_at.desc())
        .limit(1)
    )
    last_refreshed = last_run.scalar_one_or_none()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "last_refreshed": last_refreshed.isoformat() if last_refreshed else None,
        "results": [JobRead.model_validate(j) for j in jobs],
    }