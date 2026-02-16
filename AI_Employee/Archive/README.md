# Archive

Cold storage for completed, expired, and retained items.

## Structure

| Subfolder | Contents | Source | Retention |
|-----------|----------|--------|-----------|
| `Approved/` | Approved tasks older than 30 days | `Approved/` | 1 year, then delete |
| `Rejected/` | Rejected tasks older than 30 days | `Rejected/` | 1 year, then delete |
| `Logs/` | Audit JSONL files older than 90 days | `Logs/audit/` | 1 year, then delete |

## Rules
- Files retain their original name when archived
- Archival is logged in `Logs/audit/`
- Files tagged `#retain-indefinitely` are never archived
- Active escalations bypass archival regardless of age
- See `Config/retention_policy.md` for full schedule
