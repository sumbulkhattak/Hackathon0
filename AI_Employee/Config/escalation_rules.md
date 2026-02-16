# Agent Configuration — Escalation Rules

> **Last Updated:** 2026-02-16
> **Scope:** Checked by every skill before completing a task.

---

## Auto-Escalate Triggers

| Trigger | Urgency | Routing |
|---------|---------|---------|
| Customer uses angry/threatening language | HIGH | `ESCALATION-TONE_{timestamp}.md` |
| Refund request >= 2,000 | MEDIUM | `ESCALATION-REFUND_{timestamp}.md` |
| Legal mention (lawyer, court, consumer forum) | URGENT | `ESCALATION-LEGAL_{timestamp}.md` |
| Product safety concern (allergy, injury) | URGENT | `ESCALATION-SAFETY_{timestamp}.md` |
| Repeat complaint (same customer, 3+ times) | HIGH | `ESCALATION-REPEAT_{timestamp}.md` |
| Social media complaint (1000+ followers) | HIGH | `ESCALATION-SOCIAL_{timestamp}.md` |
| Custom/bulk order request | MEDIUM | `ESCALATION-BULK_{timestamp}.md` |
| Task stale > 24 hours | MEDIUM | `ESCALATION-STALE_{timestamp}.md` |

## Escalation File Format

```markdown
# Escalation: {TYPE}

> **Urgency:** {URGENT / HIGH / MEDIUM}
> **Created:** {YYYY-MM-DD HH:MM:SS}
> **Source:** {skill/watcher that triggered this}

## Customer
- **Name:** {name}
- **Email:** {email}
- **Order(s):** {order IDs if applicable}

## Context
{What happened — 2-3 sentences}

## History
{Previous interactions, complaints, or orders if relevant}

## AI Recommendation
{What the AI would do if it had authority}

## Required Action
{What the human needs to decide}
```

## Escalation Destination

All escalation files are created in `Needs_Action/` with the `ESCALATION-` prefix.
They bypass normal AI processing and surface directly for human attention.
