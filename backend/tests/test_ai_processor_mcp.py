"""Tests for AI processor MCP tool integration."""
import pytest
from unittest.mock import patch, MagicMock
from services.ai_processor import _detect_task_type, _build_system_prompt


def test_detect_product_add_type():
    assert _detect_task_type("PRODUCT-ADD_2026-02-17_12-00-00.md") == "PRODUCT-ADD"


def test_detect_price_update_type():
    assert _detect_task_type("PRICE-UPDATE_2026-02-17_12-00-00.md") == "PRICE-UPDATE"


def test_skill_map_includes_product():
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
