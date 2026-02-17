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


def test_get_order_not_found(server, db):
    db.query.return_value.filter.return_value.first.return_value = None
    result = server.call_tool("get_order", {"order_id": 999})
    assert "error" in result
    assert "999" in result["error"]


def test_get_order_stats(server, db):
    db.query.return_value.filter.return_value.count.return_value = 5
    db.query.return_value.filter.return_value.scalar.return_value = 12500.0
    result = server.call_tool("get_order_stats", {})
    assert "total_orders" in result
    assert "total_revenue" in result


def test_list_orders(server, db):
    mock_order = MagicMock()
    mock_order.id = 1
    mock_order.customer_name = "Priya"
    mock_order.email = "priya@gmail.com"
    mock_order.total = 3499.0
    mock_order.status = "pending"
    mock_order.created_at = MagicMock()
    mock_order.created_at.isoformat.return_value = "2026-02-17T00:00:00"

    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_order]
    db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_order]
    result = server.call_tool("list_orders", {"status": "pending"})
    assert isinstance(result, list)


def test_search_faq(server):
    with patch("mcp.knowledge_server.vault") as mock_vault:
        mock_vault.read_company_handbook.return_value = "## 6. Refund Policy\n\n7-day return window.\n\n## 7. Pricing\n\nEntry tier."
        result = server.call_tool("search_faq", {"query": "refund"})
        assert len(result) > 0
        assert "refund" in result[0]["section"].lower()


def test_get_customer_history(server):
    with patch("mcp.knowledge_server.vault") as mock_vault:
        mock_vault.read_memory_file.return_value = "# Client: Priya\n\n| Date | Type |\n| 2026-02-17 | ORDER |"
        result = server.call_tool("get_customer_history", {"slug": "priya-sharma"})
        assert "Priya" in result["content"]


def test_get_customer_history_from_email(server):
    with patch("mcp.knowledge_server.vault") as mock_vault:
        mock_vault.read_memory_file.return_value = "# Client: Priya"
        result = server.call_tool("get_customer_history", {"email": "priya.sharma@gmail.com"})
        assert result["slug"] == "priya-sharma"
        mock_vault.read_memory_file.assert_called_once_with("Clients", "priya-sharma.md")


def test_get_customer_history_not_found(server):
    with patch("mcp.knowledge_server.vault") as mock_vault:
        mock_vault.read_memory_file.side_effect = FileNotFoundError("Not found")
        result = server.call_tool("get_customer_history", {"slug": "unknown"})
        assert result["content"] is None
        assert "No profile found" in result["note"]


def test_get_customer_history_no_args(server):
    result = server.call_tool("get_customer_history", {})
    assert "error" in result


def test_search_policies(server):
    with patch("mcp.knowledge_server.vault") as mock_vault:
        mock_vault.read_company_handbook.return_value = "## 5. Order Processing\n\nShipping in 3-5 days.\n\n## 6. Refund Policy\n\n7-day window."
        result = server.call_tool("search_policies", {"topic": "shipping"})
        assert len(result) > 0


def test_get_product_info(server, db):
    mock_product = MagicMock()
    mock_product.name = "Rose Necklace"
    mock_product.price = 1299.0
    mock_product.stock = 50
    mock_product.description = "A beautiful necklace"
    mock_product.category = MagicMock()
    mock_product.category.name = "Necklaces"

    db.query.return_value.filter.return_value.first.return_value = mock_product
    result = server.call_tool("get_product_info", {"slug": "rose-necklace"})
    assert result["name"] == "Rose Necklace"
    assert result["in_stock"] is True


def test_get_product_info_not_found(server, db):
    db.query.return_value.filter.return_value.first.return_value = None
    result = server.call_tool("get_product_info", {"slug": "nonexistent"})
    assert "error" in result


def test_call_tool_unknown_raises(server):
    with pytest.raises(ValueError, match="Unknown tool"):
        server.call_tool("nonexistent", {})
