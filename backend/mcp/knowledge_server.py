"""MCP Knowledge Server — order monitoring & customer intelligence tools."""

import logging
import re
from datetime import datetime, timezone

from models import Order, OrderItem, Product
from services import vault

logger = logging.getLogger(__name__)


class KnowledgeServer:
    """MCP server for read-only order and customer data access."""

    def __init__(self, db=None):
        self.db = db

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": "get_order",
                "description": "Get full order details by order ID",
                "input_schema": {
                    "type": "object",
                    "properties": {"order_id": {"type": "integer"}},
                    "required": ["order_id"],
                },
            },
            {
                "name": "list_orders",
                "description": "List orders with optional filters",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "customer_email": {"type": "string"},
                        "date_from": {"type": "string"},
                        "date_to": {"type": "string"},
                    },
                },
            },
            {
                "name": "get_order_stats",
                "description": "Get today's order statistics",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "get_customer_history",
                "description": "Get customer profile and interaction history from memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "slug": {"type": "string"},
                    },
                },
            },
            {
                "name": "search_faq",
                "description": "Search the company handbook for answers",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
            {
                "name": "get_product_info",
                "description": "Get product details for customer-facing responses",
                "input_schema": {
                    "type": "object",
                    "properties": {"slug": {"type": "string"}},
                    "required": ["slug"],
                },
            },
            {
                "name": "search_policies",
                "description": "Search handbook for specific policy topics",
                "input_schema": {
                    "type": "object",
                    "properties": {"topic": {"type": "string"}},
                    "required": ["topic"],
                },
            },
        ]

    def call_tool(self, tool_name: str, args: dict):
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return handler(args)

    def _tool_get_order(self, args: dict) -> dict:
        order = self.db.query(Order).filter(Order.id == args["order_id"]).first()
        if not order:
            return {"error": f"Order #{args['order_id']} not found"}
        items = []
        for item in order.items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            items.append({
                "product": product.name if product else f"Product #{item.product_id}",
                "quantity": item.quantity,
                "price": item.price,
            })
        return {
            "id": order.id,
            "customer_name": order.customer_name,
            "email": order.email,
            "phone": order.phone,
            "address": order.address,
            "city": order.city,
            "total": order.total,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "items": items,
        }

    def _tool_list_orders(self, args: dict) -> list[dict]:
        query = self.db.query(Order)
        if args.get("status"):
            query = query.filter(Order.status == args["status"])
        if args.get("customer_email"):
            query = query.filter(Order.email == args["customer_email"])
        orders = query.order_by(Order.created_at.desc()).limit(50).all()
        return [
            {
                "id": o.id,
                "customer_name": o.customer_name,
                "email": o.email,
                "total": o.total,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]

    def _tool_get_order_stats(self, args: dict) -> dict:
        today = datetime.now(timezone.utc).date()
        total_orders = self.db.query(Order).filter(
            Order.created_at >= datetime.combine(today, datetime.min.time())
        ).count()
        total_revenue = self.db.query(Order).filter(
            Order.created_at >= datetime.combine(today, datetime.min.time())
        ).scalar() or 0
        pending = self.db.query(Order).filter(Order.status == "pending").count()
        completed = self.db.query(Order).filter(Order.status == "completed").count()
        return {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue) if total_revenue else 0,
            "pending": pending,
            "completed": completed,
            "date": str(today),
        }

    def _tool_get_customer_history(self, args: dict) -> dict:
        slug = args.get("slug")
        if not slug and args.get("email"):
            slug = re.sub(r'[^a-z0-9]+', '-', args["email"].split("@")[0].lower()).strip('-')
        if not slug:
            return {"error": "Provide email or slug"}
        try:
            content = vault.read_memory_file("Clients", f"{slug}.md")
            return {"slug": slug, "content": content}
        except FileNotFoundError:
            return {"slug": slug, "content": None, "note": "No profile found"}

    def _tool_search_faq(self, args: dict) -> list[dict]:
        handbook = vault.read_company_handbook()
        return _search_sections(handbook, args["query"])

    def _tool_get_product_info(self, args: dict) -> dict:
        product = self.db.query(Product).filter(Product.slug == args["slug"]).first()
        if not product:
            return {"error": f"Product '{args['slug']}' not found"}
        return {
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "description": product.description,
            "category": product.category.name if product.category else None,
            "in_stock": product.stock > 0,
        }

    def _tool_search_policies(self, args: dict) -> list[dict]:
        handbook = vault.read_company_handbook()
        return _search_sections(handbook, args["topic"])


def _search_sections(text: str, query: str) -> list[dict]:
    """Split handbook into ## sections and return matches."""
    sections = re.split(r'(?=^## )', text, flags=re.MULTILINE)
    query_lower = query.lower()
    results = []
    for section in sections:
        if query_lower in section.lower():
            title_match = re.match(r'## (.+)', section)
            title = title_match.group(1).strip() if title_match else "Untitled"
            results.append({
                "section": title,
                "content": section.strip()[:500],
            })
    return results
