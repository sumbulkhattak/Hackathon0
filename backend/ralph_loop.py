"""
Ralph Wiggum Loop — The AI Employee's main event loop.

Continuously monitors all 6 pipeline folders:
  Phase 1: Scan Needs_Action/ -> AI process -> Pending_Approval/
  Phase 2: Approval gate (human decides, loop waits)
  Phase 3: Execute Approved/ -> Executing/ -> Archived/
  Phase 4: Watchdog — recover stale Executing/ tasks
  Phase 5: Memory update — sync client profiles
  Phase 6: Status heartbeat — dashboard + audit

Usage:
    python ralph_loop.py                  # Run forever, 30s interval
    python ralph_loop.py --interval 10    # Faster polling
    python ralph_loop.py --once           # Single cycle, then exit
    python ralph_loop.py --dry-run        # Log only, no writes
"""

import argparse
import logging
import signal
import sys
import time
import re
from datetime import datetime, timezone
from pathlib import Path

import config
from config import ensure_vault_dirs
from services import vault, audit
from services.retry_tracker import RetryTracker
from services.task_executor import execute_task
from services.task_mover import move_task
from services.execution_watchdog import check_stale_executions

logger = logging.getLogger("ralph_loop")

SKIP_FILES = {"README.md"}


def _list_tasks(directory: Path) -> list[str]:
    """List .md task files in a directory, excluding README."""
    if not directory.exists():
        return []
    return [
        f.name for f in sorted(directory.glob("*.md"), key=lambda p: p.stat().st_mtime)
        if f.name not in SKIP_FILES
    ]


def _extract_customer(content: str) -> dict:
    """Extract customer info from task file content."""
    customer = {}
    for field in ["Customer", "Email", "Phone", "Address"]:
        match = re.search(rf'\*\*{field}\*\*\s*\|\s*(.+?)\s*\|', content)
        if match:
            customer[field.lower()] = match.group(1).strip()
    return customer


class RalphWiggumLoop:
    """The AI Employee's main event loop."""

    def __init__(self, poll_interval: int = 30, max_retries: int = 5, dry_run: bool = False):
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.retry_tracker = RetryTracker(max_retries=max_retries)
        self.loop_count = 0
        self.alive = True
        self.start_time = time.time()
        self.total_processed = 0
        self.total_executed = 0
        self.total_failed = 0

    def run(self):
        """Main entry point. Blocks forever (or until stopped)."""
        ensure_vault_dirs()
        logger.info(
            f"Ralph Wiggum Loop started "
            f"(interval={self.poll_interval}s, max_retries={self.max_retries}, "
            f"dry_run={self.dry_run})"
        )
        while self.alive:
            try:
                self.cycle()
            except Exception as e:
                logger.error(f"Cycle {self.loop_count} failed: {e}")
            if self.alive:
                time.sleep(self.poll_interval)
        logger.info("Ralph Wiggum Loop stopped.")

    def cycle(self):
        """One full scan of all folders."""
        self.loop_count += 1
        logger.info(f"--- Cycle #{self.loop_count} ---")
        processed = self.phase_scan_and_process()
        self.phase_approval_gate()
        completed = self.phase_execute()
        self.phase_watchdog()
        self.phase_memory_update(completed)
        self.phase_status_heartbeat()

    def stop(self):
        """Graceful shutdown."""
        self.alive = False
        logger.info("Shutdown requested. Finishing current cycle...")

    # -- Phase 1: Scan & Process --

    def phase_scan_and_process(self) -> list[str]:
        """Scan Needs_Action/ and AI-process each task."""
        tasks = _list_tasks(config.NEEDS_ACTION_DIR)
        processed = []

        for task_id in tasks:
            if self.retry_tracker.should_skip(task_id):
                logger.debug(f"[SCAN] Skipping {task_id} (in backoff)")
                continue

            if self.retry_tracker.is_exhausted(task_id):
                logger.warning(f"[SCAN] {task_id} exhausted retries, moving to Rejected/")
                if not self.dry_run:
                    try:
                        move_task(
                            task_id, "Needs_Action", "Rejected",
                            new_status="REJECTED",
                            actor="ralph-loop",
                            actor_type="system",
                            details={"reason": f"Max retries ({self.max_retries}) exceeded"},
                        )
                        self.retry_tracker.clear(task_id)
                    except Exception as e:
                        logger.error(f"[SCAN] Failed to reject {task_id}: {e}")
                continue

            if self.dry_run:
                logger.info(f"[DRY-RUN] Would process: {task_id}")
                processed.append(task_id)
                continue

            try:
                from database import SessionLocal
                db = SessionLocal()
                try:
                    from services.ai_processor import process_task as ai_process
                    result = ai_process(task_id, db)
                    processed.append(task_id)
                    self.total_processed += 1
                    self.retry_tracker.clear(task_id)
                    logger.info(f"[SCAN] Processed: {task_id}")
                finally:
                    db.close()
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "authentication" in error_msg.lower():
                    logger.critical(f"[SCAN] Auth failure — stopping loop: {e}")
                    self.alive = False
                    return processed
                self.retry_tracker.record_failure(task_id, error_msg)
                self.total_failed += 1

        return processed

    # -- Phase 2: Approval Gate --

    def phase_approval_gate(self) -> int:
        """Count pending approvals. Human decides — loop does nothing."""
        tasks = _list_tasks(config.PENDING_APPROVAL_DIR)
        count = len(tasks)
        if count > 0:
            logger.info(f"[GATE] Awaiting approval: {count} task(s)")
        return count

    # -- Phase 3: Execute --

    def phase_execute(self) -> list[dict]:
        """Execute all approved tasks."""
        tasks = _list_tasks(config.APPROVED_DIR)
        completed = []

        for task_id in tasks:
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would execute: {task_id}")
                completed.append({"filename": task_id, "status": "DRY_RUN"})
                continue

            try:
                result = execute_task(task_id)
                completed.append(result)
                if result.get("status") == "COMPLETED":
                    self.total_executed += 1
                    logger.info(f"[EXEC] Completed: {task_id}")
                else:
                    self.total_failed += 1
                    logger.warning(f"[EXEC] Failed: {task_id} — {result.get('error', 'unknown')}")
            except Exception as e:
                self.total_failed += 1
                logger.error(f"[EXEC] Error executing {task_id}: {e}")

        return completed

    # -- Phase 4: Watchdog --

    def phase_watchdog(self) -> list[dict]:
        """Recover stale tasks from Executing/."""
        if self.dry_run:
            return []
        recovered = check_stale_executions()
        for r in recovered:
            logger.warning(f"[WATCHDOG] Recovered: {r['filename']}")
        return recovered

    # -- Phase 5: Memory Update --

    def phase_memory_update(self, completed: list[dict] = None) -> None:
        """Update client memory for completed tasks."""
        if completed is None:
            completed = []
        if self.dry_run or not completed:
            return

        for task_result in completed:
            if task_result.get("status") != "COMPLETED":
                continue
            filename = task_result.get("filename", "")
            try:
                content = vault.read_task_file("Archived", filename)
                customer = _extract_customer(content)
                if not customer.get("customer"):
                    continue

                slug = customer["customer"].lower().replace(" ", "-")
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                task_type = filename.split("_")[0].split("-")[0]

                try:
                    existing = vault.read_memory_file("Clients", f"{slug}.md")
                    entry = f"\n| {today} | {task_type} | {filename} — COMPLETED |"
                    vault.write_memory_file("Clients", f"{slug}.md", existing + entry)
                except FileNotFoundError:
                    new_profile = f"""# Client: {customer.get('customer', 'Unknown')}

| Field | Value |
|-------|-------|
| **Email** | {customer.get('email', '—')} |
| **Phone** | {customer.get('phone', '—')} |

## Interaction History

| Date | Type | Summary |
|------|------|---------|
| {today} | {task_type} | {filename} — COMPLETED |
"""
                    vault.write_memory_file("Clients", f"{slug}.md", new_profile)
                logger.info(f"[MEMORY] Updated: {slug}")
            except Exception as e:
                logger.warning(f"[MEMORY] Failed to update for {filename}: {e}")

    # -- Phase 6: Status Heartbeat --

    def phase_status_heartbeat(self) -> None:
        """Update dashboard and log heartbeat."""
        try:
            counts = vault.get_queue_counts()

            audit.write_audit_entry(
                source="ralph-loop",
                action="loop.heartbeat",
                entity_type="system",
                entity_id=f"cycle-{self.loop_count}",
                actor="ralph-loop",
                details={
                    "cycle": self.loop_count,
                    "queues": counts,
                    "uptime_seconds": int(time.time() - self.start_time),
                    "totals": {
                        "processed": self.total_processed,
                        "executed": self.total_executed,
                        "failed": self.total_failed,
                    },
                    "retry_queue": len(self.retry_tracker.get_all()),
                },
                status="RUNNING",
            )

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

            if self.loop_count % 10 == 0:
                uptime = int(time.time() - self.start_time)
                retries = self.retry_tracker.get_all()
                logger.info(
                    f"\n{'='*50}\n"
                    f"Ralph Wiggum Loop — Cycle #{self.loop_count} Summary\n"
                    f"{'='*50}\n"
                    f"Uptime:          {uptime // 60}m {uptime % 60}s\n"
                    f"Total processed: {self.total_processed}\n"
                    f"Total executed:  {self.total_executed}\n"
                    f"Total failed:    {self.total_failed}\n"
                    f"Retry queue:     {len(retries)} task(s)\n"
                    f"---\n"
                    + "\n".join(f"  {q}: {c}" for q, c in counts.items())
                    + f"\n{'='*50}"
                )
        except Exception as e:
            logger.warning(f"[HEARTBEAT] Failed: {e}")


# -- CLI --

def main():
    parser = argparse.ArgumentParser(description="Ralph Wiggum Loop — AI Employee event loop")
    parser.add_argument("--interval", type=int, default=config.POLL_INTERVAL, help="Polling interval in seconds")
    parser.add_argument("--max-retries", type=int, default=config.MAX_RETRIES, help="Max retry attempts per task")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--dry-run", action="store_true", help="Log only, no writes")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    loop = RalphWiggumLoop(
        poll_interval=args.interval,
        max_retries=args.max_retries,
        dry_run=args.dry_run,
    )

    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}")
        loop.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if args.once:
        ensure_vault_dirs()
        loop.cycle()
        logger.info("Single cycle complete.")
    else:
        loop.run()


if __name__ == "__main__":
    main()
