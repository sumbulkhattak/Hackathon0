# Skill: Send Email

> **Skill ID:** send-email
> **Trigger:** Email action required by another skill or plan
> **Priority:** Medium–High (depends on email type)
> **SLA:** Draft within 15 minutes; send within SLA of parent task

---

## Purpose

Send transactional and customer-facing emails on behalf of Royal Sparkle. All emails follow the Company Handbook 4-Step Framework (Section 8) and must pass through the approval pipeline before dispatch.

## Inputs

| Input | Type | Required | Source | Description |
|-------|------|----------|--------|-------------|
| `recipient_email` | string | Yes | Task file / DB | Customer email address |
| `recipient_name` | string | Yes | Task file / Memory/Clients/ | Customer first name for personalization |
| `email_type` | enum | Yes | Calling skill | One of: `order_confirmation`, `status_update`, `refund_notification`, `inquiry_reply`, `complaint_response`, `follow_up`, `shipping_notification` |
| `subject` | string | Yes | Generated | Email subject line (keep original thread subject with "Re:" for replies) |
| `body_context` | object | Yes | Calling skill | Key-value pairs for template rendering (order_id, items, dates, amounts, etc.) |
| `attachments` | list | No | Task file | File paths for attachments (invoices, return labels) — only when customer-requested |
| `reply_to_thread` | string | No | Task file | Original email thread ID for reply threading |
| `cc` | list | No | Calling skill | CC recipients (internal team members only, never other customers) |
| `priority` | enum | No | Calling skill | `normal` (default) or `urgent` |

## Outputs

| Output | Type | Destination | Description |
|--------|------|-------------|-------------|
| `email_draft` | Markdown | `Pending_Approval/{filename}` | Full email content ready for human review |
| `email_id` | string | Audit log | Unique identifier for tracking (`EMAIL-{type}_{timestamp}`) |
| `send_status` | enum | Audit log | `drafted`, `approved`, `sent`, `failed`, `bounced` |
| `audit_entry` | JSONL | `Logs/audit/AUDIT_{date}.jsonl` | Structured audit record of the email action |
| `client_memory_update` | Markdown | `Memory/Clients/{slug}.md` | Append interaction record to customer profile |

## Approval Requirements

| Email Type | Approval Required | Authority | Handbook Reference |
|------------|-------------------|-----------|-------------------|
| Order confirmation | No — auto-send | AI Agent (Tier 1) | Section 5: Order Processing |
| Shipping notification | No — auto-send | AI Agent (Tier 1) | Section 5: Order Processing |
| Standard inquiry reply | Yes — human review | AI drafts → Pending_Approval | Section 4: Support Tiers |
| Complaint response | Yes — human review | AI drafts → Pending_Approval | Section 4: Tier 2 |
| Refund notification | Yes — human review | Supervisor/Manager (amount-based) | Section 6: Refund Approval |
| Follow-up email | No — auto-send | AI Agent (Tier 1) | Section 4: Rule 5 |
| Marketing / promotional | **Always** — human approval | Marketing lead → Director | Section 9: AI Must NEVER #3 |

### Approval Pipeline

```
AI drafts email → Pending_Approval/EMAIL-{type}_{timestamp}.md
    → Human reviews in Obsidian / Dashboard
    → Approved → MCP Email Server sends → Approved/
    → Rejected → Rejected/ (with reason)
```

**Auto-send exceptions** (no approval needed):
- Order confirmations (immediate, within 5 minutes — Section 5)
- Shipping notifications with tracking numbers
- Follow-up check-ins (24 hours post-resolution — Section 4, Rule 5)

## Steps

### 1. Validate Inputs
- Verify `recipient_email` is valid format
- Verify `recipient_name` exists (fall back to "there" if missing)
- Confirm `email_type` is recognized
- Check all required `body_context` fields for the template exist

### 2. Load Template & Context
- Select template from Company Handbook Section 8 based on `email_type`
- Load customer history from `Memory/Clients/` if available
- Apply Brand Voice rules (Section 3): warm, specific, customer-first

### 3. Render Email
- Fill template placeholders with `body_context` values
- Apply 4-Step Framework: Acknowledge → Address → Resolve → Follow-up
- Validate against writing rules (Section 3):
  - [ ] Uses customer's first name
  - [ ] Active voice throughout
  - [ ] Specific timelines (no "soon" or "shortly")
  - [ ] Under word limit (100–150 simple, 200–250 complex)
  - [ ] No unfilled placeholders (`{name}`, `{date}`, etc.)

### 4. Route for Approval
- If auto-send type → proceed to Step 5
- If approval required → write to `Pending_Approval/` and STOP
- Add approval metadata: who needs to approve, SLA for approval

### 5. Send via MCP Email Server
- Call `mcp__email__send` with rendered email
- Capture `message_id` and `send_status` from response
- If send fails → retry once after 30 seconds
- If retry fails → log error, create `ESCALATION-EMAIL_{timestamp}.md`

### 6. Post-Send Actions
- Write audit entry to `Logs/audit/`
- Update `Memory/Clients/{slug}.md` with interaction summary
- Move task file to `Approved/` (or `Rejected/` if send failed permanently)
- Refresh Dashboard.md

## MCP Integration

### MCP Server: `mcp__email`

The Send Email skill integrates with an MCP-compliant email server for transactional email dispatch.

#### Tools

| MCP Tool | Purpose | Parameters |
|----------|---------|------------|
| `mcp__email__send` | Send a single email | `to`, `subject`, `body_html`, `body_text`, `from_name`, `reply_to`, `cc`, `attachments` |
| `mcp__email__send_template` | Send using a pre-registered template | `to`, `template_id`, `template_vars`, `from_name` |
| `mcp__email__get_status` | Check delivery status of a sent email | `message_id` |
| `mcp__email__validate` | Validate an email address before sending | `email` |

#### Configuration

```json
{
  "mcpServers": {
    "email": {
      "type": "smtp",
      "provider": "transactional",
      "from_address": "care@royalsparkle.in",
      "from_name": "Royal Sparkle",
      "reply_to": "support@royalsparkle.in",
      "rate_limit": "100/hour",
      "retry_policy": {
        "max_retries": 1,
        "retry_delay_seconds": 30
      }
    }
  }
}
```

#### Error Handling

| MCP Error | Action |
|-----------|--------|
| `invalid_recipient` | Log warning, skip send, flag task for human review |
| `rate_limited` | Queue email, retry after cooldown period |
| `authentication_failed` | Log CRITICAL error, escalate to tech team |
| `send_failed` | Retry once after 30 seconds; escalate if retry fails |
| `bounced` | Update client memory, flag email as invalid |
| `timeout` | Retry once; if persistent, queue for manual send |

#### Security Rules
- **Never** include customer payment details in email body
- **Never** send to addresses not associated with the task
- **Never** CC external parties without explicit approval
- All email content is logged in audit (body excluded for privacy; subject + recipient logged)
- Attachments are scanned before send (no executable files)

## Error Handling

| Situation | Action |
|-----------|--------|
| Missing recipient email | Skip send, flag task for human input |
| Template rendering fails (missing variable) | Log error, fall back to generic template |
| Email bounces after send | Update client memory, create follow-up task |
| Approval timeout (> SLA) | Auto-escalate to next authority level |
| Duplicate send detected | Block send, log warning, alert human |

## Rules

- Follow Company Handbook Section 3 (Brand Voice) for ALL email content
- Follow Section 8 (Email Response Guidelines) for structure and templates
- Obey Section 9 (Sensitive Action Rules) — never send unsolicited marketing
- Never include internal system details (queue names, AI processing, vault paths) in customer emails
- Never send emails to multiple unrelated customers in a single action
- Always log the send action in audit, regardless of success or failure
