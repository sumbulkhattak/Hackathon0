# Skill: Reasoning Engine

> **Skill ID:** reasoning-engine
> **Trigger:** New task file detected in `Needs_Action/`
> **Priority:** High
> **SLA:** Generate plan within 30 minutes of task detection

---

## Purpose

Automatically analyze incoming tasks using a 3-stage pipeline (Perception → Reasoning → Planning) and produce structured, actionable Markdown plans.

## Input

Any `.md` task file from `Needs_Action/` with a recognized prefix:
- `ORDER-` — Order processing tasks
- `INQUIRY_` — Customer inquiry tasks
- `INVENTORY-ALERT_` — Low stock alerts
- `ESCALATION-` — Escalated issues
- `FILE-UPLOAD_` — Uploaded document/image reviews

## Pipeline

### Stage 1: Perception

Gather all relevant facts from the task file:
- Parse the metadata table (`| **Field** | Value |`)
- Identify the task type, priority, customer (if any), and key details
- Load the matching Agent Skill for procedural context
- Check `Memory/Clients/` for customer history if a customer name is present
- Summarize what is known in a structured perception block

### Stage 2: Reasoning

Analyze the task against Company Handbook rules:
- Which policies apply? (response SLAs, escalation triggers, decision authority)
- What is the correct priority and urgency?
- Are there escalation triggers? (angry language, legal, safety, high-value refund)
- What handbook sections are most relevant?
- What are the risks of inaction or incorrect action?

Output a clear analysis paragraph covering: situation assessment, applicable rules, and recommended approach.

### Stage 3: Planning

Break the work into concrete, ordered steps:
- Each step has: title, action description, owner (AI or Human), and SLA
- Steps follow the matching Agent Skill's procedure
- Include a risks section (what could go wrong)
- Include success criteria as checkboxes

## Output Format

The plan must be written as a Markdown file in `Plans/` with this structure:

```
# Plan: {descriptive title}

> **Plan ID:** PLAN-{slug}_{timestamp}
> **Source Task:** {original filename}
> **Created:** {timestamp}
> **Priority:** {priority}
> **Pipeline:** Perception → Reasoning → Planning

## 1. Perception (What We Know)
{structured metadata table}

## 2. Reasoning (Analysis)
{analysis paragraph}

## 3. Action Plan
### Step 1: {title}
- **Action:** ...
- **Owner:** AI / Human
- **SLA:** ...
(repeat for each step)

## 4. Risks & Considerations
- {bullet list}

## 5. Success Criteria
- [ ] {checkbox list}
```

## Rules

- Never skip the Perception stage — always gather facts before reasoning
- Never fabricate information not present in the task file or handbook
- If a task matches escalation triggers, flag it prominently in the Reasoning section
- Keep plans actionable — every step must have a clear owner and timeline
- Plans are informational artifacts — they do not move or modify the original task file's queue position
- Always reference specific Company Handbook sections when justifying decisions

## Error Handling

| Situation | Action |
|-----------|--------|
| Task file is empty or malformed | Log warning, skip task |
| No matching Agent Skill | Use general reasoning with handbook only |
| Claude API unavailable | Log error, retry once after 30 seconds |
| Customer not found in Memory | Proceed without history, note in Perception |
