"""Task Queue Routes — 7 endpoints for the 4-stage pipeline."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import TaskApproval, TaskRejection
from services import vault, audit
from services.ai_processor import process_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Tasks"])

VALID_QUEUES = ["Needs_Action", "Pending_Approval", "Approved", "Rejected", "Plans"]


# ── GET /api/tasks — List all tasks ──────────────────────────────────────────

@router.get("/tasks")
async def list_tasks(
    queue: Optional[str] = Query(None, description="Filter by queue name"),
    task_type: Optional[str] = Query(None, alias="type", description="Filter by task type prefix"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
):
    """List all tasks across queues, with optional filters."""
    queues = [queue] if queue and queue in VALID_QUEUES else VALID_QUEUES

    all_tasks = []
    for q in queues:
        try:
            files = vault.list_task_files(q)
        except ValueError:
            continue
        for f in files:
            if task_type and not f["task_type"].startswith(task_type.upper()):
                continue
            # Read metadata for priority filtering
            if priority:
                try:
                    content = vault.read_task_file(q, f["filename"])
                    meta = vault.parse_task_metadata(content)
                    if meta.get("Priority", "").lower() != priority.lower():
                        continue
                except FileNotFoundError:
                    continue
            all_tasks.append(f)

    return {"count": len(all_tasks), "tasks": all_tasks}


# ── GET /api/tasks/{task_id} — Read task detail ─────────────────────────────

@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Read a task file's content and metadata. task_id is the filename."""
    for q in VALID_QUEUES:
        try:
            content = vault.read_task_file(q, task_id)
            metadata = vault.parse_task_metadata(content)
            return {
                "filename": task_id,
                "queue": q,
                "metadata": metadata,
                "content": content,
            }
        except FileNotFoundError:
            continue

    raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")


# ── POST /api/tasks/{task_id}/process — AI-process a Needs_Action task ──────

@router.post("/tasks/{task_id}/process")
async def process_task_endpoint(task_id: str, db: Session = Depends(get_db)):
    """Run AI processing on a task in Needs_Action."""
    # Verify task exists in Needs_Action
    try:
        vault.read_task_file("Needs_Action", task_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found in Needs_Action: {task_id}",
        )

    try:
        result = process_task(task_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    # Refresh dashboard
    _refresh_dashboard()

    return result


# ── POST /api/tasks/{task_id}/approve — Move to Approved ────────────────────

@router.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str, body: TaskApproval):
    """Approve a task in Pending_Approval — moves it to Approved."""
    try:
        content = vault.read_task_file("Pending_Approval", task_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found in Pending_Approval: {task_id}",
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    approval_note = f"""

---

## Approval

**Approved by:** {body.approved_by}
**Approved at:** {now}
"""
    if body.notes:
        approval_note += f"**Notes:** {body.notes}\n"

    approval_note += "\n## Status: APPROVED\n"

    vault.write_task_file("Pending_Approval", task_id, content + approval_note)
    vault.move_task_file(task_id, "Pending_Approval", "Approved")

    audit.write_audit_entry(
        source="api/tasks",
        action="task.approved",
        entity_type=vault._parse_filename(task_id)["task_type"].lower(),
        entity_id=task_id,
        actor=body.approved_by,
        queue="Approved",
        status="APPROVED",
    )
    audit.append_daily_log(
        source="api/tasks",
        action="Task Approved",
        details=f"{task_id} by {body.approved_by}",
        status="APPROVED",
    )

    _refresh_dashboard()

    return {"status": "approved", "filename": task_id, "moved_to": "Approved", "approved_by": body.approved_by}


# ── POST /api/tasks/{task_id}/reject — Move to Rejected ─────────────────────

@router.post("/tasks/{task_id}/reject")
async def reject_task(task_id: str, body: TaskRejection):
    """Reject a task in Pending_Approval — moves it to Rejected."""
    try:
        content = vault.read_task_file("Pending_Approval", task_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found in Pending_Approval: {task_id}",
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    rejection_note = f"""

---

## Rejection

**Rejected by:** {body.rejected_by}
**Rejected at:** {now}
**Reason:** {body.reason}
**Reprocess:** {'Yes' if body.reprocess else 'No'}

## Status: REJECTED
"""

    vault.write_task_file("Pending_Approval", task_id, content + rejection_note)
    vault.move_task_file(task_id, "Pending_Approval", "Rejected")

    audit.write_audit_entry(
        source="api/tasks",
        action="task.rejected",
        entity_type=vault._parse_filename(task_id)["task_type"].lower(),
        entity_id=task_id,
        actor=body.rejected_by,
        details={"reason": body.reason, "reprocess": body.reprocess},
        queue="Rejected",
        status="REJECTED",
    )
    audit.append_daily_log(
        source="api/tasks",
        action="Task Rejected",
        details=f"{task_id} by {body.rejected_by}: {body.reason}",
        status="REJECTED",
    )

    _refresh_dashboard()

    return {
        "status": "rejected",
        "filename": task_id,
        "moved_to": "Rejected",
        "rejected_by": body.rejected_by,
        "reprocess": body.reprocess,
    }


# ── POST /api/tasks/{task_id}/reprocess — Move Rejected → Needs_Action ──────

@router.post("/tasks/{task_id}/reprocess")
async def reprocess_task(task_id: str):
    """Move a rejected task back to Needs_Action for reprocessing."""
    try:
        content = vault.read_task_file("Rejected", task_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found in Rejected: {task_id}",
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    reprocess_note = f"""

---

## Reprocessing

**Returned to queue:** {now}
**Reason:** Marked for reprocessing after rejection

## Status: PENDING (requeued)
"""

    vault.write_task_file("Rejected", task_id, content + reprocess_note)
    vault.move_task_file(task_id, "Rejected", "Needs_Action")

    audit.write_audit_entry(
        source="api/tasks",
        action="task.reprocessed",
        entity_type=vault._parse_filename(task_id)["task_type"].lower(),
        entity_id=task_id,
        queue="Needs_Action",
        status="PENDING",
    )
    audit.append_daily_log(
        source="api/tasks",
        action="Task Requeued",
        details=f"{task_id} → Needs_Action for reprocessing",
        status="PENDING",
    )

    _refresh_dashboard()

    return {"status": "requeued", "filename": task_id, "moved_to": "Needs_Action"}


# ── DELETE /api/tasks/{task_id} — Delete task ────────────────────────────────

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, queue: str = Query(..., description="Queue the task is in")):
    """Delete a task file from a specific queue."""
    if queue not in VALID_QUEUES:
        raise HTTPException(status_code=400, detail=f"Invalid queue: {queue}")

    deleted = vault.delete_task_file(queue, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task not found: {queue}/{task_id}")

    audit.write_audit_entry(
        source="api/tasks",
        action="task.deleted",
        entity_type=vault._parse_filename(task_id)["task_type"].lower(),
        entity_id=task_id,
        queue=queue,
        status="DELETED",
    )
    audit.append_daily_log(
        source="api/tasks",
        action="Task Deleted",
        details=f"{task_id} from {queue}",
        status="DELETED",
    )

    _refresh_dashboard()

    return {"status": "deleted", "filename": task_id, "queue": queue}


# ── Helper ────────────────────────────────────────────────────────────────────

def _refresh_dashboard():
    """Refresh the vault dashboard with current counts."""
    try:
        counts = vault.get_queue_counts()
        today = audit.get_today_summary()
        recent = audit.read_audit_entries()[-5:]
        vault.update_dashboard(
            queue_counts=counts,
            recent_actions=recent,
            today_metrics={
                "completed": today.get("completed", 0),
                "pending": today.get("pending", 0),
                "inquiries": today.get("inquiries", 0),
                "orders": today.get("orders", 0),
                "alerts": today.get("alerts", 0),
            },
        )
    except Exception as e:
        logger.warning(f"Dashboard refresh failed: {e}")
