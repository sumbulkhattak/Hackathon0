"""Vault File Service — all vault I/O goes through this module."""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger(__name__)

# ── Queue helpers ─────────────────────────────────────────────────────────────

def _resolve_queue_dir(queue: str) -> Path:
    """Resolve a queue name to its directory path."""
    d = config.QUEUE_DIRS.get(queue)
    if d is None:
        raise ValueError(f"Unknown queue: {queue}")
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Task file operations ─────────────────────────────────────────────────────

def list_task_files(queue: str) -> list[dict]:
    """List .md files in a queue directory, returning metadata dicts."""
    d = _resolve_queue_dir(queue)
    files = sorted(d.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for f in files:
        info = _parse_filename(f.name)
        info["filename"] = f.name
        info["queue"] = queue
        info["size"] = f.stat().st_size
        info["modified"] = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
        results.append(info)
    return results


def _parse_filename(filename: str) -> dict:
    """Extract task type and timestamp from filename convention."""
    # ORDER-1_2026-02-16_12-21-57.md
    # INQUIRY_2026-02-16_12-21-27.md
    # INVENTORY-ALERT_2026-02-16_12-21-30.md
    # ESCALATION-complaint_2026-02-16_12-21-30.md
    name = filename.removesuffix(".md")
    parts = name.split("_", 1)
    task_type = parts[0] if parts else "UNKNOWN"
    timestamp_str = parts[1] if len(parts) > 1 else ""
    return {"task_type": task_type, "timestamp_str": timestamp_str}


def read_task_file(queue: str, filename: str) -> str:
    """Read a task file's content."""
    d = _resolve_queue_dir(queue)
    filepath = d / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Task file not found: {queue}/{filename}")
    return filepath.read_text(encoding="utf-8")


def write_task_file(queue: str, filename: str, content: str) -> str:
    """Write a task file and return its absolute path."""
    d = _resolve_queue_dir(queue)
    filepath = d / filename
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"[VAULT] Wrote {queue}/{filename}")
    return str(filepath)


def move_task_file(filename: str, from_queue: str, to_queue: str) -> str:
    """Move a task file between queues. Returns new path."""
    src_dir = _resolve_queue_dir(from_queue)
    dst_dir = _resolve_queue_dir(to_queue)
    src = src_dir / filename
    dst = dst_dir / filename
    if not src.exists():
        raise FileNotFoundError(f"Task file not found: {from_queue}/{filename}")
    src.rename(dst)
    logger.info(f"[VAULT] Moved {filename}: {from_queue} → {to_queue}")
    return str(dst)


def delete_task_file(queue: str, filename: str) -> bool:
    """Delete a task file. Returns True if deleted."""
    d = _resolve_queue_dir(queue)
    filepath = d / filename
    if not filepath.exists():
        return False
    filepath.unlink()
    logger.info(f"[VAULT] Deleted {queue}/{filename}")
    return True


# ── Task metadata parsing ────────────────────────────────────────────────────

def parse_task_metadata(content: str) -> dict:
    """Extract metadata from | **Field** | Value | tables in task files."""
    metadata = {}
    pattern = re.compile(r'\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|')
    for match in pattern.finditer(content):
        key = match.group(1).strip()
        value = match.group(2).strip()
        metadata[key] = value
    # Also extract the status line: ## Status: PENDING
    status_match = re.search(r'## Status:\s*(\w+)', content)
    if status_match:
        metadata["Status"] = status_match.group(1)
    return metadata


def generate_task_filename(task_type: str, entity_id: Optional[str] = None) -> str:
    """Generate a filename following the vault naming convention."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    if entity_id:
        return f"{task_type}-{entity_id}_{timestamp}.md"
    return f"{task_type}_{timestamp}.md"


# ── Dashboard ─────────────────────────────────────────────────────────────────

def update_dashboard(
    queue_counts: dict[str, int],
    recent_actions: list[dict],
    today_metrics: dict,
) -> str:
    """Rewrite Dashboard.md with current data."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Recent actions rows
    if recent_actions:
        action_rows = "\n".join(
            f"| {a.get('timestamp', '—')} | {a.get('action', '—')} | {a.get('status', '—')} | {a.get('entity_id', '—')} |"
            for a in recent_actions[:5]
        )
    else:
        action_rows = "| — | No actions yet | — | — |"

    content = f"""# Royal Sparkle AI Employee — Dashboard

> **Last Updated:** {now}
> **Status:** ACTIVE
> **Agent Version:** 1.0.0

---

## System Health

| Component | Status | Last Check |
|-----------|--------|------------|
| Order Processing | ONLINE | {now} |
| Inquiry Handler | ONLINE | {now} |
| Inventory Monitor | ONLINE | {now} |
| Scheduled Tasks | ONLINE | {now} |
| Memory System | ONLINE | {now} |

---

## Queue Summary

| Queue | Count | Oldest Item |
|-------|-------|-------------|
| Needs Action | {queue_counts.get('Needs_Action', 0)} | — |
| Pending Approval | {queue_counts.get('Pending_Approval', 0)} | — |
| Approved | {queue_counts.get('Approved', 0)} | — |
| Executing | {queue_counts.get('Executing', 0)} | — |
| Rejected | {queue_counts.get('Rejected', 0)} | — |
| Archived | {queue_counts.get('Archived', 0)} | — |

---

## Today's Activity

| Metric | Value |
|--------|-------|
| Tasks Completed | {today_metrics.get('completed', 0)} |
| Tasks Pending | {today_metrics.get('pending', 0)} |
| Inquiries Replied | {today_metrics.get('inquiries', 0)} |
| Orders Processed | {today_metrics.get('orders', 0)} |
| Alerts Triggered | {today_metrics.get('alerts', 0)} |

---

## Active Watchers

| Watcher | Monitoring | Interval | Status |
|---------|-----------|----------|--------|
| Low Stock Alert | Product inventory < 10 units | Every order | ACTIVE |
| New Order | Incoming orders | Real-time | ACTIVE |
| Customer Inquiry | Support inbox | Real-time | ACTIVE |
| Daily Revenue | Sales totals | Daily 11:00 PM | ACTIVE |

---

## Recent Actions Log (Last 5)

| Timestamp | Action | Result | File |
|-----------|--------|--------|------|
{action_rows}

---

## Quick Links

- [Company Handbook](./Company_Handbook.md) — Brand rules, tone, policies
- [Plans](./Plans/) — Strategic proposals and action plans
- [Agent Skills](./Agent_Skills/) — Available skill modules
- [Logs](./Logs/) — Full activity history
- [Memory](./Memory/) — Persistent knowledge base

---

> This dashboard is auto-maintained by the Royal Sparkle AI Employee System.
> For manual overrides, edit files directly in the relevant directories.
"""
    dashboard_path = config.VAULT_PATH / "Dashboard.md"
    dashboard_path.write_text(content, encoding="utf-8")
    logger.info("[VAULT] Dashboard.md updated")
    return str(dashboard_path)


def get_queue_counts() -> dict[str, int]:
    """Count .md files in each queue directory."""
    counts = {}
    for name, d in config.QUEUE_DIRS.items():
        if d.exists():
            counts[name] = len(list(d.glob("*.md")))
        else:
            counts[name] = 0
    return counts


# ── Memory operations ─────────────────────────────────────────────────────────

def list_memory_files(subfolder: str) -> list[dict]:
    """List files in a Memory/ subfolder (Clients, Finance, Projects)."""
    d = config.MEMORY_DIR / subfolder
    if not d.exists():
        return []
    files = []
    for f in sorted(d.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        files.append({
            "filename": f.name,
            "slug": f.stem,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
        })
    return files


def read_memory_file(subfolder: str, filename: str) -> str:
    """Read a memory file's content."""
    filepath = config.MEMORY_DIR / subfolder / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Memory file not found: {subfolder}/{filename}")
    return filepath.read_text(encoding="utf-8")


def write_memory_file(subfolder: str, filename: str, content: str) -> str:
    """Write a memory file. Returns absolute path."""
    d = config.MEMORY_DIR / subfolder
    d.mkdir(parents=True, exist_ok=True)
    filepath = d / filename
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"[VAULT] Wrote Memory/{subfolder}/{filename}")
    return str(filepath)


# ── Handbook / Templates / Config readers ─────────────────────────────────────

def read_company_handbook() -> str:
    """Read the Company_Handbook.md."""
    path = config.VAULT_PATH / "Company_Handbook.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_template(name: str) -> str:
    """Read a template file from Templates/."""
    path = config.TEMPLATES_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_agent_skill(name: str) -> str:
    """Read an agent skill file from Agent_Skills/."""
    path = config.AGENT_SKILLS_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_config_file(name: str) -> str:
    """Read a config file from Config/."""
    path = config.CONFIG_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def list_watcher_files() -> list[dict]:
    """List watcher definition files."""
    d = config.WATCHERS_DIR
    if not d.exists():
        return []
    return [
        {"filename": f.name, "slug": f.stem}
        for f in sorted(d.glob("*.md"))
    ]
