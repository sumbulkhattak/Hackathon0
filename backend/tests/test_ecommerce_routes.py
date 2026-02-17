"""Tests for e-commerce trigger and stats endpoints."""
import pytest


def test_product_trigger_schema():
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
    from routes.triggers import PriceUpdateTriggerRequest
    req = PriceUpdateTriggerRequest(
        product_id=1,
        new_price=1499.0,
        reason="Premium materials",
    )
    assert req.product_id == 1
    assert req.new_price == 1499.0


def test_ecommerce_stats_endpoint_exists():
    from routes.ecommerce import router
    paths = [r.path for r in router.routes]
    assert any("/stats" in p for p in paths)
