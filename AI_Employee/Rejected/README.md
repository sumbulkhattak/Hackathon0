# Rejected

Tasks that were reviewed and rejected by a human.

## Rejection Process
1. Add a rejection note to the file explaining why
2. Move the file here
3. The AI Employee learns from rejections to improve future responses

## Rejection Note Format
Add to the bottom of the task file:
```markdown
## Rejection
- **Rejected by:** {name}
- **Date:** {date}
- **Reason:** {explanation}
- **Action:** {reprocess / discard / escalate}
```

## Reprocessing
- If `Action: reprocess`, the task will be moved back to `Needs_Action/` with rejection feedback
- The AI Employee will attempt a revised response incorporating the feedback
