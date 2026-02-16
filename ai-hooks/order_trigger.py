"""
AI Hook: Order Trigger
Called when a new order is placed in Royal Sparkle.

Usage:
    This module can be imported by external AI agents or automation pipelines
    to process new orders — e.g., send confirmation emails, update CRM, or
    trigger downstream workflows.

Endpoint: POST /api/hooks/order-trigger
Payload:
    {
        "event": "new_order",
        "data": {
            "order_id": 1,
            "customer_name": "Priya Sharma",
            "email": "priya@example.com",
            "total": 1299.0,
            "items_count": 2
        }
    }
"""

import requests
import logging

logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"


def trigger_order_hook(order_id: int, customer_name: str, email: str, total: float, items_count: int):
    """Send order data to the AI hook endpoint."""
    payload = {
        "event": "new_order",
        "data": {
            "order_id": order_id,
            "customer_name": customer_name,
            "email": email,
            "total": total,
            "items_count": items_count,
        },
    }

    try:
        response = requests.post(f"{API_BASE}/api/hooks/order-trigger", json=payload)
        response.raise_for_status()
        logger.info(f"Order hook triggered successfully for order #{order_id}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to trigger order hook: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    result = trigger_order_hook(
        order_id=1,
        customer_name="Priya Sharma",
        email="priya@example.com",
        total=1299.0,
        items_count=2,
    )
    print(result)
