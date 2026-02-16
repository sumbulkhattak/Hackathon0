# Agent Configuration — Retention Policy

> **Last Updated:** 2026-02-16
> **Scope:** Defines how long data lives in each folder before archival or deletion.

---

## Retention Schedule

| Data Type | Location | Active Retention | Archive To | Archive Retention | Then |
|-----------|----------|-----------------|------------|-------------------|------|
| Approved tasks | `Approved/` | 30 days | `Archive/Approved/` | 1 year | Delete |
| Rejected tasks | `Rejected/` | 30 days | `Archive/Rejected/` | 1 year | Delete |
| Daily logs (MD) | `Logs/` | Indefinite | — | — | Keep forever |
| Audit logs (JSONL) | `Logs/audit/` | 90 days | `Archive/Logs/` | 1 year | Delete |
| Daily reports | `Plans/` | 90 days | `Archive/Approved/` | 1 year | Delete |
| Weekly/Monthly reports | `Plans/` | 1 year | — | — | Keep forever |
| Client profiles | `Memory/Clients/` | Indefinite | — | — | Keep forever |
| Finance records | `Memory/Finance/` | Indefinite | — | — | Keep forever |
| Completed projects | `Memory/Projects/` | 30 days post-completion | `Archive/Approved/` | 1 year | Delete |

## Archival Process

1. **Scheduled Task** runs weekly (Sunday 2:00 AM IST)
2. Scans each folder for items exceeding active retention
3. Moves qualifying files to the corresponding `Archive/` subfolder
4. Logs the archival action in `Logs/audit/`
5. Updates `Dashboard.md` with archival summary

## Deletion Process

1. **Scheduled Task** runs monthly (1st of month, 3:00 AM IST)
2. Scans `Archive/` for items exceeding archive retention
3. Permanently deletes qualifying files
4. Logs deletion in `Logs/audit/` (the log entry itself is retained)

## Exceptions

- Files tagged `#retain-indefinitely` are never archived or deleted
- Active escalations are never archived regardless of age
- Client profiles are never deleted (privacy request = anonymize, not delete)
