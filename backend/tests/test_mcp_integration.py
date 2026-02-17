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
