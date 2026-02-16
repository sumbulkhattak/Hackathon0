"""Audit Service — JSONL audit trail + daily Markdown logs."""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger(__name__)


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _next_audit_id(date_str: str) -> str:
    """Generate next sequential audit ID for a given date."""
    audit_file = config.AUDIT_DIR / f"AUDIT_{date_str}.jsonl"
    if audit_file.exists():
        lines = [l for l in audit_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
        count = len(lines) + 1
    else:
        count = 1
    ts = datetime.now(timezone.utc).strftime("%H%M%S")
    return f"aud_{date_str.replace('-', '')}_{ts}_{count:03d}"


# ── Write audit entry (JSONL) ────────────────────────────────────────────────

def write_audit_entry(
    source: str,
    action: str,
    entity_type: str,
    entity_id: str,
    actor: str = "ai-employee",
    details: Optional[dict] = None,
    queue: Optional[str] = None,
    status: str = "PENDING",
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
) -> dict:
    """Append a JSONL entry to Logs/audit/AUDIT_{date}.jsonl."""
    config.AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    date_str = _today_str()
    audit_id = _next_audit_id(date_str)

    entry = {
        "id": audit_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor": actor,
        "details": details or {},
        "queue": queue,
        "status": status,
        "duration_ms": duration_ms,
        "error": error,
    }

    audit_file = config.AUDIT_DIR / f"AUDIT_{date_str}.jsonl"
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    logger.info(f"[AUDIT] {action} | {entity_type}/{entity_id} | {status}")
    return entry


# ── Append daily log (Markdown table) ────────────────────────────────────────

def append_daily_log(
    source: str,
    action: str,
    details: str,
    status: str = "PENDING",
) -> None:
    """Append a row to Logs/LOG_{date}.md table."""
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = _today_str()
    log_file = config.LOGS_DIR / f"LOG_{date_str}.md"
    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

    if not log_file.exists():
        header = f"""# Daily Log — {date_str}

| Time (UTC) | Source | Action | Details | Status |
|------------|--------|--------|---------|--------|
"""
        log_file.write_text(header, encoding="utf-8")

    row = f"| {now_str} | {source} | {action} | {details} | {status} |\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(row)


# ── Read / filter audit entries ───────────────────────────────────────────────

def read_audit_entries(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action_filter: Optional[str] = None,
    entity_type_filter: Optional[str] = None,
) -> list[dict]:
    """Read and filter JSONL audit entries."""
    config.AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    if date:
        dates = [date]
    elif start_date and end_date:
        dates = _date_range(start_date, end_date)
    else:
        dates = [_today_str()]

    entries = []
    for d in dates:
        audit_file = config.AUDIT_DIR / f"AUDIT_{d}.jsonl"
        if not audit_file.exists():
            continue
        for line in audit_file.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if action_filter and entry.get("action") != action_filter:
                continue
            if entity_type_filter and entry.get("entity_type") != entity_type_filter:
                continue
            entries.append(entry)

    return entries


def _date_range(start: str, end: str) -> list[str]:
    """Generate a list of date strings between start and end (inclusive)."""
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    dates = []
    current = s
    while current <= e:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


# ── Today's summary ──────────────────────────────────────────────────────────

def get_today_summary() -> dict:
    """Aggregate today's audit entries by action/type/status."""
    entries = read_audit_entries(date=_today_str())

    summary = {
        "date": _today_str(),
        "total_entries": len(entries),
        "by_action": {},
        "by_entity_type": {},
        "by_status": {},
        "completed": 0,
        "pending": 0,
        "errors": 0,
        "orders": 0,
        "inquiries": 0,
        "alerts": 0,
    }

    for e in entries:
        action = e.get("action", "unknown")
        etype = e.get("entity_type", "unknown")
        status = e.get("status", "unknown")

        summary["by_action"][action] = summary["by_action"].get(action, 0) + 1
        summary["by_entity_type"][etype] = summary["by_entity_type"].get(etype, 0) + 1
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

        if status == "COMPLETED":
            summary["completed"] += 1
        elif status == "PENDING":
            summary["pending"] += 1
        if e.get("error"):
            summary["errors"] += 1
        if etype == "order":
            summary["orders"] += 1
        elif etype == "inquiry":
            summary["inquiries"] += 1
        elif etype == "inventory":
            summary["alerts"] += 1

    return summary
