CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── 1. SOURCES ──────────────────────────────────────────────────
-- Every ingestion source is a row here. No hardcoding in code.
CREATE TABLE sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    source_type     TEXT NOT NULL CHECK (source_type IN ('rss', 'api', 'scrape')),
    url             TEXT NOT NULL,
    config          JSONB DEFAULT '{}',     -- headers, selectors, API params
    is_active       BOOLEAN DEFAULT true,
    fetch_interval_minutes INT DEFAULT 60,
    last_fetched_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ── 2. JOBS ─────────────────────────────────────────────────────
-- Normalized job listings. Fingerprint prevents duplicates.
CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint     TEXT NOT NULL UNIQUE,   -- SHA-256 of title+company+location
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    location        TEXT,
    job_type        TEXT,                   -- 'full-time' | 'contract' | 'part-time'
    seniority       TEXT,                   -- 'ic' | 'senior' | 'lead' | 'director' | 'vp' | 'c-suite'
    description     TEXT,
    apply_url       TEXT,
    salary_raw      TEXT,                   -- keep original string, don't parse lossy
    salary_min      NUMERIC,
    salary_max      NUMERIC,
    salary_currency TEXT DEFAULT 'USD',
    tags            TEXT[] DEFAULT '{}',
    source_ids      UUID[] DEFAULT '{}',    -- which sources surfaced this job
    first_seen_at   TIMESTAMPTZ DEFAULT now(),
    last_seen_at    TIMESTAMPTZ DEFAULT now(),
    posted_at       TIMESTAMPTZ,            -- original post date if available
    is_active       BOOLEAN DEFAULT true,
    raw             JSONB DEFAULT '{}'      -- original payload, never discard
);

CREATE INDEX idx_jobs_seniority  ON jobs (seniority);
CREATE INDEX idx_jobs_location   ON jobs (location);
CREATE INDEX idx_jobs_is_active  ON jobs (is_active);
CREATE INDEX idx_jobs_last_seen  ON jobs (last_seen_at DESC);
-- Full-text search index
CREATE INDEX idx_jobs_fts ON jobs
    USING gin(to_tsvector('english', coalesce(title,'') || ' ' || coalesce(company,'') || ' ' || coalesce(description,'')));

-- ── 3. INGESTION RUNS ───────────────────────────────────────────
-- One row per scheduler tick per source. Gives full audit history.
CREATE TABLE ingestion_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    started_at      TIMESTAMPTZ DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    status          TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','success','failed')),
    jobs_fetched    INT DEFAULT 0,
    jobs_new        INT DEFAULT 0,
    jobs_updated    INT DEFAULT 0,
    error_message   TEXT
);

-- ── 4. SOURCE LOGS ──────────────────────────────────────────────
-- Per-run structured logs for debugging without touching app logs.
CREATE TABLE source_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      UUID NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
    level       TEXT NOT NULL CHECK (level IN ('info','warn','error')),
    message     TEXT NOT NULL,
    context     JSONB DEFAULT '{}',
    logged_at   TIMESTAMPTZ DEFAULT now()
);