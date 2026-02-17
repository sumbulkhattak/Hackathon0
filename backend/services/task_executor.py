"""Task Executor — executes approved actions by task type."""

import logging
import re
from datetime import datetime, timezone
from typing import Optional
import json

import config
from services.task_mover import move_task

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Raised when task execution fails."""
    pass


EXECUTOR_MAP = {
    "ORDER":     "_execute_order",
    "INQUIRY":   "_execute_inquiry",
    "INVENTORY": "_execute_inventory",
    "FILE":      "_execute_file",
    "EMAIL":     "_execute_email",
    "INVOICE":   "_execute_invoice",
    "ESCALATION": "_execute_escalation",
}


def parse_queued_actions(content: str) -> list[dict]:
    """Parse the Queued Actions table from a task file."""
    actions = []
    in_table = False
    for line in content.split("\n"):
        if "## Queued Actions" in line:
            in_table = True
            continue
        if in_table and line.startswith("|") and not line.startswith("| #") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5 and parts[0].isdigit():
                try:
                    args = json.loads(parts[3])
                except (json.JSONDecodeError, IndexError):
                    args = {}
                actions.append({
                    "server": parts[1],
                    "tool": parts[2],
                    "args": args,
                    "status": parts[4],
                })
        elif in_table and line.startswith("##") and "Queued Actions" not in line:
            break
    return actions


def _detect_type(filename: str) -> str:
    """Detect task type from filename prefix."""
    prefix = filename.split("_")[0].split("-")[0]
    return prefix.upper()


def _read_task(filename: str, queue: str = "Approved") -> str:
    """Read task file content from a queue."""
    d = config.QUEUE_DIRS.get(queue)
    if d is None:
        raise ExecutionError(f"Unknown queue: {queue}")
    path = d / filename
    if not path.exists():
        raise ExecutionError(f"Task not found: {queue}/{filename}")
    return path.read_text(encoding="utf-8")


def _move(filename: str, from_queue: str, to_queue: str, **kwargs) -> str:
    """Wrapper around task_mover.move_task."""
    return move_task(filename, from_queue, to_queue, **kwargs)


def _run_action(task_type: str, content: str, filename: str) -> dict:
    """Execute the action for a task — uses MCP servers if queued actions exist."""
    now = datetime.now(timezone.utc).isoformat()
    logger.info(f"[EXECUTOR] Running action for {task_type}: {filename}")

    # Check for MCP queued actions
    actions = parse_queued_actions(content)
    if actions:
        from database import SessionLocal
        db = SessionLocal()
        try:
            import mcp as mcp_registry
            results = []
            for action in actions:
                server = mcp_registry.get_server(action["server"], db)
                if hasattr(server, "execute_action"):
                    exec_payload = {"action": action["tool"], "args": action["args"]}
                    result = server.execute_action(exec_payload)
                else:
                    result = server.call_tool(action["tool"], action["args"])
                results.append({"tool": action["tool"], "result": result})
                status = result.get("status", "ok") if isinstance(result, dict) else "ok"
                logger.info(f"[EXECUTOR] MCP {action['server']}.{action['tool']} → {status}")
            return {
                "steps_completed": len(results),
                "executed_at": now,
                "action": "mcp_execution",
                "results": results,
            }
        finally:
            db.close()

    return {
        "steps_completed": 1,
        "executed_at": now,
        "action": f"{task_type.lower()}_action",
        "details": f"Executed {task_type} action for {filename}",
    }


def execute_task(filename: str) -> dict:
    """
    Execute an approved task:
    1. Move Approved -> Executing
    2. Run the action
    3. Success: Move Executing -> Archived
    4. Failure: Move Executing -> Pending_Approval
    """
    task_type = _detect_type(filename)

    # 1. Move to Executing
    _move(
        filename, "Approved", "Executing",
        new_status="EXECUTING",
        actor="task-executor",
        actor_type="system",
    )

    # 2. Run the action
    try:
        content = _read_task(filename, "Executing")
        result = _run_action(task_type, content, filename)

        # 3. Success -> Archived
        _move(
            filename, "Executing", "Archived",
            new_status="COMPLETED",
            actor="task-executor",
            actor_type="system",
            details=result,
        )

        logger.info(f"[EXECUTOR] {filename} completed successfully")
        return {
            "status": "COMPLETED",
            "filename": filename,
            "task_type": task_type,
            "moved_to": "Archived",
            **result,
        }

    except Exception as e:
        # 4. Failure -> back to Pending_Approval
        logger.error(f"[EXECUTOR] {filename} failed: {e}")
        try:
            _move(
                filename, "Executing", "Pending_Approval",
                new_status="PROCESSED",
                actor="task-executor",
                actor_type="system",
                details={"execution_error": str(e)},
            )
        except Exception as move_err:
            logger.error(f"[EXECUTOR] Failed to move {filename} back: {move_err}")

        return {
            "status": "FAILED",
            "filename": filename,
            "task_type": task_type,
            "moved_to": "Pending_Approval",
            "error": str(e),
        }
