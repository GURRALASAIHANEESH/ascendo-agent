import hashlib
import re
from datetime import datetime
from typing import Any


SENIORITY_RULES = [
    (["chief", "cto", "ceo", "coo", "vp ", "vice president"], "c-suite"),
    (["director"], "director"),
    (["lead", "principal", "staff"], "lead"),
    (["senior", "sr."], "senior"),
    (["manager"], "manager"),
    (["intern", "junior", "jr."], "junior"),
]


def detect_seniority(title: str) -> str:
    t = title.lower()
    for keywords, level in SENIORITY_RULES:
        if any(k in t for k in keywords):
            return level
    return "ic"


def compute_fingerprint(title: str, company: str, location: str) -> str:
    key = f"{title.lower().strip()}|{company.lower().strip()}|{(location or '').lower().strip()}"
    return hashlib.sha256(key.encode()).hexdigest()


def _make_json_safe(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable types in a dict."""
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def normalize_job(raw: dict[str, Any], source_id: str) -> dict[str, Any]:
    title = (raw.get("title") or "").strip()
    company = (raw.get("company") or "").strip()
    location = (raw.get("location") or "").strip() or None

    if not title or not company:
        raise ValueError(f"Job missing required fields: title='{title}' company='{company}'")

    return {
        "fingerprint": compute_fingerprint(title, company, location or ""),
        "title": title,
        "company": company,
        "location": location,
        "job_type": raw.get("job_type"),
        "seniority": detect_seniority(title),
        "description": (raw.get("description") or "")[:5000],
        "apply_url": raw.get("apply_url"),
        "salary_raw": raw.get("salary_raw"),
        "tags": raw.get("tags") or [],
        "posted_at": raw.get("posted_at"),
        "source_ids": [source_id],
        "raw": _make_json_safe(raw),
    }