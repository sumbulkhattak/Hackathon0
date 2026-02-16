"""
AI Hook: Inquiry Trigger
Called when a customer submits an inquiry about a product or order.

Usage:
    This module can be imported by external AI agents (chatbots, support
    systems) to forward customer inquiries for processing.

Endpoint: POST /api/hooks/inquiry
Payload:
    {
        "event": "customer_inquiry",
        "data": {
            "customer_name": "Priya Sharma",
            "email": "priya@example.com",
            "subject": "Order status",
            "message": "When will my order #5 be shipped?",
            "product_id": null,
            "order_id": 5
        }
    }
"""

import requests
import logging

logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"


def trigger_inquiry_hook(
    customer_name: str,
    email: str,
    subject: str,
    message: str,
    product_id: int | None = None,
    order_id: int | None = None,
):
    """Send customer inquiry data to the AI hook endpoint."""
    payload = {
        "event": "customer_inquiry",
        "data": {
            "customer_name": customer_name,
            "email": email,
            "subject": subject,
            "message": message,
            "product_id": product_id,
            "order_id": order_id,
        },
    }

    try:
        response = requests.post(f"{API_BASE}/api/hooks/inquiry", json=payload)
        response.raise_for_status()
        logger.info(f"Inquiry hook triggered successfully for {email}")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to trigger inquiry hook: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    result = trigger_inquiry_hook(
        customer_name="Priya Sharma",
        email="priya@example.com",
        subject="Product availability",
        message="Is the Rose Petal Layered Necklace available in gold?",
        product_id=1,
    )
    print(result)
