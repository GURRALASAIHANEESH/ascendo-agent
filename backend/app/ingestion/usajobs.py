import httpx
from datetime import datetime

USAJOBS_API_URL = "https://data.usajobs.gov/api/search"
USAJOBS_EMAIL = "ascendo@test.com"
USAJOBS_API_KEY = "guEuMcsd2lpWJ2l7maP/eyPkj9iFvbXmMWM4BTqsMvM="

# Strict field service titles only
FIELD_SERVICE_KEYWORDS = [
    "field service technician",
    "field service engineer",
    "field service representative",
    "field technician",
    "field engineer",
    "field operations",
    "maintenance technician",
    "maintenance engineer",
    "service technician",
    "hvac technician",
    "hvac engineer",
    "elevator technician",
    "biomedical technician",
    "medical equipment technician",
    "field support engineer",
    "field support technician",
    "equipment technician",
    "industrial technician",
    "electromechanical technician",
    "field service manager",
    "director of field service",
    "vice president field service",
    "service operations manager", 
]

SEARCH_TERMS = [
    "field service technician",
    "field service engineer",
    "maintenance technician",
    "hvac technician",
    "field technician",
]


async def fetch_usajobs_jobs(source_id: str) -> list[dict]:
    results = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for term in SEARCH_TERMS:
            try:
                response = await client.get(
                    USAJOBS_API_URL,
                    headers={
                        "Host": "data.usajobs.gov",
                        "User-Agent": USAJOBS_EMAIL,
                        "Authorization-Key": USAJOBS_API_KEY,
                    },
                    params={
                        "Keyword": term,
                        "ResultsPerPage": 25,
                        "Fields": "minimum",
                    },
                )
                response.raise_for_status()
                data = response.json()

                items = (
                    data.get("SearchResult", {})
                    .get("SearchResultItems", [])
                )

                print(f"[USAJobs] Term='{term}' → {len(items)} raw results")

                for item in items:
                    obj = item.get("MatchedObjectDescriptor", {})
                    job_id = item.get("MatchedObjectId", "")

                    if job_id in seen_ids:
                        continue

                    title = obj.get("PositionTitle", "")

                    # Strict title match
                    if not _is_field_service(title):
                        continue

                    seen_ids.add(job_id)

                    locations = obj.get("PositionLocation", [])
                    location = locations[0].get("LocationName", "USA") if locations else "USA"

                    salary_range = obj.get("PositionRemuneration", [{}])
                    salary_min = salary_range[0].get("MinimumRange") if salary_range else None
                    salary_max = salary_range[0].get("MaximumRange") if salary_range else None
                    salary_raw = f"${salary_min} - ${salary_max}" if salary_min and salary_max else None

                    results.append({
                        "title": title,
                        "company": obj.get("OrganizationName", "US Government"),
                        "location": location,
                        "job_type": "full_time",
                        "description": obj.get("UserArea", {})
                                         .get("Details", {})
                                         .get("JobSummary", ""),
                        "apply_url": obj.get("ApplyURI", [""])[0],
                        "salary_raw": salary_raw,
                        "tags": ["government", "field service", term],
                        "posted_at": _parse_date(obj.get("PublicationStartDate")),
                        "source_id": source_id,
                    })

            except Exception as e:
                print(f"[USAJobs] Error on term '{term}': {e}")
                continue

    print(f"[USAJobs] Total matched field service jobs: {len(results)}")
    return results


def _is_field_service(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in FIELD_SERVICE_KEYWORDS)


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None