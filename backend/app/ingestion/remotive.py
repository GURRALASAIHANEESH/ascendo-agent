import httpx
from datetime import datetime
from app.core.config import settings


FIELD_SERVICE_KEYWORDS = [
    "field service",
    "field engineer",
    "field technician",
    "field operations",
    "service technician",
    "service manager",
    "maintenance engineer",
    "hvac",
    "elevator technician",
    "medical device",
    "biomedical",
    "fse",
    "field support",
    "aftermarket",
    "service operations",
    "vice president of service",
    "vp of service",
    "director of service",
    "service leader",
]


REMOTIVE_CATEGORIES = [
    "software-dev",
    "devops-sysadmin",
    "customer-support",
    "all"
]


async def fetch_remotive_jobs(source_id: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            settings.REMOTIVE_API_URL,
            params={"limit": 100},
        )
        response.raise_for_status()
        data = response.json()

    jobs = data.get("jobs", [])
    results = []

    print(f"[Remotive] Total jobs fetched from API: {len(jobs)}")

    for job in jobs:
        title = (job.get("title") or "").lower()

        if not any(kw in title for kw in FIELD_SERVICE_KEYWORDS):
            continue

        results.append({
            "title": job.get("title"),
            "company": job.get("company_name"),
            "location": job.get("candidate_required_location") or "Remote",
            "job_type": job.get("job_type"),
            "description": job.get("description"),
            "apply_url": job.get("url"),
            "salary_raw": job.get("salary"),
            "tags": job.get("tags") or [],
            "posted_at": _parse_date(job.get("publication_date")),
            "source_id": source_id,
        })

    print(f"[Remotive] Jobs after keyword filter: {len(results)}")
    return results


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None