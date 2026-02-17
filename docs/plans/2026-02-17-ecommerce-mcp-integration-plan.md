# E-Commerce MCP Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build 3 local MCP servers (catalog, knowledge, email) that wrap existing SQLAlchemy models, integrate them with the AI processor and task executor, add new trigger endpoints, and update the frontend dashboard.

**Architecture:** Local Python MCP tool modules in `backend/mcp/` that provide callable tools. The AI processor discovers tools and passes them to Claude. The task executor parses queued actions from approved tasks and runs them via MCP. All writes go through HITL approval.

**Tech Stack:** Python, FastAPI, SQLAlchemy, SQLite, Claude API (tool use), Next.js/React/TypeScript

**Design Doc:** `docs/plans/2026-02-17-ecommerce-mcp-integration-design.md`

---

### Task 1: MCP Registry and Catalog Server

**Files:**
- Create: `backend/mcp/__init__.py`
- Create: `backend/mcp/catalog_server.py`
- Create: `backend/tests/test_mcp_catalog.py`

**Step 1: Write the failing test**

Create `backend/tests/test_mcp_catalog.py`:

```python
"""Tests for MCP Catalog Server — product & pricing tools."""
import pytest
from unittest.mock import MagicMock, patch
from mcp.catalog_server import CatalogServer


@pytest.fixture
def db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def server(db):
    return CatalogServer(db)


def test_list_tools_returns_all_tools(server):
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert "get_product" in names
    assert "list_products" in names
    assert "create_product" in names
    assert "update_product" in names
    assert "update_price" in names
    assert "set_stock" in names
    assert "delete_product" in names
    assert len(names) == 7


def test_get_product_by_id(server, db):
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Rose Necklace"
    mock_product.slug = "rose-necklace"
    mock_product.price = 1299.0
    mock_product.stock = 50
    mock_product.featured = False
    mock_product.description = "A beautiful necklace"
    mock_product.image_url = "/img/rose.jpg"
    mock_product.images_list = ["/img/rose.jpg"]
    mock_product.category = MagicMock()
    mock_product.category.name = "Necklaces"
    mock_product.category.id = 1

    db.query.return_value.filter.return_value.first.return_value = mock_product
    result = server.call_tool("get_product", {"id": 1})
    assert result["name"] == "Rose Necklace"
    assert result["price"] == 1299.0


def test_list_products_low_stock(server, db):
    mock_p = MagicMock()
    mock_p.id = 1
    mock_p.name = "Low Stock Item"
    mock_p.slug = "low-stock"
    mock_p.price = 499.0
    mock_p.stock = 3
    mock_p.featured = False
    mock_p.category = MagicMock()
    mock_p.category.name = "Earrings"

    db.query.return_value.filter.return_value.all.return_value = [mock_p]
    result = server.call_tool("list_products", {"low_stock": True})
    assert len(result) == 1
    assert result[0]["stock"] == 3


def test_create_product_returns_plan(server, db):
    result = server.call_tool("create_product", {
        "name": "New Choker",
        "description": "A stunning choker",
        "price": 2499.0,
        "category_id": 1,
        "stock": 25,
        "featured": False,
    })
    assert result["action"] == "create_product"
    assert result["args"]["name"] == "New Choker"
    assert result["requires_approval"] is True


def test_update_price_returns_plan(server, db):
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Rose Necklace"
    mock_product.price = 1299.0

    db.query.return_value.filter.return_value.first.return_value = mock_product
    result = server.call_tool("update_price", {"id": 1, "new_price": 1499.0, "reason": "Premium materials"})
    assert result["action"] == "update_price"
    assert result["old_price"] == 1299.0
    assert result["new_price"] == 1499.0
    assert result["requires_approval"] is True


def test_call_tool_unknown_raises(server):
    with pytest.raises(ValueError, match="Unknown tool"):
        server.call_tool("nonexistent_tool", {})
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_mcp_catalog.py -v`
Expected: FAIL — module not found

**Step 3: Write the MCP registry**

Create `backend/mcp/__init__.py`:

```python
"""MCP Server Registry — central access point for all MCP tool servers."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Server instances are lazily initialized
_servers = {}


def get_server(name: str, db=None):
    """Get an MCP server instance by name."""
    if name not in _servers:
        if name == "catalog":
            from mcp.catalog_server import CatalogServer
            _servers[name] = CatalogServer(db)
        elif name == "knowledge":
            from mcp.knowledge_server import KnowledgeServer
            _servers[name] = KnowledgeServer(db)
        elif name == "email":
            from mcp.email_server import EmailServer
            _servers[name] = EmailServer()
        else:
            raise ValueError(f"Unknown MCP server: {name}")
    # Update db session if provided (sessions are per-request)
    if db is not None and hasattr(_servers[name], 'db'):
        _servers[name].db = db
    return _servers[name]


def get_all_tools(db=None) -> list[dict]:
    """Get all tool definitions from all MCP servers for Claude."""
    tools = []
    for name in ["catalog", "knowledge", "email"]:
        try:
            server = get_server(name, db)
            for tool in server.list_tools():
                tool["server"] = name
                tools.append(tool)
        except Exception as e:
            logger.warning(f"Failed to load MCP server '{name}': {e}")
    return tools


def call_tool(server_name: str, tool_name: str, args: dict, db=None):
    """Route a tool call to the correct MCP server."""
    server = get_server(server_name, db)
    return server.call_tool(tool_name, args)


def reset():
    """Clear cached server instances (for testing)."""
    _servers.clear()
```

**Step 4: Write the Catalog Server**

Create `backend/mcp/catalog_server.py`:

```python
"""MCP Catalog Server — product & pricing management tools."""

import logging
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
                        "category": {"type": "string", "description": "Filter by category name"},
                        "featured": {"type": "boolean", "description": "Filter featured products only"},
                        "low_stock": {"type": "boolean", "description": "Filter products with stock < 10"},
                    },
                },
            },
            {
                "name": "create_product",
                "description": "Create a new product (requires approval). Returns an action plan.",
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
                        "images": {"type": "array", "items": {"type": "string"}, "default": []},
                    },
                    "required": ["name", "description", "price", "category_id"],
                },
            },
            {
                "name": "update_product",
                "description": "Update product fields (requires approval). Returns an action plan.",
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
                "description": "Update product price (requires approval). Returns old/new comparison.",
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
                "description": "Update product stock level (requires approval).",
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
                "description": "Delete a product (requires approval).",
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
        """Execute a tool call."""
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return handler(args)

    # ── Read tools (execute immediately) ──

    def _tool_get_product(self, args: dict) -> dict:
        product = None
        if "id" in args:
            product = self.db.query(Product).filter(Product.id == args["id"]).first()
        elif "slug" in args:
            product = self.db.query(Product).filter(Product.slug == args["slug"]).first()
        if not product:
            return {"error": "Product not found"}
        return _product_to_dict(product)

    def _tool_list_products(self, args: dict) -> list[dict]:
        query = self.db.query(Product)
        if args.get("low_stock"):
            query = query.filter(Product.stock < 10)
        if args.get("featured"):
            query = query.filter(Product.featured == True)
        if args.get("category"):
            query = query.join(Category).filter(Category.name == args["category"])
        products = query.all()
        return [_product_to_dict(p) for p in products]

    # ── Write tools (return action plans, don't execute) ──

    def _tool_create_product(self, args: dict) -> dict:
        return {
            "action": "create_product",
            "server": "catalog",
            "args": args,
            "requires_approval": True,
            "description": f"Create product: {args.get('name')} at ₹{args.get('price', 0):,.0f}",
        }

    def _tool_update_product(self, args: dict) -> dict:
        product_id = args.get("id")
        product = self.db.query(Product).filter(Product.id == product_id).first()
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
        product = self.db.query(Product).filter(Product.id == args["id"]).first()
        old_price = product.price if product else 0
        return {
            "action": "update_price",
            "server": "catalog",
            "args": args,
            "old_price": old_price,
            "new_price": args["new_price"],
            "requires_approval": True,
            "description": f"Price change: ₹{old_price:,.0f} → ₹{args['new_price']:,.0f} ({args.get('reason', '')})",
        }

    def _tool_set_stock(self, args: dict) -> dict:
        product = self.db.query(Product).filter(Product.id == args["id"]).first()
        old_stock = product.stock if product else 0
        return {
            "action": "set_stock",
            "server": "catalog",
            "args": args,
            "old_stock": old_stock,
            "new_stock": args["quantity"],
            "requires_approval": True,
            "description": f"Stock change: {old_stock} → {args['quantity']} ({args.get('reason', '')})",
        }

    def _tool_delete_product(self, args: dict) -> dict:
        product = self.db.query(Product).filter(Product.id == args["id"]).first()
        return {
            "action": "delete_product",
            "server": "catalog",
            "args": args,
            "product_name": product.name if product else "Unknown",
            "requires_approval": True,
            "description": f"Delete product #{args['id']}",
        }

    # ── Execute approved actions (called by task_executor in Phase 3) ──

    def execute_action(self, action: dict) -> dict:
        """Execute a previously approved action against the database."""
        action_type = action["action"]
        args = action["args"]

        if action_type == "create_product":
            import re
            slug = re.sub(r'[^a-z0-9]+', '-', args["name"].lower()).strip('-')
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
            return {"status": "created", "product_id": product.id, "name": product.name}

        elif action_type == "update_product":
            product = self.db.query(Product).filter(Product.id == args["id"]).first()
            if not product:
                return {"status": "error", "error": f"Product #{args['id']} not found"}
            for field in ["name", "description", "featured", "image_url"]:
                if field in args:
                    setattr(product, field, args[field])
            self.db.commit()
            return {"status": "updated", "product_id": product.id}

        elif action_type == "update_price":
            product = self.db.query(Product).filter(Product.id == args["id"]).first()
            if not product:
                return {"status": "error", "error": f"Product #{args['id']} not found"}
            old_price = product.price
            product.price = args["new_price"]
            self.db.commit()
            return {"status": "updated", "product_id": product.id, "old_price": old_price, "new_price": args["new_price"]}

        elif action_type == "set_stock":
            product = self.db.query(Product).filter(Product.id == args["id"]).first()
            if not product:
                return {"status": "error", "error": f"Product #{args['id']} not found"}
            old_stock = product.stock
            product.stock = args["quantity"]
            self.db.commit()
            return {"status": "updated", "product_id": product.id, "old_stock": old_stock, "new_stock": args["quantity"]}

        elif action_type == "delete_product":
            product = self.db.query(Product).filter(Product.id == args["id"]).first()
            if not product:
                return {"status": "error", "error": f"Product #{args['id']} not found"}
            name = product.name
            self.db.delete(product)
            self.db.commit()
            return {"status": "deleted", "product_name": name}

        return {"status": "error", "error": f"Unknown action: {action_type}"}
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_mcp_catalog.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add backend/mcp/__init__.py backend/mcp/catalog_server.py backend/tests/test_mcp_catalog.py
git commit -m "feat: add MCP registry and catalog server with 7 tools"
```

---

### Task 2: Knowledge MCP Server

**Files:**
- Create: `backend/mcp/knowledge_server.py`
- Create: `backend/tests/test_mcp_knowledge.py`

**Step 1: Write the failing test**

Create `backend/tests/test_mcp_knowledge.py`:

```python
"""Tests for MCP Knowledge Server — orders, customers, FAQ tools."""
import pytest
from unittest.mock import MagicMock, patch
from mcp.knowledge_server import KnowledgeServer


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def server(db):
    return KnowledgeServer(db)


def test_list_tools_returns_all_tools(server):
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert "get_order" in names
    assert "list_orders" in names
    assert "get_order_stats" in names
    assert "get_customer_history" in names
    assert "search_faq" in names
    assert "get_product_info" in names
    assert "search_policies" in names
    assert len(names) == 7


def test_get_order(server, db):
    mock_order = MagicMock()
    mock_order.id = 1
    mock_order.customer_name = "Priya"
    mock_order.email = "priya@gmail.com"
    mock_order.total = 3499.0
    mock_order.status = "pending"
    mock_order.phone = "9876543210"
    mock_order.address = "45 Marine Drive"
    mock_order.city = "Mumbai"
    mock_order.created_at = MagicMock()
    mock_order.created_at.isoformat.return_value = "2026-02-17T00:00:00"
    mock_order.items = []

    db.query.return_value.filter.return_value.first.return_value = mock_order
    result = server.call_tool("get_order", {"order_id": 1})
    assert result["customer_name"] == "Priya"
    assert result["total"] == 3499.0


def test_get_order_stats(server, db):
    from unittest.mock import PropertyMock
    # Mock scalar results
    db.query.return_value.filter.return_value.count.return_value = 5
    db.query.return_value.filter.return_value.scalar.return_value = 12500.0

    result = server.call_tool("get_order_stats", {})
    assert "total_orders" in result
    assert "total_revenue" in result


def test_search_faq(server):
    with patch("mcp.knowledge_server.vault") as mock_vault:
        mock_vault.read_company_handbook.return_value = "## 6. Refund Policy\n\n7-day return window.\n\n## 7. Pricing\n\nEntry tier: 299-499."
        result = server.call_tool("search_faq", {"query": "refund"})
        assert len(result) > 0
        assert "refund" in result[0]["section"].lower()


def test_get_customer_history(server):
    with patch("mcp.knowledge_server.vault") as mock_vault:
        mock_vault.read_memory_file.return_value = "# Client: Priya\n\n| Date | Type |\n| 2026-02-17 | ORDER |"
        result = server.call_tool("get_customer_history", {"slug": "priya-sharma"})
        assert "Priya" in result["content"]


def test_search_policies(server):
    with patch("mcp.knowledge_server.vault") as mock_vault:
        mock_vault.read_company_handbook.return_value = "## 5. Order Processing\n\nShipping in 3-5 days.\n\n## 6. Refund Policy\n\n7-day window."
        result = server.call_tool("search_policies", {"topic": "shipping"})
        assert len(result) > 0


def test_call_tool_unknown_raises(server):
    with pytest.raises(ValueError, match="Unknown tool"):
        server.call_tool("nonexistent", {})
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_mcp_knowledge.py -v`
Expected: FAIL — module not found

**Step 3: Write the Knowledge Server**

Create `backend/mcp/knowledge_server.py`:

```python
"""MCP Knowledge Server — order monitoring & customer intelligence tools."""

import logging
import re
from datetime import datetime, timezone, timedelta

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
                    "properties": {
                        "order_id": {"type": "integer"},
                    },
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
                        "date_from": {"type": "string", "description": "YYYY-MM-DD"},
                        "date_to": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                },
            },
            {
                "name": "get_order_stats",
                "description": "Get today's order statistics: count, revenue, pending, completed",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "get_customer_history",
                "description": "Get customer profile and interaction history from memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "slug": {"type": "string", "description": "Client slug e.g. priya-sharma"},
                    },
                },
            },
            {
                "name": "search_faq",
                "description": "Search the company handbook for answers to customer questions",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_product_info",
                "description": "Get product details for customer-facing responses",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "slug": {"type": "string"},
                    },
                    "required": ["slug"],
                },
            },
            {
                "name": "search_policies",
                "description": "Search handbook for specific policy topics (refund, shipping, etc.)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                    },
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
            return {"slug": slug, "content": None, "note": "No profile found for this customer"}

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
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_mcp_knowledge.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add backend/mcp/knowledge_server.py backend/tests/test_mcp_knowledge.py
git commit -m "feat: add MCP knowledge server with 7 read-only tools"
```

---

### Task 3: Email MCP Server

**Files:**
- Create: `backend/mcp/email_server.py`
- Create: `backend/tests/test_mcp_email.py`

**Step 1: Write the failing test**

Create `backend/tests/test_mcp_email.py`:

```python
"""Tests for MCP Email Server — customer communication tools."""
import pytest
from unittest.mock import patch, MagicMock
from mcp.email_server import EmailServer


@pytest.fixture
def server():
    return EmailServer()


def test_list_tools_returns_all_tools(server):
    tools = server.list_tools()
    names = [t["name"] for t in tools]
    assert "draft_reply" in names
    assert "send_email" in names
    assert "get_thread" in names
    assert len(names) == 3


def test_draft_reply_returns_plan(server):
    result = server.call_tool("draft_reply", {
        "to": "priya@gmail.com",
        "subject": "Re: Order #3",
        "body": "Hi Priya, your order is confirmed!",
    })
    assert result["action"] == "send_email"
    assert result["requires_approval"] is True
    assert result["args"]["to"] == "priya@gmail.com"


def test_send_email_returns_plan(server):
    result = server.call_tool("send_email", {
        "to": "priya@gmail.com",
        "subject": "Order Confirmation",
        "body": "Thank you for your order!",
    })
    assert result["action"] == "send_email"
    assert result["requires_approval"] is True


def test_get_thread_reads_audit(server):
    with patch("mcp.email_server.audit") as mock_audit:
        mock_audit.read_audit_entries.return_value = [
            {"entity_id": "INQUIRY_2026-02-17.md", "action": "task.completed", "timestamp": "2026-02-17"},
        ]
        result = server.call_tool("get_thread", {"customer_email": "priya@gmail.com"})
        assert isinstance(result, list)


def test_call_tool_unknown_raises(server):
    with pytest.raises(ValueError, match="Unknown tool"):
        server.call_tool("nonexistent", {})
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_mcp_email.py -v`
Expected: FAIL — module not found

**Step 3: Write the Email Server**

Create `backend/mcp/email_server.py`:

```python
"""MCP Email Server — customer communication tools."""

import logging
from services import audit

logger = logging.getLogger(__name__)


class EmailServer:
    """MCP server for email operations."""

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": "draft_reply",
                "description": "Draft a customer email reply (requires approval before sending)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email"},
                        "subject": {"type": "string"},
                        "body": {"type": "string", "description": "Email body text"},
                        "template": {"type": "string", "description": "Template name (optional)"},
                    },
                    "required": ["to", "subject", "body"],
                },
            },
            {
                "name": "send_email",
                "description": "Send an email to a customer (requires approval)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["to", "subject", "body"],
                },
            },
            {
                "name": "get_thread",
                "description": "Get previous email/interaction history for a customer",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_email": {"type": "string"},
                    },
                    "required": ["customer_email"],
                },
            },
        ]

    def call_tool(self, tool_name: str, args: dict):
        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return handler(args)

    def _tool_draft_reply(self, args: dict) -> dict:
        return {
            "action": "send_email",
            "server": "email",
            "args": {
                "to": args["to"],
                "subject": args["subject"],
                "body": args["body"],
            },
            "requires_approval": True,
            "description": f"Send email to {args['to']}: {args['subject']}",
        }

    def _tool_send_email(self, args: dict) -> dict:
        return {
            "action": "send_email",
            "server": "email",
            "args": args,
            "requires_approval": True,
            "description": f"Send email to {args['to']}: {args['subject']}",
        }

    def _tool_get_thread(self, args: dict) -> list[dict]:
        entries = audit.read_audit_entries()
        email = args["customer_email"].lower()
        relevant = [
            e for e in entries
            if email in str(e.get("details", "")).lower()
            or email in str(e.get("entity_id", "")).lower()
        ]
        return relevant[-10:]  # Last 10 interactions

    def execute_action(self, action: dict) -> dict:
        """Execute approved email send. Logs to audit (no real SMTP yet)."""
        args = action["args"]
        logger.info(f"[EMAIL] Sending to {args['to']}: {args['subject']}")
        audit.write_audit_entry(
            source="mcp/email",
            action="email.sent",
            entity_type="email",
            entity_id=args["to"],
            actor="task-executor",
            details={"subject": args["subject"], "to": args["to"]},
            status="SENT",
        )
        return {
            "status": "sent",
            "to": args["to"],
            "subject": args["subject"],
            "note": "Logged to audit trail (SMTP not configured)",
        }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_mcp_email.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add backend/mcp/email_server.py backend/tests/test_mcp_email.py
git commit -m "feat: add MCP email server with 3 communication tools"
```

---

### Task 4: New Trigger Endpoints

**Files:**
- Modify: `backend/routes/triggers.py:1-378`
- Create: `backend/routes/ecommerce.py`
- Modify: `backend/main.py:65-73`
- Create: `backend/tests/test_ecommerce_routes.py`

**Step 1: Write the failing test**

Create `backend/tests/test_ecommerce_routes.py`:

```python
"""Tests for e-commerce trigger and stats endpoints."""
import pytest
from unittest.mock import patch, MagicMock


def test_product_trigger_schema():
    """ProductTriggerRequest schema exists with required fields."""
    from routes.triggers import ProductTriggerRequest
    req = ProductTriggerRequest(
        name="Test Choker",
        description="A beautiful choker",
        price=2499.0,
        category_id=1,
    )
    assert req.name == "Test Choker"
    assert req.price == 2499.0


def test_price_update_trigger_schema():
    """PriceUpdateTriggerRequest schema exists with required fields."""
    from routes.triggers import PriceUpdateTriggerRequest
    req = PriceUpdateTriggerRequest(
        product_id=1,
        new_price=1499.0,
        reason="Premium materials",
    )
    assert req.product_id == 1
    assert req.new_price == 1499.0


def test_ecommerce_stats_endpoint_exists():
    """The ecommerce router has a /stats endpoint."""
    from routes.ecommerce import router
    paths = [r.path for r in router.routes]
    assert "/stats" in paths
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_ecommerce_routes.py -v`
Expected: FAIL — schemas/module not found

**Step 3: Add new schemas and endpoints to triggers.py**

Add to `backend/routes/triggers.py` after the InventoryTriggerRequest class (line 38):

```python
class ProductTriggerRequest(BaseModel):
    name: str
    description: str
    price: float
    category_id: int
    stock: int = 50
    featured: bool = False
    image_url: str = ""


class PriceUpdateTriggerRequest(BaseModel):
    product_id: int
    new_price: float
    reason: str
```

Add new endpoints at the end of `backend/routes/triggers.py`:

```python
# ─── 4. PRODUCT ADD TRIGGER ──────────────────────────────────────────────

@router.post("/product")
async def trigger_product(
    req: ProductTriggerRequest,
    db: Session = Depends(get_db),
    auto_process: bool = Query(False),
):
    """Generate a task file to add a new product."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"PRODUCT-ADD_{timestamp}.md"

    # Look up category name
    from models import Category
    category = db.query(Category).filter(Category.id == req.category_id).first()
    category_name = category.name if category else f"Category #{req.category_id}"

    content = f"""# New Product Task

## Status: PENDING

| Field | Value |
|-------|-------|
| **Task Type** | Product Addition |
| **Priority** | Medium |
| **Created** | {now.strftime("%Y-%m-%d %H:%M:%S UTC")} |
| **Product Name** | {req.name} |
| **Description** | {req.description} |
| **Price** | ₹{req.price:,.0f} |
| **Category** | {category_name} |
| **Category ID** | {req.category_id} |
| **Stock** | {req.stock} |
| **Featured** | {"Yes" if req.featured else "No"} |

## Action Required

- [ ] Verify product details and pricing
- [ ] Check for duplicate listings
- [ ] Validate category assignment
- [ ] Add product to catalog
- [ ] Update inventory system

## Notes

> Auto-generated by Royal Sparkle AI Trigger System.
> Review and approve before publishing to the storefront.
"""

    filepath = vault.write_task_file("Needs_Action", filename, content)

    audit.write_audit_entry(
        source="trigger/product",
        action="task.created",
        entity_type="product",
        entity_id=filename,
        details={"product_name": req.name, "price": req.price, "category": category_name},
        queue="Needs_Action",
        status="PENDING",
    )
    audit.append_daily_log(
        source="trigger/product",
        action="Task Created",
        details=f"PRODUCT-ADD — {req.name} — ₹{req.price:,.0f}",
        status="PENDING",
    )

    result = {"status": "task_created", "trigger": "product", "task_file": filename, "path": filepath}

    if auto_process:
        try:
            process_result = process_task(filename, db)
            result["auto_processed"] = True
            result["process_result"] = process_result
        except Exception as e:
            result["auto_processed"] = False
            result["process_error"] = str(e)

    return result


# ─── 5. PRICE UPDATE TRIGGER ──────────────────────────────────────────────

@router.post("/price-update")
async def trigger_price_update(
    req: PriceUpdateTriggerRequest,
    db: Session = Depends(get_db),
    auto_process: bool = Query(False),
):
    """Generate a task file to update product pricing."""
    product = db.query(Product).filter(Product.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product #{req.product_id} not found")

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"PRICE-UPDATE_{timestamp}.md"

    content = f"""# Price Update Task

## Status: PENDING

| Field | Value |
|-------|-------|
| **Task Type** | Price Update |
| **Priority** | Medium |
| **Created** | {now.strftime("%Y-%m-%d %H:%M:%S UTC")} |
| **Product ID** | {product.id} |
| **Product Name** | {product.name} |
| **Current Price** | ₹{product.price:,.0f} |
| **New Price** | ₹{req.new_price:,.0f} |
| **Change** | {"+" if req.new_price > product.price else ""}₹{req.new_price - product.price:,.0f} |
| **Reason** | {req.reason} |

## Action Required

- [ ] Verify pricing against margin rules (min 30% margin)
- [ ] Check for active promotions on this product
- [ ] Update price in catalog
- [ ] Notify marketing if significant change

## Notes

> Auto-generated by Royal Sparkle AI Trigger System.
> Price changes require approval before applying.
"""

    filepath = vault.write_task_file("Needs_Action", filename, content)

    audit.write_audit_entry(
        source="trigger/price-update",
        action="task.created",
        entity_type="product",
        entity_id=filename,
        details={
            "product_id": product.id,
            "product_name": product.name,
            "old_price": product.price,
            "new_price": req.new_price,
            "reason": req.reason,
        },
        queue="Needs_Action",
        status="PENDING",
    )
    audit.append_daily_log(
        source="trigger/price-update",
        action="Task Created",
        details=f"PRICE-UPDATE — {product.name}: ₹{product.price:,.0f} → ₹{req.new_price:,.0f}",
        status="PENDING",
    )

    result = {"status": "task_created", "trigger": "price-update", "task_file": filename, "path": filepath}

    if auto_process:
        try:
            process_result = process_task(filename, db)
            result["auto_processed"] = True
            result["process_result"] = process_result
        except Exception as e:
            result["auto_processed"] = False
            result["process_error"] = str(e)

    return result
```

**Step 4: Create the ecommerce stats route**

Create `backend/routes/ecommerce.py`:

```python
"""E-Commerce stats and monitoring endpoints."""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

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

    # Count pending inquiries from vault
    inquiry_tasks = vault.list_task_files("Needs_Action")
    pending_inquiries = sum(1 for t in inquiry_tasks if t["task_type"].startswith("INQUIRY"))

    pending_approval_tasks = vault.list_task_files("Pending_Approval")
    pending_responses = sum(1 for t in pending_approval_tasks if t["task_type"].startswith("INQUIRY"))

    return {
        "products": {
            "total": total_products,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "completed": completed_orders,
            "revenue": float(revenue),
        },
        "inquiries": {
            "pending": pending_inquiries,
            "awaiting_response": pending_responses,
        },
    }
```

**Step 5: Register the new route in main.py**

Add to `backend/main.py` after line 17:

```python
from routes.ecommerce import router as ecommerce_router
```

Add after line 73 (after audit_router):

```python
app.include_router(ecommerce_router)
```

**Step 6: Run tests**

Run: `cd backend && python -m pytest tests/test_ecommerce_routes.py -v`
Expected: PASS (3 tests)

**Step 7: Commit**

```bash
git add backend/routes/triggers.py backend/routes/ecommerce.py backend/main.py backend/tests/test_ecommerce_routes.py
git commit -m "feat: add product/price-update triggers and ecommerce stats endpoint"
```

---

### Task 5: AI Processor MCP Integration

**Files:**
- Modify: `backend/services/ai_processor.py:39-98`
- Create: `backend/tests/test_ai_processor_mcp.py`

**Step 1: Write the failing test**

Create `backend/tests/test_ai_processor_mcp.py`:

```python
"""Tests for AI processor MCP tool integration."""
import pytest
from unittest.mock import patch, MagicMock
from services.ai_processor import _detect_task_type, _build_system_prompt


def test_detect_product_add_type():
    assert _detect_task_type("PRODUCT-ADD_2026-02-17_12-00-00.md") == "PRODUCT-ADD"


def test_detect_price_update_type():
    assert _detect_task_type("PRICE-UPDATE_2026-02-17_12-00-00.md") == "PRICE-UPDATE"


def test_skill_map_includes_product():
    """The system prompt builder recognizes PRODUCT-ADD tasks."""
    with patch("services.ai_processor.vault") as mock_vault:
        mock_vault.read_company_handbook.return_value = "handbook"
        mock_vault.read_agent_skill.return_value = "skill content"
        prompt = _build_system_prompt("PRODUCT-ADD")
        assert "handbook" in prompt
        assert "skill content" in prompt


def test_skill_map_includes_price_update():
    with patch("services.ai_processor.vault") as mock_vault:
        mock_vault.read_company_handbook.return_value = "handbook"
        mock_vault.read_agent_skill.return_value = "skill content"
        prompt = _build_system_prompt("PRICE-UPDATE")
        assert "handbook" in prompt
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_ai_processor_mcp.py -v`
Expected: FAIL — PRODUCT-ADD not recognized

**Step 3: Update ai_processor.py**

Add new task types to `_detect_task_type()` (after line 96):

```python
    elif filename.startswith("PRODUCT-ADD"):
        return "PRODUCT-ADD"
    elif filename.startswith("PRICE-UPDATE"):
        return "PRICE-UPDATE"
```

Add new entries to `skill_map` in `_build_system_prompt()` (after line 63):

```python
        "PRODUCT-ADD": "update_product_listing.md",
        "PRICE-UPDATE": "update_product_listing.md",
```

Add new processor routing in `process_task()` (after line 172):

```python
        elif task_type == "PRODUCT-ADD":
            result = process_product_task(filename, db)
        elif task_type == "PRICE-UPDATE":
            result = process_price_update_task(filename, db)
```

Add the new processor functions at the end of `ai_processor.py`:

```python
# ── Product Add Processor ──────────────────────────────────────────────────

def process_product_task(filename: str, db: Session) -> dict:
    """Process a PRODUCT-ADD task: validate details and draft listing plan."""
    content = vault.read_task_file("Needs_Action", filename)
    metadata = vault.parse_task_metadata(content)

    system_prompt = _build_system_prompt("PRODUCT-ADD")
    user_prompt = f"""Review this product addition request. Generate:
1. Validation check (name, description, pricing against handbook rules)
2. SEO-friendly product listing draft
3. Category verification
4. Any concerns or flags

Here is the task file:

{content}
"""

    ai_response = _call_claude(system_prompt, user_prompt)

    updated_content = content + f"""

---

## AI Processing Output

**Processed:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
**Model:** {config.CLAUDE_MODEL}

{ai_response}

## Queued Actions

| # | Server | Tool | Args | Status |
|---|--------|------|------|--------|
| 1 | catalog | create_product | {{"name": "{metadata.get('Product Name', '')}", "description": "{metadata.get('Description', '')}", "price": {metadata.get('Price', '0').replace('₹', '').replace(',', '')}, "category_id": {metadata.get('Category ID', '1')}, "stock": {metadata.get('Stock', '50')}}} | PENDING |

## Status: PROCESSED
"""

    vault.write_task_file("Needs_Action", filename, updated_content)
    vault.move_task_file(filename, "Needs_Action", "Pending_Approval")

    audit.write_audit_entry(
        source="ai-processor/product",
        action="task.processed",
        entity_type="product",
        entity_id=filename,
        details={"product_name": metadata.get("Product Name", "")},
        queue="Pending_Approval",
        status="PROCESSED",
    )
    audit.append_daily_log(
        source="ai-processor/product",
        action="Task Processed",
        details=f"{filename} — Product: {metadata.get('Product Name', 'Unknown')}",
        status="PROCESSED",
    )

    return {
        "status": "processed",
        "task_type": "PRODUCT-ADD",
        "filename": filename,
        "moved_to": "Pending_Approval",
    }


# ── Price Update Processor ─────────────────────────────────────────────────

def process_price_update_task(filename: str, db: Session) -> dict:
    """Process a PRICE-UPDATE task: validate against margin rules."""
    content = vault.read_task_file("Needs_Action", filename)
    metadata = vault.parse_task_metadata(content)

    product_id = metadata.get("Product ID", "")
    product = None
    if product_id.isdigit():
        product = db.query(Product).filter(Product.id == int(product_id)).first()

    system_prompt = _build_system_prompt("PRICE-UPDATE")
    user_prompt = f"""Review this pricing change request. Validate:
1. New price vs handbook margin rules (minimum 30% margin)
2. Comparison with current pricing tier
3. Impact assessment
4. Any flags or concerns

Here is the task file:

{content}
"""
    if product:
        user_prompt += f"\nCurrent DB price: ₹{product.price:,.0f}, Stock: {product.stock}"

    ai_response = _call_claude(system_prompt, user_prompt)

    new_price = metadata.get("New Price", "0").replace("₹", "").replace(",", "").strip()

    updated_content = content + f"""

---

## AI Processing Output

**Processed:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
**Model:** {config.CLAUDE_MODEL}

{ai_response}

## Queued Actions

| # | Server | Tool | Args | Status |
|---|--------|------|------|--------|
| 1 | catalog | update_price | {{"id": {product_id}, "new_price": {new_price}, "reason": "{metadata.get('Reason', '')}"}} | PENDING |

## Status: PROCESSED
"""

    vault.write_task_file("Needs_Action", filename, updated_content)
    vault.move_task_file(filename, "Needs_Action", "Pending_Approval")

    audit.write_audit_entry(
        source="ai-processor/price-update",
        action="task.processed",
        entity_type="product",
        entity_id=filename,
        details={
            "product_id": product_id,
            "product_name": metadata.get("Product Name", ""),
            "new_price": new_price,
        },
        queue="Pending_Approval",
        status="PROCESSED",
    )
    audit.append_daily_log(
        source="ai-processor/price-update",
        action="Task Processed",
        details=f"{filename} — {metadata.get('Product Name', 'Unknown')}: ₹{metadata.get('Current Price', '?')} → ₹{metadata.get('New Price', '?')}",
        status="PROCESSED",
    )

    return {
        "status": "processed",
        "task_type": "PRICE-UPDATE",
        "filename": filename,
        "moved_to": "Pending_Approval",
    }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_ai_processor_mcp.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add backend/services/ai_processor.py backend/tests/test_ai_processor_mcp.py
git commit -m "feat: add PRODUCT-ADD and PRICE-UPDATE processing to AI processor"
```

---

### Task 6: Task Executor MCP Integration

**Files:**
- Modify: `backend/services/task_executor.py:19-64`
- Create: `backend/tests/test_executor_mcp.py`

**Step 1: Write the failing test**

Create `backend/tests/test_executor_mcp.py`:

```python
"""Tests for task executor MCP action parsing and execution."""
import pytest
from services.task_executor import _detect_type, parse_queued_actions


def test_detect_product_add_type():
    assert _detect_type("PRODUCT-ADD_2026-02-17.md") == "PRODUCT"


def test_detect_price_update_type():
    assert _detect_type("PRICE-UPDATE_2026-02-17.md") == "PRICE"


def test_parse_queued_actions_from_content():
    content = """# Task

## Queued Actions

| # | Server | Tool | Args | Status |
|---|--------|------|------|--------|
| 1 | catalog | create_product | {"name": "Choker", "price": 2499} | PENDING |
| 2 | email | send_email | {"to": "test@test.com", "subject": "Hi", "body": "Hello"} | PENDING |
"""
    actions = parse_queued_actions(content)
    assert len(actions) == 2
    assert actions[0]["server"] == "catalog"
    assert actions[0]["tool"] == "create_product"
    assert actions[0]["args"]["name"] == "Choker"
    assert actions[1]["server"] == "email"


def test_parse_queued_actions_empty():
    content = "# Task\n\nNo actions here."
    actions = parse_queued_actions(content)
    assert actions == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_executor_mcp.py -v`
Expected: FAIL — parse_queued_actions not found

**Step 3: Update task_executor.py**

Add the `parse_queued_actions` function and update `_run_action` to use MCP servers.

Add after imports (line 6):

```python
import json
```

Add after `EXECUTOR_MAP` (line 27):

```python
def parse_queued_actions(content: str) -> list[dict]:
    """Parse the Queued Actions table from a task file."""
    actions = []
    in_table = False
    for line in content.split("\n"):
        if "## Queued Actions" in line:
            in_table = True
            continue
        if in_table and line.startswith("|") and not line.startswith("| #") and not line.startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5 and parts[0].isdigit():
                try:
                    args = json.loads(parts[3])
                except (json.JSONDecodeError, IndexError):
                    args = {}
                actions.append({
                    "server": parts[1],
                    "tool": parts[2],
                    "args": args,
                    "status": parts[4],
                })
        elif in_table and line.startswith("##") and "Queued Actions" not in line:
            break
    return actions
```

Update `_run_action` to check for queued MCP actions:

```python
def _run_action(task_type: str, content: str, filename: str) -> dict:
    """Execute the action for a task — uses MCP servers if queued actions exist."""
    now = datetime.now(timezone.utc).isoformat()
    logger.info(f"[EXECUTOR] Running action for {task_type}: {filename}")

    # Check for MCP queued actions
    actions = parse_queued_actions(content)
    if actions:
        from database import SessionLocal
        db = SessionLocal()
        try:
            import mcp as mcp_registry
            results = []
            for action in actions:
                server = mcp_registry.get_server(action["server"], db)
                if hasattr(server, "execute_action"):
                    result = server.execute_action(action)
                else:
                    result = server.call_tool(action["tool"], action["args"])
                results.append({"tool": action["tool"], "result": result})
                logger.info(f"[EXECUTOR] MCP {action['server']}.{action['tool']} → {result.get('status', 'ok')}")
            return {
                "steps_completed": len(results),
                "executed_at": now,
                "action": "mcp_execution",
                "results": results,
            }
        finally:
            db.close()

    return {
        "steps_completed": 1,
        "executed_at": now,
        "action": f"{task_type.lower()}_action",
        "details": f"Executed {task_type} action for {filename}",
    }
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_executor_mcp.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add backend/services/task_executor.py backend/tests/test_executor_mcp.py
git commit -m "feat: add MCP queued action parsing and execution to task executor"
```

---

### Task 7: Frontend — API Functions and E-Commerce Tab

**Files:**
- Modify: `frontend/src/lib/ai-api.ts:1-160`
- Modify: `frontend/src/app/ai-employee/page.tsx`

**Step 1: Add new API functions to ai-api.ts**

Add at the end of `frontend/src/lib/ai-api.ts`:

```typescript
// ── E-Commerce ──

export async function triggerProduct(data: {
  name: string;
  description: string;
  price: number;
  category_id: number;
  stock?: number;
  featured?: boolean;
}): Promise<unknown> {
  return fetchAI("/trigger/product", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function triggerPriceUpdate(data: {
  product_id: number;
  new_price: number;
  reason: string;
}): Promise<unknown> {
  return fetchAI("/trigger/price-update", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getEcommerceStats(): Promise<{
  products: { total: number; low_stock: number; out_of_stock: number };
  orders: { total: number; pending: number; completed: number; revenue: number };
  inquiries: { pending: number; awaiting_response: number };
}> {
  return fetchAI("/api/ecommerce/stats");
}
```

**Step 2: Update page.tsx — add E-Commerce tab**

This is a frontend-only change. Add "E-Commerce" as a 5th tab in the existing tab navigation in `frontend/src/app/ai-employee/page.tsx`. The tab should display:

1. **Product Stats widget** — calls `getEcommerceStats()`, shows total products, low stock count, out of stock
2. **Order Monitor widget** — shows today's order count, revenue, pending/completed
3. **Pending Responses widget** — shows inquiry count awaiting reply
4. **Trigger buttons** — "+ Add Product", "+ Update Price", "+ Customer Reply" that open simple forms and call the trigger APIs
5. **Task type badges** — color-coded badges in the existing Task Queue tab for ORDER (blue), INQUIRY (green), PRODUCT-ADD (purple), PRICE-UPDATE (orange), INVENTORY-ALERT (red)

The specific implementation follows the existing pattern in page.tsx (useState for tab state, fetchAI for data, Tailwind for styling).

**Step 3: Commit**

```bash
git add frontend/src/lib/ai-api.ts frontend/src/app/ai-employee/page.tsx
git commit -m "feat: add E-Commerce tab with trigger buttons and stats dashboard"
```

---

### Task 8: Integration Tests

**Files:**
- Create: `backend/tests/test_mcp_integration.py`

**Step 1: Write integration tests**

```python
"""Integration tests — MCP servers + AI processor + executor pipeline."""
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from mcp import get_all_tools, call_tool, reset as reset_mcp
from mcp.catalog_server import CatalogServer
from services.task_executor import parse_queued_actions


@pytest.fixture(autouse=True)
def clean_mcp():
    reset_mcp()
    yield
    reset_mcp()


def test_get_all_tools_returns_17():
    """All 3 MCP servers return their tools (7 + 7 + 3 = 17)."""
    db = MagicMock()
    tools = get_all_tools(db)
    assert len(tools) == 17
    servers = set(t["server"] for t in tools)
    assert servers == {"catalog", "knowledge", "email"}


def test_catalog_read_then_write_flow():
    """Catalog read tool returns data, write tool returns action plan."""
    db = MagicMock()
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Test"
    mock_product.slug = "test"
    mock_product.price = 999.0
    mock_product.stock = 50
    mock_product.featured = False
    mock_product.description = "Test product"
    mock_product.image_url = "/img/test.jpg"
    mock_product.images_list = []
    mock_product.category = MagicMock()
    mock_product.category.name = "Rings"
    mock_product.category.id = 4

    db.query.return_value.filter.return_value.first.return_value = mock_product

    # Read: immediate result
    result = call_tool("catalog", "get_product", {"id": 1}, db)
    assert result["name"] == "Test"

    # Write: action plan (not executed)
    result = call_tool("catalog", "update_price", {"id": 1, "new_price": 1299.0, "reason": "test"}, db)
    assert result["requires_approval"] is True
    assert result["old_price"] == 999.0


def test_queued_actions_roundtrip():
    """Parse queued actions from content and verify structure."""
    content = """## Queued Actions

| # | Server | Tool | Args | Status |
|---|--------|------|------|--------|
| 1 | catalog | create_product | {"name": "Choker", "price": 2499, "description": "Beautiful", "category_id": 1} | PENDING |
"""
    actions = parse_queued_actions(content)
    assert len(actions) == 1
    assert actions[0]["server"] == "catalog"
    assert actions[0]["args"]["name"] == "Choker"
```

**Step 2: Run integration tests**

Run: `cd backend && python -m pytest tests/test_mcp_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/test_mcp_integration.py
git commit -m "test: add MCP integration tests"
```

---

### Task 9: Full Test Suite Verification

**Step 1: Run all tests**

Run: `cd backend && python -m pytest tests/ -v --tb=short`
Expected: ALL PASS (no regressions)

**Step 2: Final commit**

```bash
git add -A
git commit -m "chore: finalize e-commerce MCP integration"
```

---

## Summary

| Task | What | Files | Tests |
|------|------|-------|-------|
| 1 | MCP Registry + Catalog Server (7 tools) | `mcp/__init__.py`, `mcp/catalog_server.py` | 7 |
| 2 | Knowledge Server (7 read-only tools) | `mcp/knowledge_server.py` | 7 |
| 3 | Email Server (3 tools) | `mcp/email_server.py` | 5 |
| 4 | Trigger endpoints + ecommerce stats | `routes/triggers.py`, `routes/ecommerce.py`, `main.py` | 3 |
| 5 | AI Processor: PRODUCT-ADD + PRICE-UPDATE | `services/ai_processor.py` | 4 |
| 6 | Task Executor: MCP queued actions | `services/task_executor.py` | 4 |
| 7 | Frontend: API functions + E-Commerce tab | `ai-api.ts`, `page.tsx` | — |
| 8 | Integration tests | `tests/test_mcp_integration.py` | 3 |
| 9 | Full suite verification | — | All |
