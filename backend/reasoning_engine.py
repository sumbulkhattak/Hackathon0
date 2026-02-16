"""
AI Employee Reasoning Engine — Perception → Reasoning → Planning pipeline.

Watches Needs_Action/ for new task files, consults the Company Handbook and
Agent Skills, then generates structured Plan.md files in Plans/.

Usage:
    python reasoning_engine.py                    # Watch mode (continuous)
    python reasoning_engine.py --once             # Process current tasks, then exit
    python reasoning_engine.py --dry-run          # Log pipeline, don't write files
    python reasoning_engine.py --log-level DEBUG  # Verbose logging
"""

import argparse
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

import config
from services import vault, audit

logger = logging.getLogger("reasoning_engine")

# Files to skip
SKIP_FILES = {"README.md"}

# Task type → Agent Skill file mapping
SKILL_MAP = {
    "ORDER": "order_processing.md",
    "INQUIRY": "respond_to_inquiry.md",
    "INVENTORY-ALERT": "inventory_monitor.md",
    "ESCALATION": "reasoning_engine.md",
    "FILE-UPLOAD": "reasoning_engine.md",
    "EMAIL": "send_email.md",
    "INVOICE": "generate_invoice.md",
    "LISTING": "update_product_listing.md",
}


# ── Claude API ────────────────────────────────────────────────────────────────

def _call_claude(system_prompt: str, user_prompt: str) -> str:
    """Call the Claude API and return the response text."""
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_task_type(filename: str) -> str:
    """Detect task type from filename prefix."""
    if filename.startswith("ORDER-"):
        return "ORDER"
    if filename.startswith("INQUIRY_"):
        return "INQUIRY"
    if filename.startswith("INVENTORY-ALERT"):
        return "INVENTORY-ALERT"
    if filename.startswith("ESCALATION-"):
        return "ESCALATION"
    if filename.startswith("FILE-UPLOAD"):
        return "FILE-UPLOAD"
    if filename.startswith("EMAIL-"):
        return "EMAIL"
    if filename.startswith("INVOICE-"):
        return "INVOICE"
    if filename.startswith("LISTING-"):
        return "LISTING"
    return "UNKNOWN"


def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    return slug.strip('-')[:50]


def _should_skip(filename: str, content: str) -> bool:
    """Check if a task file should be skipped."""
    if filename in SKIP_FILES:
        return True
    if filename.startswith("PLAN-"):
        return True
    # Skip already-processed tasks
    if "## Status: PROCESSED" in content or "## Status: PLANNED" in content:
        return True
    return False


def _load_client_context(metadata: dict) -> str:
    """Try to load client memory if customer name is in metadata."""
    customer = metadata.get("Customer", "")
    if not customer or customer in ("Unknown", "N/A", ""):
        return ""
    slug = _slugify(customer)
    try:
        content = vault.read_memory_file("Clients", f"{slug}.md")
        return f"\n=== CLIENT HISTORY ===\n{content}\n"
    except FileNotFoundError:
        return f"\n=== CLIENT HISTORY ===\nNo previous records for {customer}.\n"


# ── Pipeline Stages ──────────────────────────────────────────────────────────

def stage_perception(filename: str) -> dict:
    """Stage 1: Read the task, parse metadata, load context."""
    logger.info(f"[PERCEPTION] Reading task: {filename}")

    content = vault.read_task_file("Needs_Action", filename)

    if _should_skip(filename, content):
        logger.debug(f"[PERCEPTION] Skipping: {filename}")
        return {"skip": True}

    metadata = vault.parse_task_metadata(content)
    task_type = _detect_task_type(filename)

    # Load matching agent skill
    skill_file = SKILL_MAP.get(task_type, "reasoning_engine.md")
    skill_content = vault.read_agent_skill(skill_file)

    # Load client context
    client_context = _load_client_context(metadata)

    # Load reasoning engine skill (always included)
    reasoning_skill = vault.read_agent_skill("reasoning_engine.md")

    perception = {
        "skip": False,
        "filename": filename,
        "content": content,
        "metadata": metadata,
        "task_type": task_type,
        "skill_content": skill_content,
        "reasoning_skill": reasoning_skill,
        "client_context": client_context,
        "priority": metadata.get("Priority", "Medium"),
        "customer": metadata.get("Customer", "N/A"),
        "task_type_label": metadata.get("Task Type", task_type),
        "source": metadata.get("Source", "unknown"),
    }

    logger.info(
        f"[PERCEPTION] Type={task_type} | Priority={perception['priority']} | Customer={perception['customer']}"
    )
    return perception


def stage_reasoning(perception: dict) -> str:
    """Stage 2: Consult Company Handbook + skills, call Claude for analysis."""
    logger.info(f"[REASONING] Analyzing: {perception['filename']}")

    handbook = vault.read_company_handbook()

    system_prompt = f"""You are the Royal Sparkle AI Employee Reasoning Engine. Your job is to analyze incoming tasks and produce structured action plans.

You follow a strict pipeline: Perception → Reasoning → Planning.

=== COMPANY HANDBOOK ===
{handbook}

=== TASK-SPECIFIC SKILL ===
{perception['skill_content']}

=== REASONING ENGINE SKILL ===
{perception['reasoning_skill']}

INSTRUCTIONS:
You will receive a task file from the Needs_Action queue. You must produce a structured plan with exactly these 5 sections:

1. **Perception (What We Know)** — Structured metadata table summarizing key facts
2. **Reasoning (Analysis)** — Your analysis: which handbook rules apply, priority justification, escalation check, recommended approach
3. **Action Plan** — Numbered steps, each with: title, action, owner (AI/Human), SLA
4. **Risks & Considerations** — Bullet list of what could go wrong
5. **Success Criteria** — Checkbox list of how to verify the plan succeeded

Be specific. Reference handbook sections. Never fabricate data not in the task file.
"""

    user_prompt = f"""Analyze this task and generate a structured plan.

=== TASK FILE: {perception['filename']} ===
{perception['content']}

=== PARSED METADATA ===
Task Type: {perception['task_type']}
Priority: {perception['priority']}
Customer: {perception['customer']}
{perception['client_context']}

Generate the 5-section plan now. Use Markdown formatting.
"""

    try:
        response = _call_claude(system_prompt, user_prompt)
        logger.info(f"[REASONING] Claude analysis complete ({len(response)} chars)")
        return response
    except Exception as e:
        logger.error(f"[REASONING] Claude API failed: {e}")
        # Retry once after 30 seconds
        logger.info("[REASONING] Retrying in 30 seconds...")
        time.sleep(30)
        try:
            response = _call_claude(system_prompt, user_prompt)
            logger.info(f"[REASONING] Retry succeeded ({len(response)} chars)")
            return response
        except Exception as e2:
            logger.error(f"[REASONING] Retry failed: {e2}")
            raise


def stage_planning(perception: dict, reasoning_output: str, dry_run: bool = False) -> dict:
    """Stage 3: Write Plan.md to Plans/, annotate source task, update dashboard."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    now_display = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build plan slug from task type + customer or filename
    slug_source = perception['customer'] if perception['customer'] not in ("N/A", "Unknown", "") else perception['task_type']
    slug = _slugify(slug_source)
    plan_filename = f"PLAN-{slug}_{timestamp}.md"

    # Build the full plan document
    plan_content = f"""# Plan: {perception['task_type_label']} — {perception['customer']}

> **Plan ID:** {plan_filename.removesuffix('.md')}
> **Source Task:** {perception['filename']}
> **Created:** {now_display}
> **Priority:** {perception['priority']}
> **Pipeline:** Perception → Reasoning → Planning

---

{reasoning_output}

---

> Auto-generated by Royal Sparkle AI Reasoning Engine.
"""

    if dry_run:
        logger.info(f"[PLANNING] [DRY RUN] Would create: {plan_filename}")
        logger.info(f"[PLANNING] [DRY RUN] Plan content ({len(plan_content)} chars)")
        return {"plan_filename": plan_filename, "dry_run": True}

    # Write plan to Plans/
    logger.info(f"[PLANNING] Writing plan: {plan_filename}")
    plan_path = vault.write_task_file("Plans", plan_filename, plan_content)

    # Annotate the source task with a planning note
    try:
        source_content = vault.read_task_file("Needs_Action", perception['filename'])
        annotation = f"""

---

## Planning Note

**Plan Created:** {now_display}
**Plan File:** [{plan_filename}](../Plans/{plan_filename})
**Pipeline:** Perception → Reasoning → Planning

## Status: PLANNED
"""
        vault.write_task_file("Needs_Action", perception['filename'], source_content + annotation)
        logger.info(f"[PLANNING] Annotated source task: {perception['filename']}")
    except Exception as e:
        logger.warning(f"[PLANNING] Failed to annotate source task: {e}")

    # Audit logging
    audit.write_audit_entry(
        source="reasoning-engine",
        action="plan.created",
        entity_type=perception['task_type'].lower(),
        entity_id=plan_filename,
        details={
            "source_task": perception['filename'],
            "task_type": perception['task_type'],
            "priority": perception['priority'],
            "customer": perception['customer'],
        },
        queue="Plans",
        status="COMPLETED",
    )
    audit.append_daily_log(
        source="reasoning-engine",
        action="Plan Created",
        details=f"{plan_filename} for {perception['filename']} ({perception['task_type']})",
        status="COMPLETED",
    )

    # Refresh dashboard
    _refresh_dashboard()

    return {"plan_filename": plan_filename, "plan_path": plan_path, "dry_run": False}


# ── Dashboard refresh ─────────────────────────────────────────────────────────

def _refresh_dashboard():
    """Refresh Dashboard.md with current state."""
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


# ── Full pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(filename: str, dry_run: bool = False) -> dict | None:
    """Execute the full Perception → Reasoning → Planning pipeline for one task."""
    start_time = time.time()

    # Stage 1: Perception
    perception = stage_perception(filename)
    if perception.get("skip"):
        return None

    # Stage 2: Reasoning
    try:
        reasoning_output = stage_reasoning(perception)
    except Exception as e:
        logger.error(f"[PIPELINE] Reasoning failed for {filename}: {e}")
        audit.write_audit_entry(
            source="reasoning-engine",
            action="plan.failed",
            entity_type=perception['task_type'].lower(),
            entity_id=filename,
            status="ERROR",
            error=str(e),
        )
        return None

    # Stage 3: Planning
    result = stage_planning(perception, reasoning_output, dry_run=dry_run)

    duration = int((time.time() - start_time) * 1000)
    logger.info(
        f"[PIPELINE] Complete: {filename} → {result['plan_filename']} ({duration}ms)"
    )
    return result


# ── Process existing tasks (--once mode) ──────────────────────────────────────

def process_existing_tasks(dry_run: bool = False):
    """Process all current tasks in Needs_Action/ once."""
    tasks = vault.list_task_files("Needs_Action")
    logger.info(f"[ONCE] Found {len(tasks)} files in Needs_Action/")

    processed = 0
    for task in tasks:
        filename = task["filename"]
        # Quick pre-check before reading content
        if filename in SKIP_FILES or filename.startswith("PLAN-"):
            continue

        try:
            content = vault.read_task_file("Needs_Action", filename)
            if _should_skip(filename, content):
                logger.debug(f"[ONCE] Skipping (already processed): {filename}")
                continue
        except FileNotFoundError:
            continue

        result = run_pipeline(filename, dry_run=dry_run)
        if result:
            processed += 1

    logger.info(f"[ONCE] Processed {processed} tasks.")


# ── Watchdog handler ──────────────────────────────────────────────────────────

class NeedsActionHandler(FileSystemEventHandler):
    """Watches Needs_Action/ for new .md task files."""

    def __init__(self, dry_run: bool = False):
        super().__init__()
        self.dry_run = dry_run

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix.lower() != ".md":
            return

        # Delay to let the file finish writing
        time.sleep(1)

        filename = file_path.name
        logger.info(f"[WATCH] New task detected: {filename}")

        try:
            run_pipeline(filename, dry_run=self.dry_run)
        except Exception as e:
            logger.error(f"[WATCH] Pipeline error for {filename}: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Royal Sparkle AI Reasoning Engine — Perception → Reasoning → Planning"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the pipeline without writing plan files",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process all current Needs_Action tasks once, then exit",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging verbosity (default: INFO)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    config.ensure_vault_dirs()

    mode_label = "DRY RUN" if args.dry_run else "LIVE"
    logger.info(f"Reasoning Engine starting ({mode_label})")
    logger.info(f"Vault: {config.VAULT_PATH}")

    if args.once:
        logger.info("Mode: --once (process existing tasks, then exit)")
        process_existing_tasks(dry_run=args.dry_run)
        return

    # Watch mode
    watch_dir = config.NEEDS_ACTION_DIR
    logger.info(f"Watching: {watch_dir}")
    logger.info(f"Plans output: {config.PLANS_DIR}")

    handler = NeedsActionHandler(dry_run=args.dry_run)
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()

    try:
        logger.info("Reasoning Engine is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Reasoning Engine...")
        observer.stop()
    observer.join()
    logger.info("Reasoning Engine stopped.")


if __name__ == "__main__":
    main()
