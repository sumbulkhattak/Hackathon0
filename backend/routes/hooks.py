"""AI Integration Hooks — real handlers that create vault tasks + trigger processing."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import HookPayload
from services import vault, audit
from services.ai_processor import process_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hooks", tags=["AI Hooks"])


@router.post("/order-trigger")
async def hook_order_trigger(payload: HookPayload, db: Session = Depends(get_db)):
    """AI integration hook: triggered when a new order is placed.

    Creates an ORDER task in the vault and optionally processes it.
    Expected payload.data keys: order_id, customer_name, email, total, items_count
    """
    logger.info(f"[AI HOOK] Order trigger received: {payload.model_dump()}")

    data = payload.data
    order_id = data.get("order_id")

    if not order_id:
        return {"status": "error", "message": "Missing order_id in payload data"}

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"ORDER-{order_id}_{timestamp}.md"

    content = f"""# New Order Task (via Hook)

## Status: PENDING

| Field | Value |
|-------|-------|
| **Task Type** | Order Processing |
| **Priority** | High |
| **Created** | {now.strftime("%Y-%m-%d %H:%M:%S UTC")} |
| **Order ID** | #{order_id} |
| **Customer** | {data.get('customer_name', 'Unknown')} |
| **Email** | {data.get('email', 'N/A')} |
| **Total** | Rs.{data.get('total', 0):,.0f} |
| **Items** | {data.get('items_count', 'N/A')} |
| **Source** | webhook/order-trigger |

## Action Required

- [ ] Verify payment received
- [ ] Confirm order with customer via email
- [ ] Prepare items for packaging
- [ ] Update order status

## Notes

> Created via AI hook integration.
"""

    filepath = vault.write_task_file("Needs_Action", filename, content)

    audit.write_audit_entry(
        source="hook/order-trigger",
        action="task.created",
        entity_type="order",
        entity_id=filename,
        details=data,
        queue="Needs_Action",
        status="PENDING",
    )
    audit.append_daily_log(
        source="hook/order-trigger",
        action="Task Created",
        details=f"ORDER-{order_id} via webhook — {data.get('customer_name', 'Unknown')}",
        status="PENDING",
    )

    result = {"status": "task_created", "hook": "order-trigger", "task_file": filename, "path": filepath}

    # Auto-process if the hook event signals it
    if data.get("auto_process"):
        try:
            process_result = process_task(filename, db)
            result["auto_processed"] = True
            result["process_result"] = process_result
        except Exception as e:
            result["auto_processed"] = False
            result["process_error"] = str(e)

    return result


@router.post("/inquiry")
async def hook_inquiry(payload: HookPayload, db: Session = Depends(get_db)):
    """AI integration hook: customer inquiry webhook.

    Creates an INQUIRY task in the vault.
    Expected payload.data keys: customer_name, email, subject, message
    """
    logger.info(f"[AI HOOK] Inquiry received: {payload.model_dump()}")

    data = payload.data
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"INQUIRY_{timestamp}.md"

    customer_name = data.get("customer_name", "Unknown")
    first_name = customer_name.split()[0] if customer_name else "Customer"

    content = f"""# Customer Inquiry — Reply Plan (via Hook)

## Status: PENDING

| Field | Value |
|-------|-------|
| **Task Type** | Customer Reply |
| **Priority** | Medium |
| **Created** | {now.strftime("%Y-%m-%d %H:%M:%S UTC")} |
| **Customer** | {customer_name} |
| **Email** | {data.get('email', 'N/A')} |
| **Subject** | {data.get('subject', 'General Inquiry')} |
| **Source** | webhook/inquiry |

## Customer Message

> {data.get('message', 'No message provided.')}

## Reply Plan

1. **Acknowledge** — Greet {first_name} and thank them
2. **Address** — Answer their question about: _{data.get('subject', 'their inquiry')}_
3. **Resolve** — Provide clear solution
4. **Follow-up** — Offer help, close warmly

## Notes

> Created via AI hook integration.
"""

    filepath = vault.write_task_file("Needs_Action", filename, content)

    audit.write_audit_entry(
        source="hook/inquiry",
        action="task.created",
        entity_type="inquiry",
        entity_id=filename,
        details={"customer": customer_name, "subject": data.get("subject", "")},
        queue="Needs_Action",
        status="PENDING",
    )
    audit.append_daily_log(
        source="hook/inquiry",
        action="Task Created",
        details=f"INQUIRY from {customer_name} via webhook — \"{data.get('subject', '')}\"",
        status="PENDING",
    )

    result = {"status": "task_created", "hook": "inquiry", "task_file": filename, "path": filepath}

    if data.get("auto_process"):
        try:
            process_result = process_task(filename, db)
            result["auto_processed"] = True
            result["process_result"] = process_result
        except Exception as e:
            result["auto_processed"] = False
            result["process_error"] = str(e)

    return result


@router.post("/inventory-alert")
async def hook_inventory_alert(payload: HookPayload, db: Session = Depends(get_db)):
    """AI integration hook: low stock inventory alert.

    Creates an INVENTORY-ALERT task in the vault.
    Expected payload.data keys: product_id, product_name, current_stock, threshold
    """
    logger.info(f"[AI HOOK] Inventory alert received: {payload.model_dump()}")

    data = payload.data
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"INVENTORY-ALERT_{timestamp}.md"

    stock = data.get("current_stock", 0)
    urgency = "CRITICAL" if stock <= 3 else ("LOW" if stock <= 7 else "WARNING")
    priority = "Critical" if stock <= 3 else "High"

    content = f"""# Inventory Alert — Low Stock (via Hook)

## Status: PENDING

| Field | Value |
|-------|-------|
| **Task Type** | Inventory Restock |
| **Priority** | {priority} |
| **Created** | {now.strftime("%Y-%m-%d %H:%M:%S UTC")} |
| **Product ID** | {data.get('product_id', 'N/A')} |
| **Product** | {data.get('product_name', 'Unknown')} |
| **Current Stock** | {stock} |
| **Threshold** | {data.get('threshold', 10)} |
| **Urgency** | {urgency} |
| **Products Affected** | 1 |
| **Critical Items** | {1 if stock <= 3 else 0} |
| **Source** | webhook/inventory-alert |

## Action Required

- [ ] Review stock level
- [ ] Contact supplier for restock
- [ ] Update expected restock date

## Notes

> Created via AI hook integration.
"""

    filepath = vault.write_task_file("Needs_Action", filename, content)

    audit.write_audit_entry(
        source="hook/inventory-alert",
        action="task.created",
        entity_type="inventory",
        entity_id=filename,
        details=data,
        queue="Needs_Action",
        status="PENDING",
    )
    audit.append_daily_log(
        source="hook/inventory-alert",
        action="Task Created",
        details=f"INVENTORY-ALERT for {data.get('product_name', 'Unknown')} — {stock} units ({urgency})",
        status="PENDING",
    )

    result = {"status": "task_created", "hook": "inventory-alert", "task_file": filename, "path": filepath}

    if data.get("auto_process"):
        try:
            process_result = process_task(filename, db)
            result["auto_processed"] = True
            result["process_result"] = process_result
        except Exception as e:
            result["auto_processed"] = False
            result["process_error"] = str(e)

    return result
