"""
AI Hook: Inventory Alert
Called when product stock drops below threshold (< 10 units).

Usage:
    This module can be imported by monitoring systems or AI agents
    to trigger restocking workflows, send alerts to admins, or
    update inventory dashboards.

Endpoint: POST /api/hooks/inventory-alert
Payload:
    {
        "event": "low_stock",
        "data": {
            "product_id": 3,
            "product_name": "Crystal Chandelier Earrings",
            "current_stock": 5,
            "threshold": 10
        }
    }
"""

import requests
import logging

logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"


def trigger_inventory_alert(product_id: int, product_name: str, current_stock: int, threshold: int = 10):
    """Send low-stock alert to the AI hook endpoint."""
    payload = {
        "event": "low_stock",
        "data": {
            "product_id": product_id,
            "product_name": product_name,
            "current_stock": current_stock,
            "threshold": threshold,
        },
    }

    try:
        response = requests.post(f"{API_BASE}/api/hooks/inventory-alert", json=payload)
        response.raise_for_status()
        logger.info(f"Inventory alert triggered for {product_name} (stock: {current_stock})")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to trigger inventory alert: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    result = trigger_inventory_alert(
        product_id=3,
        product_name="Crystal Chandelier Earrings",
        current_stock=5,
    )
    print(result)
