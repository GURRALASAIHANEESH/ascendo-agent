import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, Numeric, ARRAY, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def now_utc():
    return datetime.utcnow()


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=60)
    last_fetched_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc, onupdate=now_utc)

    runs: Mapped[list["IngestionRun"]] = relationship("IngestionRun", back_populates="source", cascade="all, delete")

    __table_args__ = (
        CheckConstraint("source_type IN ('rss', 'api', 'scrape')", name="ck_source_type"),
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fingerprint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text)
    job_type: Mapped[str | None] = mapped_column(String(50))
    seniority: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    apply_url: Mapped[str | None] = mapped_column(Text)
    salary_raw: Mapped[str | None] = mapped_column(Text)
    salary_min: Mapped[float | None] = mapped_column(Numeric)
    salary_max: Mapped[float | None] = mapped_column(Numeric)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD")
    tags: Mapped[list] = mapped_column(ARRAY(Text), default=list)
    source_ids: Mapped[list] = mapped_column(ARRAY(UUID(as_uuid=True)), default=list)
    first_seen_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc)
    last_seen_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc)
    posted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc)
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    jobs_fetched: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    jobs_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped["Source"] = relationship("Source", back_populates="runs")
    logs: Mapped[list["SourceLog"]] = relationship("SourceLog", back_populates="run", cascade="all, delete")


class SourceLog(Base):
    __tablename__ = "source_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="CASCADE"))
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)
    logged_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=now_utc)

    run: Mapped["IngestionRun"] = relationship("IngestionRun", back_populates="logs")