---
id: 001
title: HITL Approval Workflow Design
stage: general
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: hitl-approval-workflow
branch: master
user: user
command: brainstorming
labels: ["hitl", "approval-workflow", "design", "file-system-native"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - docs/plans/2026-02-17-hitl-approval-workflow-design.md
tests:
  - none
---

## Prompt

Design a Human-in-the-Loop approval workflow.

Folders:

- Pending_Approval
- Approved
- Rejected

Rules:

- No sensitive action without approval
- Move files after decision
- Log all actions

Output workflow diagram + automation logic.

## Response snapshot

Designed a File-System Native HITL approval workflow (Approach A) with 6 folders: Needs_Action, Pending_Approval, Approved, Executing, Archived, Rejected. Gate-everything policy — no action executes without human approval. Includes: state machine with valid transitions, YAML frontmatter metadata tracking, approval guard middleware (403 on invalid transitions), write-then-delete file mover, enhanced audit logging (from/to status, actor_type), task executor with failure handling, stale execution watchdog (15 min timeout), and dashboard integration with per-state action buttons.

## Outcome

- ✅ Impact: Full HITL design doc approved and written
- 🧪 Tests: none (design phase)
- 📁 Files: docs/plans/2026-02-17-hitl-approval-workflow-design.md
- 🔁 Next prompts: implementation planning via writing-plans skill
- 🧠 Reflection: User wanted Executing and Archived states added beyond the initial 4-folder proposal. Gate-everything was preferred over risk-based gating.

## Evaluation notes (flywheel)

- Failure modes observed: Initial state machine missing Executing/Archived states — user caught this
- Graders run and results (PASS/FAIL): N/A (design phase)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Implement the design via writing-plans skill
