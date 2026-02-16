"""Audit Routes — query audit logs and today's summary."""

import logging
from typing import Optional

from fastapi import APIRouter, Query

from services import audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Audit"])


@router.get("/audit")
async def get_audit_entries(
    date: Optional[str] = Query(None, description="Single date (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Range start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Range end (YYYY-MM-DD)"),
    action: Optional[str] = Query(None, description="Filter by action (e.g. task.created)"),
    entity_type: Optional[str] = Query(None, alias="type", description="Filter by entity type"),
):
    """Read audit entries with optional date range and filters."""
    entries = audit.read_audit_entries(
        date=date,
        start_date=start_date,
        end_date=end_date,
        action_filter=action,
        entity_type_filter=entity_type,
    )
    return {"count": len(entries), "entries": entries}


@router.get("/audit/today")
async def get_today_summary():
    """Get today's aggregated audit summary."""
    summary = audit.get_today_summary()
    return summary
