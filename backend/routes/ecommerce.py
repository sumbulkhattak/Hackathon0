"""E-Commerce stats and monitoring endpoints."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Order, Product
from services import vault

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ecommerce", tags=["E-Commerce"])


@router.get("/stats")
async def get_ecommerce_stats(db: Session = Depends(get_db)):
    """Aggregate product, order, and inquiry stats for the dashboard."""
    total_products = db.query(Product).count()
    low_stock = db.query(Product).filter(Product.stock < 10).count()
    out_of_stock = db.query(Product).filter(Product.stock == 0).count()

    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    completed_orders = db.query(Order).filter(Order.status == "completed").count()

    revenue = db.query(func.sum(Order.total)).scalar() or 0

    inquiry_tasks = vault.list_task_files("Needs_Action")
    pending_inquiries = sum(1 for t in inquiry_tasks if t["task_type"].startswith("INQUIRY"))

    pending_approval_tasks = vault.list_task_files("Pending_Approval")
    pending_responses = sum(1 for t in pending_approval_tasks if t["task_type"].startswith("INQUIRY"))

    return {
        "products": {"total": total_products, "low_stock": low_stock, "out_of_stock": out_of_stock},
        "orders": {"total": total_orders, "pending": pending_orders, "completed": completed_orders, "revenue": float(revenue)},
        "inquiries": {"pending": pending_inquiries, "awaiting_response": pending_responses},
    }
