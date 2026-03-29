from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class JobRead(BaseModel):
    id: UUID
    title: str
    company: str
    location: str | None
    job_type: str | None
    seniority: str | None
    description: str | None
    apply_url: str | None
    salary_raw: str | None
    salary_min: float | None
    salary_max: float | None
    salary_currency: str
    tags: list[str]
    first_seen_at: datetime
    last_seen_at: datetime
    posted_at: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}


class JobFilters(BaseModel):
    search: str | None = None
    seniority: str | None = None    # 'ic' | 'senior' | 'lead' | 'director' | 'vp'
    location: str | None = None
    job_type: str | None = None
    page: int = 1
    page_size: int = 20