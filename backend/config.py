"""Centralized configuration — vault paths, API keys, directory resolution."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ── Vault root ────────────────────────────────────────────────────────────────
VAULT_PATH = Path(os.getenv("VAULT_PATH", "../AI_Employee")).resolve()

# ── Queue directories (4-stage pipeline) ──────────────────────────────────────
NEEDS_ACTION_DIR = VAULT_PATH / "Needs_Action"
PENDING_APPROVAL_DIR = VAULT_PATH / "Pending_Approval"
APPROVED_DIR = VAULT_PATH / "Approved"
REJECTED_DIR = VAULT_PATH / "Rejected"

# ── Other vault directories ───────────────────────────────────────────────────
PLANS_DIR = VAULT_PATH / "Plans"
LOGS_DIR = VAULT_PATH / "Logs"
AUDIT_DIR = VAULT_PATH / "Logs" / "audit"
AGENT_SKILLS_DIR = VAULT_PATH / "Agent_Skills"
WATCHERS_DIR = VAULT_PATH / "Watchers"
MEMORY_DIR = VAULT_PATH / "Memory"
TEMPLATES_DIR = VAULT_PATH / "Templates"
CONFIG_DIR = VAULT_PATH / "Config"
ARCHIVE_DIR = VAULT_PATH / "Archive"

# ── Queue name → path mapping ─────────────────────────────────────────────────
QUEUE_DIRS = {
    "Needs_Action": NEEDS_ACTION_DIR,
    "Pending_Approval": PENDING_APPROVAL_DIR,
    "Approved": APPROVED_DIR,
    "Rejected": REJECTED_DIR,
    "Plans": PLANS_DIR,
}

# ── Claude API ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# ── Ensure all directories exist ──────────────────────────────────────────────
def ensure_vault_dirs():
    """Create all vault directories if they don't exist."""
    for d in [
        NEEDS_ACTION_DIR, PENDING_APPROVAL_DIR, APPROVED_DIR, REJECTED_DIR,
        PLANS_DIR, LOGS_DIR, AUDIT_DIR, MEMORY_DIR,
        MEMORY_DIR / "Clients", MEMORY_DIR / "Finance", MEMORY_DIR / "Projects",
        TEMPLATES_DIR, CONFIG_DIR, ARCHIVE_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
