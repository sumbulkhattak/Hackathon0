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
