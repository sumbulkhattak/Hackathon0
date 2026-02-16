# Watcher: Customer Inquiry

> **Watcher ID:** customer-inquiry
> **Type:** Real-time
> **Trigger:** Inquiry submission
> **Endpoint:** `POST /trigger/inquiry`
> **Status:** ACTIVE

---

## Configuration

| Setting | Value |
|---------|-------|
| Monitor | All incoming customer inquiries |
| Auto-trigger | Immediately on submission |
| Task Prefix | `INQUIRY_` |
| Destination | `Needs_Action/` |
| SLA | Reply draft within 4 hours |

## Behavior

1. Customer submits inquiry (email, contact form, etc.)
2. System fires `/trigger/inquiry` with customer details and message
3. Task file created in `Needs_Action/`
4. `inquiry-reply` skill picks up the task
5. Draft reply created in `Pending_Approval/`

## Priority Escalation

| Keyword in Subject/Message | Priority Override |
|---------------------------|-------------------|
| "urgent", "emergency" | High |
| "refund", "return" | Medium-High |
| "complaint", "disappointed" | High (check escalation rules) |
| "lawyer", "legal", "consumer forum" | URGENT (auto-escalate) |

## Log Format

```
[{timestamp}] WATCHER:inquiry | From: {name} <{email}> | Subject: {subject} | Priority: {level}
```
