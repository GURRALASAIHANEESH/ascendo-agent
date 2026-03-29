# Ascendo AI Community Jobs

Ascendo AI Community Jobs is a full-stack field service job aggregation platform built for the Ascendo assessment. It is designed to collect roles from multiple source types, normalize them into a single database, refresh them on a schedule, and present them through a searchable jobs interface with source management.

## Overview

The goal of this project is to support a community of senior field service leaders and the broader field service ecosystem with a jobs platform that can:

- aggregate jobs from external sources such as APIs, RSS feeds, and company URLs,
- refresh jobs automatically on a schedule,
- support search and seniority-based filtering,
- allow users to add and manage data sources,
- provide a clean UI for browsing opportunities.

This project is built as a real system with separate backend ingestion, database persistence, scheduler orchestration, and frontend presentation layers.

## Features

### Jobs experience
- Search jobs by title, company, and location.
- Filter by seniority level, from individual contributor to VP / C-suite.
- View salary, location, job type, tags, and direct apply links.
- See refresh context in the UI.

### Source management
- Add new sources from the frontend.
- List all configured ingestion sources.
- Trigger manual refresh for a specific source.
- Delete sources that are no longer needed.

### Backend ingestion
- Normalize jobs into a common schema.
- Support upsert-style ingestion to reduce duplicates.
- Track source metadata and ingestion runs.
- Schedule recurring refreshes.

## Current Source Adapters

The backend currently includes adapters for:

- Remotive API
- USAJobs API
- RSS feeds
- Additional free-source ingestion helpers

> Note: Live results depend on external source availability, API responses, filtering terms, and source accessibility.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Frontend | Next.js 16 + TypeScript |
| Styling | Tailwind CSS + shadcn/ui |
| Database | PostgreSQL |
| ORM | SQLAlchemy Async |
| Validation | Pydantic |
| Scheduler | APScheduler |
| API Proxy | Next.js Route Handlers |

## Architecture

```text
External Sources
   ├─ APIs
   ├─ RSS Feeds
   └─ Company URLs
        ↓
Ingestion Adapters
        ↓
Normalization Pipeline
        ↓
PostgreSQL Database
        ↓
FastAPI Jobs / Sources APIs
        ↓
Next.js UI
```

## Project Structure

```text
ascendo-jobs/
├── backend
│   ├── alembic
│   ├── app
│   │   ├── api
│   │   │   ├── jobs.py
│   │   │   └── sources.py
│   │   ├── core
│   │   │   ├── config.py
│   │   │   └── scheduler.py
│   │   ├── db
│   │   │   ├── schema.sql
│   │   │   └── session.py
│   │   ├── ingestion
│   │   │   ├── free_sources.py
│   │   │   ├── remotive.py
│   │   │   ├── rss.py
│   │   │   └── usajobs.py
│   │   ├── models
│   │   │   └── models.py
│   │   ├── pipeline
│   │   │   ├── normalizer.py
│   │   │   └── runner.py
│   │   ├── schemas
│   │   │   ├── job.py
│   │   │   └── source.py
│   │   └── main.py
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
├── frontend
│   ├── app
│   │   ├── api
│   │   │   ├── jobs
│   │   │   │   └── route.ts
│   │   │   └── sources
│   │   │       ├── [id]
│   │   │       │   ├── refresh
│   │   │       │   │   └── route.ts
│   │   │       │   └── route.ts
│   │   │       └── route.ts
│   │   ├── sources
│   │   │   └── page.tsx
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components
│   │   ├── ui
│   │   ├── JobBoard.tsx
│   │   ├── JobCard.tsx
│   │   └── SearchBar.tsx
│   ├── lib
│   │   ├── api.ts
│   │   └── utils.ts
│   └── package.json
├── .gitignore
└── README.md
```

## Local Setup

## 1) Clone the repository

```bash
git clone https://github.com/GURRALASAIHANEESH/ascendo-agent.git
cd ascendo-agent
```

## 2) Start PostgreSQL

If you are using Docker:

```powershell
docker run --name ascendo-postgres `
  -e POSTGRES_USER=ascendo `
  -e POSTGRES_PASSWORD=ascendo_pass `
  -e POSTGRES_DB=ascendo_jobs `
  -p 5434:5432 `
  -d postgres:16
```

If the container already exists but is stopped:

```powershell
docker start ascendo-postgres
```

## 3) Backend setup

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://ascendo:ascendo_pass@localhost:5434/ascendo_jobs
```

Optional environment values may be needed depending on which adapters you use, for example third-party API credentials.

Start the backend:

```powershell
uvicorn app.main:app --reload --port 8001
```

Or from the repository root:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8001
```

## 4) Frontend setup

```powershell
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

Start the frontend:

```powershell
npm run dev
```

Open:

- Frontend: `http://localhost:3000` or the next available port
- Backend docs: `http://localhost:8001/docs`

## API Endpoints

### Jobs
- `GET /jobs` — list jobs with optional search and filter parameters

### Sources
- `GET /sources` — list configured sources
- `POST /sources` — create a new source
- `POST /sources/{source_id}/refresh` — trigger manual ingestion for one source
- `DELETE /sources/{source_id}` — delete a source

### Health
- `GET /health` — backend health check

## Example Source Payload

```json
{
  "name": "Remotive Field Service Jobs",
  "source_type": "api",
  "url": "https://remotive.com/api/remote-jobs?search=field+service",
  "config": {},
  "fetch_interval_minutes": 60
}
```

## What This Project Demonstrates

- Full-stack product development with FastAPI and Next.js
- Async database access with SQLAlchemy
- Background job scheduling
- Source-driven ingestion architecture
- Schema normalization for heterogeneous job inputs
- Operational source management from the UI

## Assessment Context

This project was built for an Ascendo assessment centered on a field service jobs agent for a community of senior field service leaders. The intended product direction is a jobs intelligence platform that can grow through community-added sources, periodic refreshes, and broad field service role coverage.

## Known Limitations

- Some external sources may block requests or return no matching jobs depending on search terms.
- Live job volume depends on source availability and adapter behavior.
- Source quality and coverage vary across APIs and RSS feeds.
- Additional tuning may be needed to improve field-service-specific recall.

## Suggested Next Improvements

- Add ingestion run history UI.
- Add job detail pages.
- Add pagination and sorting options.
- Add observability for refresh success/failure by source.
- Improve source validation before saving.
- Add authentication and saved-job workflows.
- Add richer ranking and relevance logic for field service roles.

## GitHub Push

From the repository root:

```powershell
git init
git remote add origin https://github.com/GURRALASAIHANEESH/ascendo-agent.git
git add .
git commit -m "Initial commit: Ascendo AI Community Jobs"
git branch -M main
git push -u origin main
```

If Git asks for authentication, use a GitHub Personal Access Token instead of your account password.

## Author

Built by GURRALA SAI HANEESH !! 