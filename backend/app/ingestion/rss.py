import feedparser
import httpx
from datetime import datetime
from email.utils import parsedate_to_datetime


async def fetch_rss_jobs(source_id: str, url: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url)
        response.raise_for_status()
        content = response.text

    feed = feedparser.parse(content)
    results = []

    for entry in feed.entries:
        results.append({
            "title": entry.get("title", "").strip(),
            "company": _extract_company(entry, feed),
            "location": entry.get("location") or entry.get("georss_point") or None,
            "job_type": None,
            "description": entry.get("summary", "")[:5000],
            "apply_url": entry.get("link"),
            "salary_raw": None,
            "tags": [t.term for t in entry.get("tags", [])],
            "posted_at": _parse_rss_date(entry),
            "source_id": source_id,
        })

    return results


def _extract_company(entry: dict, feed: dict) -> str:
    # Some RSS feeds put company in author, some in feed title
    return (
        entry.get("author")
        or entry.get("dc_creator")
        or feed.feed.get("title")
        or "Unknown"
    ).strip()


def _parse_rss_date(entry: dict) -> datetime | None:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        return None