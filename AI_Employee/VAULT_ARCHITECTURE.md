# Royal Sparkle AI Employee — Vault Architecture

> **Version:** 1.0.0
> **Date:** 2026-02-16
> **Type:** Obsidian Markdown Vault — Local-First Autonomous FTE

---

## 1. Complete Folder Tree

```
AI_Employee/                          ← Obsidian Vault Root
│
├── Dashboard.md                      ← Real-time system health & queue summary
├── Company_Handbook.md               ← Brand rules, tone, policies, SLAs
├── VAULT_ARCHITECTURE.md             ← This file — structure reference
│
├── Needs_Action/                     ← Inbox: unprocessed tasks
│   ├── README.md                     ← Queue rules, prefixes, SLA tiers
│   ├── ORDER-1_2026-02-16_12-21-57.md
│   ├── INQUIRY_2026-02-16_12-21-27.md
│   └── INVENTORY-ALERT_2026-02-16_12-21-30.md
│
├── Pending_Approval/                 ← AI-processed, awaiting human review
│   └── README.md                     ← Review checklist and SLA
│
├── Approved/                         ← Human-approved, ready for execution
│   └── README.md                     ← Post-approval actions, archival rules
│
├── Rejected/                         ← Human-rejected with feedback
│   └── README.md                     ← Rejection format, reprocessing rules
│
├── Plans/                            ← Reports, proposals, strategic plans
│   └── README.md                     ← File types and schedule
│
├── Logs/                             ← Activity logs (Markdown daily + JSON audit)
│   ├── LOG_2026-02-16.md             ← Human-readable daily activity
│   └── audit/                        ← Machine-readable JSON audit trail
│       └── AUDIT_2026-02-16.jsonl    ← JSONL audit entries (90-day retention)
│
├── Agent_Skills/                     ← Skill modules (what the AI can do)
│   ├── order_processing.md           ← Skill: process orders
│   ├── inquiry_reply.md              ← Skill: draft customer replies
│   ├── inventory_monitor.md          ← Skill: monitor & restock inventory
│   └── daily_reporting.md            ← Skill: compile daily metrics
│
├── Watchers/                         ← Event listeners (what triggers tasks)
│   ├── new_order_watcher.md          ← Watch: incoming orders
│   ├── low_stock_watcher.md          ← Watch: post-order stock check
│   └── inquiry_watcher.md            ← Watch: customer inquiries
│
├── Scheduled_Tasks/                  ← Cron-like recurring jobs
│   ├── daily_revenue_summary.md      ← 11:00 PM IST — daily report
│   ├── morning_stock_scan.md         ← 9:00 AM IST — stock sweep
│   ├── weekly_performance_report.md  ← Monday 9:00 AM IST — weekly rollup
│   └── pending_task_review.md        ← Every 4 hours — stale task check
│
├── Memory/                           ← Persistent knowledge base
│   ├── Clients/                      ← Customer profiles & interaction history
│   │   └── README.md                 ← File format, VIP rules
│   ├── Finance/                      ← Revenue, suppliers, cost tracking
│   │   └── README.md                 ← Structure, supplier template
│   └── Projects/                     ← Campaigns, launches, initiatives
│       └── README.md                 ← Project template, archival rules
│
├── Templates/                        ← Reusable file templates
│   ├── task_order.md                 ← Template: new order task
│   ├── task_inquiry.md               ← Template: new inquiry task
│   ├── task_inventory_alert.md       ← Template: inventory alert task
│   ├── task_escalation.md            ← Template: escalation task
│   ├── reply_product_availability.md ← Template: product inquiry reply
│   ├── reply_order_status.md         ← Template: order status reply
│   ├── reply_return_request.md       ← Template: return/exchange reply
│   ├── report_daily.md              ← Template: daily report
│   ├── report_weekly.md             ← Template: weekly report
│   └── client_profile.md            ← Template: new client memory file
│
├── Archive/                          ← Completed & expired items
│   ├── Approved/                     ← Approved tasks older than 30 days
│   ├── Rejected/                     ← Rejected tasks older than 30 days
│   └── Logs/                         ← Audit logs older than 90 days
│
└── Config/                           ← Agent configuration
    ├── thresholds.md                 ← Inventory thresholds, SLA timers
    ├── escalation_rules.md           ← Escalation triggers & routing
    └── retention_policy.md           ← Data retention & archival rules
```

---

## 2. Purpose of Each Folder

### Root Files

| File | Purpose |
|------|---------|
| `Dashboard.md` | Single-pane-of-glass view. System health, queue counts, today's metrics, active watchers, recent actions, workflow diagram. Auto-maintained by the agent after every action. |
| `Company_Handbook.md` | The AI's "brain" for brand identity, communication tone, customer service policies, product knowledge, escalation rules, and decision authority. Every output must conform to this. |
| `VAULT_ARCHITECTURE.md` | Structural reference. Documents folder purposes, naming conventions, and data flow. |

### Workflow Queues (The 4-Stage Pipeline)

| Folder | Stage | Owner | Purpose |
|--------|-------|-------|---------|
| `Needs_Action/` | 1. Intake | AI | Unprocessed tasks land here from watchers and triggers. The AI picks them up by priority (CRITICAL > HIGH > MEDIUM > LOW) and processes them using the matching skill. |
| `Pending_Approval/` | 2. Review | Human | AI-completed work awaiting human review. Contains drafted replies, restock plans, processed orders. Human approves or rejects. |
| `Approved/` | 3. Execute | System | Human-approved items. Replies get sent, orders get dispatched, plans get executed. Archived after 30 days. |
| `Rejected/` | 4. Feedback | AI | Human-rejected items with a rejection note. If marked `reprocess`, the task returns to `Needs_Action/` with feedback so the AI can learn and retry. |

### Operational Folders

| Folder | Purpose |
|--------|---------|
| `Plans/` | Output destination for reports and proposals. Daily reports (`DAILY-REPORT_`), weekly rollups (`WEEKLY-REPORT_`), monthly reviews (`MONTHLY-REPORT_`), strategic proposals (`PLAN-`), and restock plans (`RESTOCK-`). Reports are informational; proposals require review before execution. |
| `Logs/` | **Dual-format activity log.** `LOG_{date}.md` files are human-readable daily activity tables viewable in Obsidian. `audit/AUDIT_{date}.jsonl` files are machine-readable JSON Lines for programmatic analysis, alerting, and compliance. 90-day retention on audit logs; daily logs retained indefinitely. |
| `Agent_Skills/` | Skill definitions — the AI's capabilities. Each `.md` file defines: trigger, input format, step-by-step execution logic, templates, error handling, and output. Adding a new skill = adding a new `.md` file here. |
| `Watchers/` | Event listener definitions. Each watcher monitors a specific trigger (order placed, stock changed, inquiry received) and creates task files in `Needs_Action/`. Defines monitoring scope, thresholds, deduplication rules, and log format. |
| `Scheduled_Tasks/` | Cron-like job definitions. Each file specifies: schedule (time/frequency), skill used, execution steps, dependencies, and output destination. The orchestrator reads these to fire jobs on schedule. |

### Knowledge Base

| Folder | Purpose |
|--------|---------|
| `Memory/Clients/` | One file per customer. Stores contact info, order history, preferences, interaction notes, and tags (VIP, returning, complaint-history). Updated after every order and inquiry. Never stores payment details. |
| `Memory/Finance/` | Financial knowledge: daily revenue snapshots, supplier contacts and pricing, refund tracking, operational costs. Subdirectories for `daily/` snapshots. Updated by the daily-reporting skill and inventory-monitor skill. |
| `Memory/Projects/` | Active campaigns, product launches, improvement initiatives. One file per project with status, timeline, tasks, and notes. Reviewed weekly; archived after 30 days post-completion. |

### Supporting Folders

| Folder | Purpose |
|--------|---------|
| `Templates/` | Reusable file templates for tasks, replies, reports, and client profiles. The agent stamps these when creating new files, ensuring consistent structure. Editing a template changes future output format globally. |
| `Archive/` | Cold storage. `Archive/Approved/` holds approved tasks older than 30 days. `Archive/Rejected/` holds rejected tasks older than 30 days. `Archive/Logs/` holds audit JSON older than 90 days. Preserves training data and compliance trail without cluttering active folders. |
| `Config/` | Agent configuration. Inventory thresholds, SLA timers, escalation routing rules, and data retention policies. Changing a value here changes agent behavior without modifying skill logic. |

---

## 3. File Naming Conventions

### General Rules

1. **UPPERCASE prefix** identifies the file type at a glance
2. **Underscore `_`** separates prefix from timestamp
3. **Hyphen `-`** separates words within a prefix or within dates/times
4. **Timestamps** use `YYYY-MM-DD_HH-MM-SS` (colons are invalid in filenames)
5. **All files are `.md`** except audit logs (`.jsonl`)
6. **Slugs** use `lowercase-kebab-case`

### Task Files (Workflow Queues)

| Type | Pattern | Example |
|------|---------|---------|
| Order | `ORDER-{id}_{YYYY-MM-DD_HH-MM-SS}.md` | `ORDER-1_2026-02-16_12-21-57.md` |
| Inquiry | `INQUIRY_{YYYY-MM-DD_HH-MM-SS}.md` | `INQUIRY_2026-02-16_12-21-27.md` |
| Inventory Alert | `INVENTORY-ALERT_{YYYY-MM-DD_HH-MM-SS}.md` | `INVENTORY-ALERT_2026-02-16_09-00-00.md` |
| Escalation | `ESCALATION-{type}_{YYYY-MM-DD_HH-MM-SS}.md` | `ESCALATION-REFUND_2026-02-16_14-30-00.md` |

### Reports & Plans

| Type | Pattern | Example |
|------|---------|---------|
| Daily Report | `DAILY-REPORT_{YYYY-MM-DD}.md` | `DAILY-REPORT_2026-02-16.md` |
| Weekly Report | `WEEKLY-REPORT_{YYYY-MM-DD}.md` | `WEEKLY-REPORT_2026-02-10.md` |
| Monthly Report | `MONTHLY-REPORT_{YYYY-MM}.md` | `MONTHLY-REPORT_2026-02.md` |
| Strategic Plan | `PLAN-{topic-slug}_{YYYY-MM-DD}.md` | `PLAN-valentines-campaign_2026-02-01.md` |
| Restock Plan | `RESTOCK-{supplier-slug}_{YYYY-MM-DD}.md` | `RESTOCK-gem-traders_2026-02-16.md` |

### Logs

| Type | Pattern | Example |
|------|---------|---------|
| Daily Activity (MD) | `LOG_{YYYY-MM-DD}.md` | `LOG_2026-02-16.md` |
| Audit Trail (JSON) | `audit/AUDIT_{YYYY-MM-DD}.jsonl` | `audit/AUDIT_2026-02-16.jsonl` |

### Memory Files

| Type | Pattern | Example |
|------|---------|---------|
| Client Profile | `Memory/Clients/{name-slug}.md` | `Memory/Clients/priya-sharma.md` |
| Supplier | `Memory/Finance/suppliers.md` | Single file, append entries |
| Project | `Memory/Projects/{project-slug}.md` | `Memory/Projects/summer-collection-launch.md` |
| Daily Finance | `Memory/Finance/daily/{YYYY-MM-DD}.md` | `Memory/Finance/daily/2026-02-16.md` |

### Configuration & Templates

| Type | Pattern | Example |
|------|---------|---------|
| Config | `Config/{setting-name}.md` | `Config/thresholds.md` |
| Template | `Templates/{type}_{purpose}.md` | `Templates/task_order.md` |

### Archive Files

Archived files retain their original name, moved into the corresponding `Archive/` subfolder:
- `Archive/Approved/ORDER-1_2026-01-15_10-30-00.md`
- `Archive/Logs/AUDIT_2025-11-15.jsonl`

---

## 4. Data Flow Summary

```
External Event (Order / Inquiry / Stock Change)
        │
        ▼
   ┌──────────┐
   │ Watchers  │  ← Detect events, validate, create task files
   └────┬─────┘
        │
        ▼
┌──────────────┐
│ Needs_Action │  ← AI processes using matching Agent_Skill
└──────┬───────┘
       │
       ├── Reads: Company_Handbook.md (tone, policy)
       ├── Reads: Memory/ (customer history, supplier data)
       ├── Uses:  Templates/ (consistent output format)
       │
       ▼
┌──────────────────┐
│ Pending_Approval  │  ← Human reviews AI work
└──────┬───────────┘
       │
  ┌────┴────┐
  │         │
  ▼         ▼
┌────────┐ ┌────────┐
│Approved│ │Rejected│  → Feedback loop back to Needs_Action
└───┬────┘ └────────┘
    │
    ├── Logged: Logs/ (daily MD + audit JSONL)
    ├── Updated: Dashboard.md
    └── Archived: Archive/ (after retention period)
```

```
Scheduled_Tasks (Cron)
        │
        ▼
   Agent_Skills execute on schedule
        │
        ├── Daily: revenue summary → Plans/
        ├── Daily: stock scan → Needs_Action/ (if critical)
        ├── Weekly: performance report → Plans/
        └── 4-hourly: stale task check → Escalation
```

---

## 5. JSON Audit Log Format

Each line in `audit/AUDIT_{date}.jsonl` is a self-contained JSON object:

```json
{
  "id": "aud_20260216_122127_001",
  "timestamp": "2026-02-16T12:21:27Z",
  "source": "watcher/inquiry",
  "action": "task.created",
  "entity_type": "inquiry",
  "entity_id": "INQUIRY_2026-02-16_12-21-27",
  "actor": "ai-employee",
  "details": {
    "customer": "Priya Sharma",
    "subject": "Delivery Timeline",
    "priority": "MEDIUM"
  },
  "queue": "Needs_Action",
  "status": "PENDING",
  "duration_ms": null,
  "error": null
}
```

### Audit Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique audit ID: `aud_{date}_{time}_{seq}` |
| `timestamp` | ISO 8601 | When the action occurred |
| `source` | string | Origin: `watcher/*`, `skill/*`, `schedule/*`, `human/*`, `system` |
| `action` | string | What happened: `task.created`, `task.processed`, `task.approved`, `task.rejected`, `task.archived`, `report.generated`, `escalation.triggered` |
| `entity_type` | string | `order`, `inquiry`, `inventory`, `escalation`, `report`, `plan` |
| `entity_id` | string | Reference to the task filename |
| `actor` | string | `ai-employee`, `human:{name}`, `system` |
| `details` | object | Action-specific payload |
| `queue` | string | Current queue: `Needs_Action`, `Pending_Approval`, `Approved`, `Rejected`, `Archive` |
| `status` | string | Outcome: `PENDING`, `COMPLETED`, `FAILED`, `ESCALATED` |
| `duration_ms` | number | Processing time (null for instant actions) |
| `error` | string | Error message if failed (null otherwise) |

### Retention Policy

| Log Type | Retention | Archive Action |
|----------|-----------|----------------|
| Daily MD (`LOG_*.md`) | Indefinite | None — lightweight, human reference |
| Audit JSONL (`AUDIT_*.jsonl`) | 90 days active | Move to `Archive/Logs/` after 90 days |
| Archived Audit | 1 year | Delete after 1 year |

---

## 6. Obsidian-Specific Notes

- **All cross-references use `[[wikilinks]]`** for Obsidian graph navigation
- **Tags** use `#tag` format in frontmatter or inline for filtering
- **Dashboard.md** is set as the vault's homepage via Obsidian settings
- **Dataview plugin** can query task files across queues using frontmatter
- **Templater plugin** can stamp files from `Templates/` on creation
- The vault is **fully offline** — no cloud sync required for core operation
- Git-backed for version history and collaboration

---

> This architecture is designed so the AI Employee operates as a full-time equivalent:
> it watches, acts, drafts, logs, and escalates — but a human always has final approval.
