"""Dashboard Route — aggregated system status."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Order, Product
from services import vault, audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Dashboard"])


@router.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db)):
    """Return full dashboard data and refresh Dashboard.md in the vault."""

    # Queue counts
    queue_counts = vault.get_queue_counts()

    # Today's audit summary
    today = audit.get_today_summary()

    # Recent actions (last 5 audit entries)
    recent_entries = audit.read_audit_entries()
    recent_actions = recent_entries[-5:] if recent_entries else []

    # Watchers
    watchers = vault.list_watcher_files()

    # DB stats (reuse existing logic)
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.total)).scalar() or 0.0
    total_products = db.query(func.count(Product.id)).scalar() or 0
    low_stock_count = db.query(func.count(Product.id)).filter(Product.stock < 10).scalar() or 0

    db_stats = {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "total_products": total_products,
        "low_stock_count": low_stock_count,
    }

    # System health
    system_health = {
        "status": "ACTIVE",
        "components": {
            "order_processing": "ONLINE",
            "inquiry_handler": "ONLINE",
            "inventory_monitor": "ONLINE",
            "scheduled_tasks": "ONLINE",
            "memory_system": "ONLINE",
        },
    }

    # Refresh Dashboard.md in the vault
    try:
        vault.update_dashboard(
            queue_counts=queue_counts,
            recent_actions=recent_actions,
            today_metrics={
                "completed": today.get("completed", 0),
                "pending": today.get("pending", 0),
                "inquiries": today.get("inquiries", 0),
                "orders": today.get("orders", 0),
                "alerts": today.get("alerts", 0),
            },
        )
    except Exception as e:
        logger.warning(f"Dashboard.md refresh failed: {e}")

    return {
        "queue_counts": queue_counts,
        "today_activity": today,
        "recent_actions": recent_actions,
        "watchers": watchers,
        "db_stats": db_stats,
        "system_health": system_health,
    }
