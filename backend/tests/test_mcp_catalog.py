"""Tests for MCP Catalog Server -- product & pricing tools."""
import pytest
from unittest.mock import MagicMock, patch
from mcp.catalog_server import CatalogServer


@pytest.fixture
def db():
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


def test_get_product_not_found(server, db):
    db.query.return_value.filter.return_value.first.return_value = None
    result = server.call_tool("get_product", {"id": 999})
    assert result == {"error": "Product not found"}


def test_get_product_by_slug(server, db):
    mock_product = MagicMock()
    mock_product.id = 2
    mock_product.name = "Gold Ring"
    mock_product.slug = "gold-ring"
    mock_product.price = 2499.0
    mock_product.stock = 30
    mock_product.featured = True
    mock_product.description = "A gold ring"
    mock_product.image_url = "/img/gold-ring.jpg"
    mock_product.images_list = []
    mock_product.category = MagicMock()
    mock_product.category.name = "Rings"
    mock_product.category.id = 2

    db.query.return_value.filter.return_value.first.return_value = mock_product
    result = server.call_tool("get_product", {"slug": "gold-ring"})
    assert result["name"] == "Gold Ring"
    assert result["slug"] == "gold-ring"


def test_list_products_low_stock(server, db):
    mock_p = MagicMock()
    mock_p.id = 1
    mock_p.name = "Low Stock Item"
    mock_p.slug = "low-stock"
    mock_p.price = 499.0
    mock_p.stock = 3
    mock_p.featured = False
    mock_p.description = "Low stock"
    mock_p.image_url = "/img/low.jpg"
    mock_p.images_list = []
    mock_p.category = MagicMock()
    mock_p.category.name = "Earrings"
    mock_p.category.id = 3

    db.query.return_value.filter.return_value.all.return_value = [mock_p]
    result = server.call_tool("list_products", {"low_stock": True})
    assert len(result) == 1
    assert result[0]["stock"] == 3


def test_create_product_returns_plan(server, db):
    result = server.call_tool(
        "create_product",
        {
            "name": "New Choker",
            "description": "A stunning choker",
            "price": 2499.0,
            "category_id": 1,
            "stock": 25,
            "featured": False,
        },
    )
    assert result["action"] == "create_product"
    assert result["args"]["name"] == "New Choker"
    assert result["requires_approval"] is True


def test_update_price_returns_plan(server, db):
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Rose Necklace"
    mock_product.price = 1299.0

    db.query.return_value.filter.return_value.first.return_value = mock_product
    result = server.call_tool(
        "update_price",
        {"id": 1, "new_price": 1499.0, "reason": "Premium materials"},
    )
    assert result["action"] == "update_price"
    assert result["old_price"] == 1299.0
    assert result["new_price"] == 1499.0
    assert result["requires_approval"] is True


def test_set_stock_returns_plan(server, db):
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.stock = 50

    db.query.return_value.filter.return_value.first.return_value = mock_product
    result = server.call_tool(
        "set_stock",
        {"id": 1, "quantity": 100, "reason": "Restock"},
    )
    assert result["action"] == "set_stock"
    assert result["old_stock"] == 50
    assert result["new_stock"] == 100
    assert result["requires_approval"] is True


def test_update_product_returns_plan(server, db):
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Rose Necklace"
    mock_product.slug = "rose-necklace"
    mock_product.price = 1299.0
    mock_product.stock = 50
    mock_product.featured = False
    mock_product.description = "A beautiful necklace"
    mock_product.image_url = "/img/rose.jpg"
    mock_product.images_list = []
    mock_product.category = MagicMock()
    mock_product.category.name = "Necklaces"
    mock_product.category.id = 1

    db.query.return_value.filter.return_value.first.return_value = mock_product
    result = server.call_tool(
        "update_product",
        {"id": 1, "name": "Updated Rose Necklace"},
    )
    assert result["action"] == "update_product"
    assert result["requires_approval"] is True
    assert result["current"]["name"] == "Rose Necklace"


def test_delete_product_returns_plan(server, db):
    mock_product = MagicMock()
    mock_product.id = 1
    mock_product.name = "Rose Necklace"

    db.query.return_value.filter.return_value.first.return_value = mock_product
    result = server.call_tool(
        "delete_product",
        {"id": 1},
    )
    assert result["action"] == "delete_product"
    assert result["product_name"] == "Rose Necklace"
    assert result["requires_approval"] is True


def test_call_tool_unknown_raises(server):
    with pytest.raises(ValueError, match="Unknown tool"):
        server.call_tool("nonexistent_tool", {})
