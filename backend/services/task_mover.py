"""Task Mover — safe write-then-delete file moves between vault folders."""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import config
from services import audit

logger = logging.getLogger(__name__)


class TaskMoveError(Exception):
    """Raised when a task move fails."""
    pass


def _resolve_dir(queue: str) -> Path:
    """Resolve queue name to directory path."""
    d = config.QUEUE_DIRS.get(queue)
    if d is None:
        raise TaskMoveError(f"Unknown queue: {queue}")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _audit_transition(
    task_id: str,
    task_type: str,
    from_status: str,
    to_status: str,
    from_folder: str,
    to_folder: str,
    actor: str,
    actor_type: str,
    details: Optional[dict] = None,
) -> None:
    """Write audit entries for a state transition."""
    audit.write_audit_entry(
        source="task-mover",
        action=f"task.{to_status.lower()}",
        entity_type=task_type.lower(),
        entity_id=task_id,
        actor=actor,
        details={
            **(details or {}),
            "from_status": from_status,
            "to_status": to_status,
            "from_folder": from_folder,
            "to_folder": to_folder,
            "actor_type": actor_type,
        },
        queue=to_folder,
        status=to_status,
    )
    audit.append_daily_log(
        source="task-mover",
        action=f"Task {to_status.capitalize()}",
        details=f"{task_id}: {from_folder} -> {to_folder} by {actor} ({actor_type})",
        status=to_status,
    )


def _update_status_line(content: str, new_status: str) -> str:
    """Replace ## Status: OLD with ## Status: NEW in task content."""
    updated = re.sub(
        r'(## Status:\s*)\w+',
        f'\\1{new_status}',
        content,
    )
    return updated


def _append_folder_history(content: str, folder: str) -> str:
    """Append a folder_history entry to the task content."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"\n> Moved to **{folder}** at {now}\n"
    return content + entry


def move_task(
    filename: str,
    from_queue: str,
    to_queue: str,
    new_status: str,
    actor: str,
    actor_type: str,
    details: Optional[dict] = None,
) -> str:
    """
    Safely move a task file between folders using write-then-delete.
    Returns the new file path. Raises TaskMoveError on failure.
    """
    src_dir = _resolve_dir(from_queue)
    dst_dir = _resolve_dir(to_queue)
    src_path = src_dir / filename
    dst_path = dst_dir / filename

    # 1. Read source
    if not src_path.exists():
        raise TaskMoveError(f"Task file not found: {from_queue}/{filename}")

    content = src_path.read_text(encoding="utf-8")
    old_status = "UNKNOWN"
    status_match = re.search(r'## Status:\s*(\w+)', content)
    if status_match:
        old_status = status_match.group(1)

    # 2. Update status
    content = _update_status_line(content, new_status)

    # 3. Append folder history
    content = _append_folder_history(content, to_queue)

    # 4. Write to destination
    try:
        dst_path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise TaskMoveError(f"Failed to write to {to_queue}/{filename}: {e}")

    # 5. Verify destination
    if not dst_path.exists():
        raise TaskMoveError(f"Verification failed: {to_queue}/{filename} not found after write")

    # 6. Delete source
    try:
        src_path.unlink()
    except Exception as e:
        logger.error(f"Failed to delete source {from_queue}/{filename}: {e}. Destination written OK.")

    # 7. Audit
    task_type = filename.split("_")[0].split("-")[0]
    _audit_transition(
        task_id=filename,
        task_type=task_type,
        from_status=old_status,
        to_status=new_status,
        from_folder=from_queue,
        to_folder=to_queue,
        actor=actor,
        actor_type=actor_type,
        details=details,
    )

    logger.info(f"[MOVER] {filename}: {from_queue}({old_status}) -> {to_queue}({new_status})")
    return str(dst_path)
