from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel, HttpUrl, field_validator

class SourceCreate(BaseModel):
    name: str
    source_type: str  # 'rss' | 'api' | 'scrape'
    url: str
    config: dict[str, Any] = {}
    fetch_interval_minutes: int = 60

    @field_validator("source_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"rss", "api", "scrape"}
        if v not in allowed:
            raise ValueError(f"source_type must be one of {allowed}")
        return v

    @field_validator("fetch_interval_minutes")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        if v < 15:
            raise ValueError("Minimum fetch interval is 15 minutes")
        return v


class SourceRead(BaseModel):
    id: UUID
    name: str
    source_type: str
    url: str
    config: dict[str, Any]
    is_active: bool
    fetch_interval_minutes: int
    last_fetched_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}