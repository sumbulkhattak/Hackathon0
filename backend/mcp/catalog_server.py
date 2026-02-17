"""MCP Catalog Server -- product & pricing management tools."""

import logging
import re
from typing import Optional

from models import Product, Category

logger = logging.getLogger(__name__)


def _product_to_dict(p) -> dict:
    """Convert a Product model to a serializable dict."""
    return {
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "featured": p.featured,
        "image_url": p.image_url,
        "images": p.images_list,
        "category": p.category.name if p.category else None,
        "category_id": p.category.id if p.category else None,
    }


class CatalogServer:
    """MCP server for product catalog operations."""

    def __init__(self, db=None):
        self.db = db

    def list_tools(self) -> list[dict]:
        """Return tool definitions for Claude's tool_use."""
        return [
            {
                "name": "get_product",
                "description": "Get full product details by ID or slug",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Product ID"},
                        "slug": {"type": "string", "description": "Product slug"},
                    },
                },
            },
            {
                "name": "list_products",
                "description": "List products with optional filters",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "featured": {"type": "boolean"},
                        "low_stock": {"type": "boolean"},
                    },
                },
            },
            {
                "name": "create_product",
                "description": "Create a new product (requires approval)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "price": {"type": "number"},
                        "category_id": {"type": "integer"},
                        "stock": {"type": "integer", "default": 50},
                        "featured": {"type": "boolean", "default": False},
                        "image_url": {"type": "string", "default": ""},
                        "images": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": [],
                        },
                    },
                    "required": ["name", "description", "price", "category_id"],
                },
            },
            {
                "name": "update_product",
                "description": "Update product fields (requires approval)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "featured": {"type": "boolean"},
                        "image_url": {"type": "string"},
                    },
                    "required": ["id"],
                },
            },
            {
                "name": "update_price",
                "description": "Update product price (requires approval)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "new_price": {"type": "number"},
                        "reason": {"type": "string"},
                    },
                    "required": ["id", "new_price", "reason"],
                },
            },
            {
                "name": "set_stock",
                "description": "Update product stock level (requires approval)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "quantity": {"type": "integer"},
                        "reason": {"type": "string"},
                    },
                    "required": ["id", "quantity", "reason"],
                },
            },
            {
                "name": "delete_product",
                "description": "Delete a product (requires approval)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                    },
                    "required": ["id"],
                },
            },
        ]

    def call_tool(self, tool_name: str, args: dict) -> dict:
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return handler(args)

    # ── Read tools (execute immediately) ──────────────────────────────

    def _tool_get_product(self, args: dict) -> dict:
        product = None
        if "id" in args:
            product = self.db.query(Product).filter(Product.id == args["id"]).first()
        elif "slug" in args:
            product = (
                self.db.query(Product).filter(Product.slug == args["slug"]).first()
            )
        if not product:
            return {"error": "Product not found"}
        return _product_to_dict(product)

    def _tool_list_products(self, args: dict) -> list[dict]:
        query = self.db.query(Product)
        if args.get("low_stock"):
            query = query.filter(Product.stock < 10)
        if args.get("featured"):
            query = query.filter(Product.featured == True)  # noqa: E712
        if args.get("category"):
            query = query.join(Category).filter(Category.name == args["category"])
        products = query.all()
        return [_product_to_dict(p) for p in products]

    # ── Write tools (return action plans, don't execute) ──────────────

    def _tool_create_product(self, args: dict) -> dict:
        return {
            "action": "create_product",
            "server": "catalog",
            "args": args,
            "requires_approval": True,
            "description": f"Create product: {args.get('name')} at "
            f"\u20b9{args.get('price', 0):,.0f}",
        }

    def _tool_update_product(self, args: dict) -> dict:
        product_id = args.get("id")
        product = (
            self.db.query(Product).filter(Product.id == product_id).first()
        )
        current = _product_to_dict(product) if product else {}
        return {
            "action": "update_product",
            "server": "catalog",
            "args": args,
            "current": current,
            "requires_approval": True,
            "description": f"Update product #{product_id}",
        }

    def _tool_update_price(self, args: dict) -> dict:
        product = (
            self.db.query(Product).filter(Product.id == args["id"]).first()
        )
        old_price = product.price if product else 0
        return {
            "action": "update_price",
            "server": "catalog",
            "args": args,
            "old_price": old_price,
            "new_price": args["new_price"],
            "requires_approval": True,
            "description": f"Price change: \u20b9{old_price:,.0f} \u2192 "
            f"\u20b9{args['new_price']:,.0f}",
        }

    def _tool_set_stock(self, args: dict) -> dict:
        product = (
            self.db.query(Product).filter(Product.id == args["id"]).first()
        )
        old_stock = product.stock if product else 0
        return {
            "action": "set_stock",
            "server": "catalog",
            "args": args,
            "old_stock": old_stock,
            "new_stock": args["quantity"],
            "requires_approval": True,
            "description": f"Stock change: {old_stock} \u2192 {args['quantity']}",
        }

    def _tool_delete_product(self, args: dict) -> dict:
        product = (
            self.db.query(Product).filter(Product.id == args["id"]).first()
        )
        return {
            "action": "delete_product",
            "server": "catalog",
            "args": args,
            "product_name": product.name if product else "Unknown",
            "requires_approval": True,
            "description": f"Delete product #{args['id']}",
        }

    # ── Action execution (Phase 3 — runs approved actions) ───────────

    def execute_action(self, action: dict) -> dict:
        """Execute a previously approved action against the database."""
        action_type = action["action"]
        args = action["args"]

        if action_type == "create_product":
            slug = re.sub(r"[^a-z0-9]+", "-", args["name"].lower()).strip("-")
            product = Product(
                name=args["name"],
                slug=slug,
                description=args["description"],
                price=args["price"],
                image_url=args.get("image_url", f"/images/{slug}.jpg"),
                stock=args.get("stock", 50),
                featured=args.get("featured", False),
                category_id=args["category_id"],
            )
            if args.get("images"):
                product.images_list = args["images"]
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return {
                "status": "created",
                "product_id": product.id,
                "name": product.name,
            }

        elif action_type == "update_product":
            product = (
                self.db.query(Product).filter(Product.id == args["id"]).first()
            )
            if not product:
                return {
                    "status": "error",
                    "error": f"Product #{args['id']} not found",
                }
            for field in ["name", "description", "featured", "image_url"]:
                if field in args:
                    setattr(product, field, args[field])
            self.db.commit()
            return {"status": "updated", "product_id": product.id}

        elif action_type == "update_price":
            product = (
                self.db.query(Product).filter(Product.id == args["id"]).first()
            )
            if not product:
                return {
                    "status": "error",
                    "error": f"Product #{args['id']} not found",
                }
            old_price = product.price
            product.price = args["new_price"]
            self.db.commit()
            return {
                "status": "updated",
                "product_id": product.id,
                "old_price": old_price,
                "new_price": args["new_price"],
            }

        elif action_type == "set_stock":
            product = (
                self.db.query(Product).filter(Product.id == args["id"]).first()
            )
            if not product:
                return {
                    "status": "error",
                    "error": f"Product #{args['id']} not found",
                }
            old_stock = product.stock
            product.stock = args["quantity"]
            self.db.commit()
            return {
                "status": "updated",
                "product_id": product.id,
                "old_stock": old_stock,
                "new_stock": args["quantity"],
            }

        elif action_type == "delete_product":
            product = (
                self.db.query(Product).filter(Product.id == args["id"]).first()
            )
            if not product:
                return {
                    "status": "error",
                    "error": f"Product #{args['id']} not found",
                }
            name = product.name
            self.db.delete(product)
            self.db.commit()
            return {"status": "deleted", "product_name": name}

        return {"status": "error", "error": f"Unknown action: {action_type}"}
